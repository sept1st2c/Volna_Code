"""Dev-only regression test replaying the actual bad transcript a user hit in
real testing (mic-check treated as an explanation attempt -> random unrelated
edge case; comprehension feedback silently discarded when chaining into
loophole delivery; brute-force node repeating the same ask verbatim after the
student said "give me a minute" or "I already know it, let's skip ahead").

Makes REAL Groq calls. Run with: .venv/Scripts/python.exe dev/test_conversation_quality.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")

import asyncio

import agent.worker as worker_mod
from graph.build import _after_optimal_approach
from graph.nodes.approach import brute_force_node, optimal_approach_node
from graph.nodes.comprehension import comprehension_node
from graph.nodes.loophole import loophole_node
from graph.state import initial_state

_failures = []


def _check(name: str, condition: bool, detail: str = "") -> None:
    status = "OK" if condition else "FAIL"
    print(f"[{name}] {status}{'  ' + detail if detail and not condition else ''}")
    if not condition:
        _failures.append(name)


def test_mic_check_does_not_trigger_random_loophole() -> None:
    state = initial_state("two-sum")
    state["user_explanation"] = "Hello, hello, am I audible? Am I audible?"
    result = comprehension_node(state)
    print(f"    narration: {result['narration']!r}")
    _check(
        "mic-check stays at COMPREHENSION_CHECK (not sent into remediation)",
        result["phase"] == "COMPREHENSION_CHECK",
        f"phase={result['phase']!r}",
    )
    # It DOES count toward the exhaustion budget (every turn does now,
    # substantive or not -- see the comment in comprehension.py: gating this
    # on is_substantive_attempt let real LLM classification variance
    # silently break the "bounded number of turns" guarantee). What must NOT
    # happen is grading it as a failed explanation or routing it into
    # loophole remediation, which the phase check above already covers.
    _check(
        "mic-check still counts toward the turn budget (bounded-progress guarantee)",
        result.get("comprehension_attempts") == 1,
        f"comprehension_attempts={result.get('comprehension_attempts')!r}",
    )


def test_loophole_delivery_acknowledges_comprehension_feedback() -> None:
    state = initial_state("two-sum")
    state["user_explanation"] = (
        "Let's just say there are two elements I need to find in an array that add up to the target value."
    )
    comp = comprehension_node(state)
    state.update(comp)
    print(f"    comprehension feedback: {comp['narration']!r}")

    if comp["phase"] != "COMPREHENSION_REMEDIATION":
        print("    (this attempt was graded ready_to_advance -- re-running with a weaker explanation)")
        state = initial_state("two-sum")
        state["user_explanation"] = "two numbers that add up to something"
        comp = comprehension_node(state)
        state.update(comp)

    loop = loophole_node(state)
    print(f"    loophole narration: {loop['narration']!r}")

    # The old bug: this narration ONLY ever contained the new edge case, with
    # zero connection to what the student's explanation actually covered --
    # i.e. comp["narration"] was silently discarded. Check word-overlap with
    # the comprehension feedback as a proxy for "did it actually acknowledge
    # what was just said" rather than launch straight into a cold new topic.
    comp_words = set(comp["narration"].lower().split())
    loop_words = set(loop["narration"].lower().split())
    overlap = comp_words & loop_words
    meaningful_overlap = {w for w in overlap if len(w) > 3}
    _check(
        "loophole narration shares real content with the comprehension feedback (not a cold, unrelated reply)",
        len(meaningful_overlap) >= 2,
        f"shared words={meaningful_overlap}",
    )


def test_brute_force_does_not_repeat_verbatim_after_stall() -> None:
    state = initial_state("two-sum")
    state["phase"] = "APPROACH_DISCUSSION"

    state["approach_transcript"] = "Give me time to think."
    first = brute_force_node(state)
    print(f"    turn 1 (\"give me time\"): {first['narration']!r}")
    # It DOES count toward the exhaustion budget (every turn does, substantive
    # or not -- see the comment in approach.py for why: gating this on
    # is_substantive_attempt let real LLM classification variance silently
    # break the "bounded number of turns" guarantee the cap exists to give).
    # What must NOT happen is grading it as a failed description or nagging.
    _check(
        "a request for time still counts toward the turn budget (bounded-progress guarantee)",
        first.get("brute_force_attempts") == 1,
        f"brute_force_attempts={first.get('brute_force_attempts')!r}",
    )
    _check("phase stays APPROACH_DISCUSSION", first["phase"] == "APPROACH_DISCUSSION")
    state.update(first)

    state["approach_transcript"] = "Just give me two minutes, let me think."
    second = brute_force_node(state)
    print(f"    turn 2 (\"two minutes\"): {second['narration']!r}")

    # The real bug: after being asked for a moment, the tutor re-issued the
    # FULL "describe every pair / brute-force approach" pressure ask anyway,
    # ignoring the request. It's fine (even good) for a short "take your
    # time" acknowledgment to repeat verbatim across two such turns -- what
    # must NOT reappear is the original demanding task instruction.
    pressure_phrases = ("checking every", "describe", "process would", "walk me through")
    _check(
        "does not re-issue the full brute-force pressure ask after 'give me a minute'",
        not any(p in second["narration"].lower() for p in pressure_phrases),
        f"second={second['narration']!r}",
    )


def test_explicit_readiness_after_real_description_advances() -> None:
    state = initial_state("two-sum")
    state["phase"] = "APPROACH_DISCUSSION"
    state["approach_transcript"] = (
        "The brute force way is to check every pair of numbers in the array with two nested loops "
        "and see if any pair sums to the target. That's O(n squared) time."
    )
    first = brute_force_node(state)
    print(f"    real description: phase={first['phase']!r} narration={first['narration']!r}")
    state.update(first)

    if first["phase"] != "HINT_LADDER":
        state["approach_transcript"] = "Yeah I already explained the brute force, I know it works, can we move on?"
        second = brute_force_node(state)
        print(f"    explicit readiness follow-up: phase={second['phase']!r} narration={second['narration']!r}")
        # Flagged by an independent review agent: the previous version of this
        # assertion OR'd in `is_substantive_attempt`, which is true for nearly
        # any real sentence -- it could pass even if explicit-readiness
        # handling were completely broken. The actual behavior under test is
        # whether the phase advances.
        _check(
            "explicit 'I already explained it, move on' after a correct description advances to HINT_LADDER",
            second["phase"] == "HINT_LADDER",
            f"phase={second['phase']!r} narration={second['narration']!r}",
        )
    else:
        _check("correct brute-force description advances immediately", True)


def test_optimal_approach_non_attempt_does_not_get_overwritten_by_a_hint() -> None:
    """Regression for a bug an independent review agent caught in this same
    changeset: optimal_approach_node's non-substantive branch returned
    phase="HINT_LADDER" (its normal resting phase), which build.py's
    _after_optimal_approach used to read as "chain into hint_node" -- so a
    student's "give me a minute" got silently overwritten by an unsolicited
    hint (last-write-wins on the plain-dict `narration` key), the exact same
    class of bug ("computed feedback silently discarded") this changeset was
    otherwise fixing elsewhere. Fixed via the skip_hint_this_turn flag."""
    state = initial_state("two-sum")
    state["phase"] = "HINT_LADDER"
    state["approach_transcript"] = "Wait, give me a second to think about this."

    result = optimal_approach_node(state)
    print(f"    optimal_approach non-attempt narration: {result['narration']!r}")
    _check(
        "non-attempt sets skip_hint_this_turn so build.py won't chain into hint_node",
        result.get("skip_hint_this_turn") is True,
    )
    state.update(result)
    routed_to = _after_optimal_approach(state)
    _check(
        "_after_optimal_approach ends the turn instead of chaining to hint_node",
        routed_to != "hint",
        f"routed_to={routed_to!r}",
    )
    _check(
        "narration is the acknowledgment, not a hint (doesn't contain the hint lead-in)",
        "here's something to think about" not in result["narration"].lower(),
        f"narration={result['narration']!r}",
    )


async def test_fragmented_speech_accumulates_instead_of_overwriting() -> None:
    """Regression for the bug behind a real user's "the tutor is brain dead"
    report: LiveKit's turn-detection often segments one continuous spoken
    explanation into several separate turns (natural mid-thought pauses).
    `_process_turn` used to overwrite `state["approach_transcript"]` with
    only the LATEST fragment each time, so a grading call could only ever
    see the last piece of an otherwise complete, correct explanation -- the
    real transcript showed a student's correct nested-loop brute-force
    description getting rejected turn after turn purely because it arrived
    in three separate spoken turns instead of one."""
    agent = worker_mod.TutorAgent("two-sum")
    agent.state["phase"] = "APPROACH_DISCUSSION"

    fragments = [
        "So we'd use a for loop to iterate through the array.",
        "And another for loop to iterate again through the array for an element we picked before it.",
        "And if the two elements add up to the target, that's our answer, otherwise we keep iterating. That's O of n squared.",
    ]
    for fragment in fragments:
        await agent._process_turn(fragment)
        # phase reset back to APPROACH_DISCUSSION by the fixtures below if
        # the (real, non-deterministic) grader happened to advance early --
        # this test is about accumulation, not about triggering advancement.
        if agent.state.get("phase") != "APPROACH_DISCUSSION":
            agent.state["phase"] = "APPROACH_DISCUSSION"

    accumulated = agent.state.get("approach_transcript", "")
    print(f"    accumulated approach_transcript: {accumulated!r}")
    _check(
        "all three fragments are present in the accumulated transcript (not just the last one)",
        all(fragment.split(".")[0] in accumulated for fragment in fragments),
        f"accumulated={accumulated!r}",
    )


async def test_accumulation_resets_on_genuine_phase_change() -> None:
    """The flip side of the accumulation fix: once the resting phase
    actually changes to a different question, the buffer must NOT keep
    growing forever -- otherwise brute-force discussion text would bleed
    into optimal-approach grading."""
    agent = worker_mod.TutorAgent("two-sum")
    agent.state["phase"] = "APPROACH_DISCUSSION"
    await agent._process_turn("Two nested loops checking every pair, O of n squared.")

    # Simulate having genuinely advanced to a new question (HINT_LADDER,
    # which reuses the same approach_transcript field name by convention --
    # exactly the case that must NOT accumulate across the topic change).
    agent.state["phase"] = "HINT_LADDER"
    await agent._process_turn("I think a hash map would let us look values up faster.")

    transcript = agent.state.get("approach_transcript", "")
    print(f"    transcript after phase change: {transcript!r}")
    _check(
        "old brute-force text does not bleed into the new optimal-approach turn",
        "nested loops" not in transcript.lower(),
        f"transcript={transcript!r}",
    )
    _check(
        "the new turn's own text is present",
        "hash map" in transcript.lower(),
        f"transcript={transcript!r}",
    )


async def test_comprehension_remediation_resets_accumulation() -> None:
    """Regression for a real bug caught by an independent review agent: since
    loophole_node always routes back to phase COMPREHENSION_CHECK after
    delivering a new edge case, phase-equality alone can't tell "one
    utterance split by pauses" apart from "a fresh restatement responding to
    brand-new feedback" -- both rest at the same phase string. Without
    fresh_guidance_just_delivered forcing a reset, a rejected first attempt
    would stay permanently glued onto every subsequent (possibly much
    better) restatement."""
    agent = worker_mod.TutorAgent("two-sum")
    agent.state["phase"] = "COMPREHENSION_CHECK"

    # Deliberately weak/wrong first attempt -- likely to be graded not-ready
    # and sent through loophole_node in the same turn.
    await agent._process_turn("umm something about an array I think")
    print(f"    after attempt 1: phase={agent.state.get('phase')!r} guidance_flag={agent.state.get('fresh_guidance_just_delivered')!r}")

    if agent.state.get("phase") != "COMPREHENSION_CHECK" or not agent.state.get("fresh_guidance_just_delivered"):
        print("    (attempt 1 didn't route through remediation this run -- real LLM grading is non-deterministic; skipping)")
        return

    await agent._process_turn("You're given an array and need to find two indices that add up to a target.")
    transcript = agent.state.get("user_explanation", "")
    print(f"    user_explanation after attempt 2: {transcript!r}")
    _check(
        "the rejected first attempt does not linger in the next restatement",
        "umm something" not in transcript.lower(),
        f"transcript={transcript!r}",
    )
    _check(
        "the second attempt's own words are present",
        "two indices" in transcript.lower(),
        f"transcript={transcript!r}",
    )


async def test_hint_ladder_gets_latest_turn_not_accumulated_buffer() -> None:
    """Regression for the more serious bug the same review caught: hint_node
    explicitly documents (and prompts.hints.py states outright) that it
    judges stuck/not-stuck from "the latest turn alone" -- but once
    HINT_LADDER accumulation was added for optimal_approach_node's benefit,
    hint_node started silently receiving the whole multi-turn buffer instead
    (they share the approach_transcript field/phase). Fixed by giving
    hint_node its own always-latest-only field."""
    agent = worker_mod.TutorAgent("two-sum")
    agent.state["phase"] = "HINT_LADDER"

    await agent._process_turn("I'm not sure what to do here.")
    await agent._process_turn("Wait, maybe a hash map to store what I've seen?")

    latest = agent.state.get("latest_spoken_turn", "")
    accumulated = agent.state.get("approach_transcript", "")
    print(f"    latest_spoken_turn={latest!r}")
    print(f"    approach_transcript={accumulated!r}")
    _check(
        "latest_spoken_turn holds only the most recent turn, not both",
        "not sure" not in latest.lower() and "hash map" in latest.lower(),
        f"latest_spoken_turn={latest!r}",
    )


if __name__ == "__main__":
    test_mic_check_does_not_trigger_random_loophole()
    test_loophole_delivery_acknowledges_comprehension_feedback()
    test_brute_force_does_not_repeat_verbatim_after_stall()
    test_explicit_readiness_after_real_description_advances()
    test_optimal_approach_non_attempt_does_not_get_overwritten_by_a_hint()
    asyncio.run(test_fragmented_speech_accumulates_instead_of_overwriting())
    asyncio.run(test_accumulation_resets_on_genuine_phase_change())
    asyncio.run(test_comprehension_remediation_resets_accumulation())
    asyncio.run(test_hint_ladder_gets_latest_turn_not_accumulated_buffer())

    print()
    if _failures:
        print(f"FAILED: {_failures}")
        sys.exit(1)
    print("ALL CONVERSATION-QUALITY TESTS PASSED")
