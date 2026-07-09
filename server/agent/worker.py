"""LiveKit Agents voice worker wiring real voice I/O to the existing,
already-verified LangGraph tutoring state machine (see `graph/build.py`).

This module owns NO tutoring logic of its own -- every word the tutor speaks
comes from `graph.nodes.*`'s `narration` output. `TutorAgent.llm_node` below
is overridden so the framework's normal "call a chat LLM" step is replaced
entirely by "advance our graph by one turn and speak whatever it authored".

------------------------------------------------------------------------
Room-naming convention (frontend integration MUST match this)
------------------------------------------------------------------------
`server/api/main.py`'s `POST /livekit/token` does not currently encode a
problem slug anywhere (its `TokenRequest` is just `room`/`identity`/`name`),
so this worker picks a convention rather than inventing new API surface:

1. Preferred: room metadata is a JSON object `{"problem_slug": "<slug>"}`.
   LiveKit room metadata is readable here via `ctx.room.metadata` with no
   string-parsing of the room name, and can be set at room-creation time
   (e.g. via `RoomService.create_room(metadata=...)` or
   `update_room_metadata`) once the frontend/API layer is ready to do so.
2. Fallback (what actually works TODAY given the existing token endpoint):
   the room NAME itself is treated as the problem slug directly -- e.g. a
   client requesting a token for room "two-sum" gets tutored on the
   "two-sum" problem. No JSON encoding required on the frontend's part.
3. If neither resolves to a known problem slug, default to "two-sum" and
   log a warning rather than crashing the session.

------------------------------------------------------------------------
Data-channel message contract (frontend integration MUST match this)
------------------------------------------------------------------------
Sent over `room.local_participant.publish_data(...)` / received via
`room.on("data_received", ...)`, reliable delivery, default (empty) topic.

Frontend -> worker, on code submission:
    {"type": "code_submit", "code": "<student's current full source>"}

Worker -> frontend, after running the submitted code through the graph's
EXECUTING -> execution_feedback chain (fired in direct response to the
message above, not on a timer):
    {
        "type": "execution_result",
        "submittedAt": "<ISO-8601 UTC timestamp>",
        "allPassed": <bool>,
        "cases": [
            {
                "id": "<test case id>",
                "label": "<edge_case_tag if authored, else id>",
                "status": "pass" | "fail",
                "isEdgeCase": <bool>,
                "message": "<string | null>"
            },
            ...
        ]
    }
    This shape is a deliberate 1:1 match for `SubmissionResult` in
    `web/lib/types.ts` (same camelCase field names) so `TestResultsPanel`
    (`web/components/TestResultsPanel.tsx`) can render it directly with no
    transformation on the frontend.

Any other/malformed `type` on an incoming data message is ignored (logged
at debug level) rather than raising.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

# Secrets live in the repo root .env (gitignored), matching api/main.py's
# convention. /server/agent/worker.py -> parents[2] is the repo root.
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")

from livekit import rtc
from livekit.agents import Agent, AgentSession, JobContext, ModelSettings, WorkerOptions, cli, llm
from livekit.plugins import deepgram, groq, silero

from graph.build import get_graph
from graph.state import TutorState, initial_state
from problems import get_problem
from problems.schema import Problem

logger = logging.getLogger("agent.worker")

_DEFAULT_PROBLEM_SLUG = "two-sum"

_AGENT_INSTRUCTIONS = (
    "You are a voice DSA tutor. You never generate your own responses -- "
    "all narration comes from an external LangGraph state machine via "
    "TutorAgent.llm_node. This instructions string exists only because the "
    "Agent base class requires one; it is never read at runtime."
)

_ALREADY_SOLVED_NARRATION = (
    "This one's already solved -- pick another problem whenever you're ready."
)
_EXECUTING_BUSY_NARRATION = "Still running your code -- one moment."

# Belt-and-suspenders fallback for when `get_graph().ainvoke(...)` raises
# despite every node's own Groq/Piston hardening (graph/llm.py's
# generate_structured and execution/piston.py's run_python both now convert
# real API/network failures into safe in-band fallback results rather than
# exceptions) -- e.g. a genuinely unexpected bug. Never invents a DSA fact
# or claims success; just asks the student to repeat themselves, matching
# the "fail toward safe/honest" philosophy of every node's own _FALLBACK.
_UNEXPECTED_ERROR_NARRATION = (
    "Sorry, something went wrong on my end. Could you say that again?"
)

# Phases where a spoken turn writes into TutorState before the graph is
# invoked. Keys are the phases `graph/build.py`'s `_entry_router` treats as
# valid entry points that a spoken turn can rest at between invocations
# (INTRO, CODING, ITERATION, EXECUTING, COMPLETE are the remaining valid
# entry phases but have no spoken-turn field to populate, or are handled as
# special cases above).
_SPOKEN_TURN_FIELD_BY_PHASE = {
    "COMPREHENSION_CHECK": "user_explanation",
    "APPROACH_DISCUSSION": "approach_transcript",
    "HINT_LADDER": "approach_transcript",
}


def _latest_user_text(chat_ctx: llm.ChatContext) -> str:
    """Extracts the most recent user-role message's text from the chat
    context handed to `llm_node`. Returns "" if there is no user turn yet
    (e.g. the very first, INTRO-triggering call)."""
    user_messages = [m for m in chat_ctx.messages() if m.role == "user"]
    if not user_messages:
        return ""
    return user_messages[-1].text_content or ""


def _build_submission_result(problem: Problem, execution_result: list[dict], all_tests_passed: bool) -> dict:
    """Builds the `execution_result` data-channel payload, matching
    `SubmissionResult` in web/lib/types.ts field-for-field."""
    test_cases_by_id = {tc.id: tc for tc in problem.test_cases}

    cases = []
    for r in execution_result:
        case_id = r.get("id", "unknown")
        tc = test_cases_by_id.get(case_id)
        passed = bool(r.get("passed"))

        message = None
        if not passed:
            if "error" in r:
                message = r["error"]
            elif "actual" in r and "expected" in r:
                message = f"expected {r['expected']!r}, got {r['actual']!r}"

        cases.append(
            {
                "id": case_id,
                "label": (tc.edge_case_tag if tc and tc.edge_case_tag else case_id),
                "status": "pass" if passed else "fail",
                "isEdgeCase": bool(tc.is_edge_case) if tc else False,
                "message": message,
            }
        )

    return {
        "type": "execution_result",
        "submittedAt": datetime.now(timezone.utc).isoformat(),
        "allPassed": all_tests_passed,
        "cases": cases,
    }


def _build_error_submission_result(message: str) -> dict:
    """Same `execution_result` shape as `_build_submission_result`, used as
    the belt-and-suspenders payload when the graph invocation itself raises
    unexpectedly (see `TutorAgent.handle_code_submission` and
    `_wire_data_channel`'s `_run`). Always `allPassed: False` -- never claim
    success that wasn't actually verified by the sandbox."""
    return {
        "type": "execution_result",
        "submittedAt": datetime.now(timezone.utc).isoformat(),
        "allPassed": False,
        "cases": [
            {
                "id": "_worker_error",
                "label": "_worker_error",
                "status": "fail",
                "isEdgeCase": False,
                "message": message,
            }
        ],
    }


class TutorAgent(Agent):
    """One instance per room/session. Owns the running `TutorState` and is
    the sole place graph turns are invoked from."""

    def __init__(self, problem_slug: str) -> None:
        super().__init__(instructions=_AGENT_INSTRUCTIONS)
        self.state: TutorState = initial_state(problem_slug)
        # Concurrency guard for `handle_code_submission`: `_wire_data_channel`
        # spawns a fresh `asyncio.create_task` per incoming `code_submit`
        # message with no queueing, so a student double-clicking submit (or
        # a frontend disabled-while-submitting race) can fire two overlapping
        # calls. Without this flag, both would synchronously stomp
        # `self.state["last_code"]`/`self.state["phase"]` before either
        # `await`s the graph, so the first submission's own harness run could
        # end up executing the SECOND submission's code. A plain bool (not an
        # asyncio.Lock) is enough because asyncio is single-threaded and the
        # check-then-set below has no `await` in between, so it can't race.
        self._code_submission_in_flight = False

    async def _process_turn(self, user_text: str) -> str:
        """Core, directly-testable "run one graph turn given raw spoken
        text" helper -- factored out of `llm_node` so it can be exercised
        without a real `chat_ctx`/`ModelSettings`/AgentSession.

        Writes `user_text` into whichever TutorState field the current
        phase expects (if any), invokes the graph exactly once, merges the
        partial-update dict it returns into `self.state`, and returns the
        narration to speak.
        """
        phase = self.state.get("phase", "INTRO")

        if phase == "COMPLETE":
            return _ALREADY_SOLVED_NARRATION

        if phase == "EXECUTING":
            # Only reachable if a spoken turn races a code submission that's
            # already mid-flight over the data channel (see
            # `_handle_data_received`). Never re-invoke the graph
            # re-entrantly here -- just stall politely and wait for the
            # in-flight submission to finish.
            return _EXECUTING_BUSY_NARRATION

        field = _SPOKEN_TURN_FIELD_BY_PHASE.get(phase)
        if field is not None:
            self.state[field] = user_text
        elif phase in ("CODING", "ITERATION"):
            # coding_pause_node probes from `state["last_code"]`, not from
            # spoken text -- there's no TutorState field a spoken turn maps
            # onto here, so it's dropped and the graph runs on state as-is
            # (still routes to coding_pause_node per `_entry_router`).
            pass
        elif phase != "INTRO":
            # INTRO's narration ignores all input (see graph/nodes/intro.py)
            # so nothing to do. Any other value would mean `self.state`
            # rested at a phase `_entry_router` doesn't recognize as a valid
            # entry point -- shouldn't happen, but degrade instead of
            # crashing the session.
            logger.warning(
                "TutorAgent._process_turn: unexpected resting phase %r; "
                "invoking graph as-is",
                phase,
            )

        try:
            result = await get_graph().ainvoke(self.state)
        except Exception:
            # Belt-and-suspenders: every node's own Groq/Piston failure
            # paths already fall back in-band (see graph/llm.py,
            # execution/piston.py) so this should be unreachable in
            # practice, but if some genuinely unexpected bug still raises
            # here, the voice session must not die and the student must
            # not be met with silence. `self.state` is deliberately left
            # untouched -- resting phase doesn't change, so the next turn
            # just retries the same step instead of silently skipping it.
            logger.exception(
                "TutorAgent._process_turn: graph invocation raised unexpectedly "
                "at phase %r; keeping session alive with a safe narration",
                phase,
            )
            return _UNEXPECTED_ERROR_NARRATION

        self.state.update(result)
        return self.state.get("narration", "")

    async def llm_node(
        self,
        chat_ctx: llm.ChatContext,
        tools: list[llm.Tool],
        model_settings: ModelSettings,
    ) -> str:
        """Overrides the framework's default "call a chat LLM" step. Our
        LangGraph is the entire brain; this never calls a real chat LLM."""
        user_text = _latest_user_text(chat_ctx)
        return await self._process_turn(user_text)

    async def handle_code_submission(self, code: str) -> dict:
        """Runs a code submission through EXECUTING -> execution_feedback,
        speaks the resulting narration, and returns the data-channel payload
        the caller should publish back. Used by the data-channel handler.

        Rejects (rather than queues or interleaves) a submission that arrives
        while a previous one is still in flight -- see the
        `_code_submission_in_flight` guard set up in `__init__`. Queuing
        would risk silently running stale code after a newer submission was
        already intended; rejecting is honest about what actually happened.
        """
        if self._code_submission_in_flight:
            logger.warning(
                "TutorAgent.handle_code_submission: rejecting overlapping "
                "code_submit while a previous submission is still running"
            )
            return _build_error_submission_result(
                "Still running your previous submission -- please wait for it to finish before submitting again."
            )

        self._code_submission_in_flight = True
        try:
            previous_phase = self.state.get("phase", "CODING")
            self.state["last_code"] = code
            self.state["phase"] = "EXECUTING"

            try:
                result = await get_graph().ainvoke(self.state)
            except Exception:
                # Same belt-and-suspenders reasoning as `_process_turn`. Critically,
                # revert `phase` back off of "EXECUTING" -- if left there, every
                # subsequent spoken turn would stall forever on
                # `_EXECUTING_BUSY_NARRATION` (see the phase == "EXECUTING" branch
                # above) with no way for the student to ever get unstuck, which is
                # worse than the bug itself.
                logger.exception(
                    "TutorAgent.handle_code_submission: graph invocation raised "
                    "unexpectedly; reverting phase %r -> %r so the student isn't "
                    "stuck in a permanent 'still running' state",
                    "EXECUTING",
                    previous_phase,
                )
                self.state["phase"] = previous_phase
                self.state["narration"] = _UNEXPECTED_ERROR_NARRATION
                return _build_error_submission_result(
                    "Something went wrong while running your code. Please try submitting again."
                )

            self.state.update(result)

            problem = get_problem(self.state["problem_slug"])
            return _build_submission_result(
                problem,
                self.state.get("last_execution_result", []),
                self.state.get("all_tests_passed", False),
            )
        finally:
            self._code_submission_in_flight = False


def _resolve_problem_slug(room: rtc.Room) -> str:
    """Implements the room-naming convention documented at the top of this
    file: prefer `{"problem_slug": "..."}` in room metadata, fall back to
    treating the room name itself as the slug, then default."""
    slug: str | None = None

    if room.metadata:
        try:
            meta = json.loads(room.metadata)
            candidate = meta.get("problem_slug") if isinstance(meta, dict) else None
            if candidate and get_problem(candidate) is not None:
                slug = candidate
        except json.JSONDecodeError:
            pass

    if slug is None and get_problem(room.name) is not None:
        slug = room.name

    if slug is None:
        logger.warning(
            "could not resolve problem_slug from room metadata (%r) or room "
            "name (%r); defaulting to %r",
            room.metadata,
            room.name,
            _DEFAULT_PROBLEM_SLUG,
        )
        slug = _DEFAULT_PROBLEM_SLUG

    return slug


def _wire_data_channel(room: rtc.Room, agent: TutorAgent, session: AgentSession) -> None:
    """Registers the data-channel listener implementing the `code_submit` ->
    `execution_result` contract documented at the top of this file."""

    def _on_data_received(packet: rtc.DataPacket) -> None:
        try:
            message = json.loads(packet.data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            logger.debug("ignoring non-JSON data-channel message")
            return

        if not isinstance(message, dict) or message.get("type") != "code_submit":
            logger.debug("ignoring data-channel message with type=%r", message.get("type") if isinstance(message, dict) else None)
            return

        code = message.get("code", "")

        async def _run() -> None:
            # `handle_code_submission` already catches graph-invocation
            # failures internally and returns a safe payload -- this
            # try/except is for anything else in this coroutine (e.g.
            # `session.say`/`publish_data` themselves raising). Without it,
            # any exception here is swallowed silently by asyncio (logged
            # only as "Task exception was never retrieved", since nothing
            # ever awaits this task) and the student would see the submit
            # button spin forever with zero feedback -- no narration, no
            # execution_result message, nothing. That was a real bug: this
            # coroutine previously had no error handling at all.
            try:
                payload = await agent.handle_code_submission(code)
                session.say(agent.state.get("narration", ""))
                await room.local_participant.publish_data(json.dumps(payload), reliable=True)
            except Exception:
                logger.exception(
                    "data-channel code_submit handling raised unexpectedly; "
                    "notifying the student instead of leaving the submission "
                    "hanging with no response at all"
                )
                try:
                    session.say(_UNEXPECTED_ERROR_NARRATION)
                except Exception:
                    logger.exception("failed to speak the fallback error narration")
                try:
                    fallback_payload = _build_error_submission_result(
                        "Something went wrong while running your code. Please try submitting again."
                    )
                    await room.local_participant.publish_data(json.dumps(fallback_payload), reliable=True)
                except Exception:
                    logger.exception("failed to publish the fallback execution_result payload")

        asyncio.create_task(_run())

    room.on("data_received", _on_data_received)


async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()

    problem_slug = _resolve_problem_slug(ctx.room)
    tutor_agent = TutorAgent(problem_slug)

    session = AgentSession(
        vad=silero.VAD.load(),
        stt=groq.STT(model="whisper-large-v3"),
        tts=deepgram.TTS(),
        # `llm` is required by the framework's internal `self.llm is None`
        # gate in `AgentSession.generate_reply` even though `TutorAgent`
        # fully overrides `llm_node` -- the actual `.chat()` method on this
        # instance is never invoked. See `Agent.default.llm_node` vs our
        # override in `voice/agent.py` / `voice/agent_activity.py`.
        llm=groq.LLM(),
    )

    _wire_data_channel(ctx.room, tutor_agent, session)

    await session.start(tutor_agent, room=ctx.room)

    # Fire the INTRO turn immediately on join, without waiting for the
    # student to speak first -- `TutorAgent.llm_node` sees an empty user
    # turn, phase is still "INTRO" (see initial_state), so it presents the
    # problem statement and advances to COMPREHENSION_CHECK.
    session.generate_reply()


if __name__ == "__main__":
    # Must be launched as `python -m agent.worker dev` (or `connect`/`start`),
    # NOT `python agent/worker.py dev` -- the latter puts server/agent/ on
    # sys.path instead of server/, so the sibling `graph`/`problems` packages
    # fail to import. Confirmed live: `-m` invocation registers successfully
    # with the real LiveKit Cloud project.
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
