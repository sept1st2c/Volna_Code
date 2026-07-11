from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from graph.nodes.approach import brute_force_node, optimal_approach_node
from graph.nodes.coding_pause import coding_pause_node
from graph.nodes.complexity import complexity_feedback_node, complexity_probe_node
from graph.nodes.comprehension import comprehension_node
from graph.nodes.execution_feedback import execution_feedback_node
from graph.nodes.executing import executing_node
from graph.nodes.hints import hint_node
from graph.nodes.intro import intro_node
from graph.nodes.loophole import loophole_node
from graph.state import TutorState

# Turn-based design note:
#
# This graph processes exactly one user turn (or one code submission) per
# invocation, then halts at END to wait for the next one -- it is not a
# continuously-running loop. `state["phase"]` doubles as both "what happened
# last" and "what kind of input we're now waiting for", which is what the
# entry router below dispatches on.
#
# A node "chains" (routes to another node instead of END) only when the tutor
# should keep speaking without new input from the student -- e.g. once brute
# force is confirmed understood, we don't wait for another turn before
# delivering the first hint; once code finishes executing, feedback is
# narrated in the same turn, not a separate one.
#
# ITERATION routing: execution_feedback_node tracks whether the student is
# failing the SAME test case across consecutive submissions (a deterministic
# "genuinely stuck" signal, no LLM opinion needed) and chains straight into
# hint_node -- within this same turn -- when that streak crosses its
# threshold, instead of silently sending them back to CODING with no fresh
# guidance. Otherwise it chains to CODING via coding_pause_node next turn.
#
# COMPLETE gate: passing every test case is necessary but not sufficient --
# complexity_probe_node empirically times/memory-profiles the submission at
# increasing input sizes and complexity_feedback_node only grants COMPLETE if
# the measured growth actually matches the problem's authored optimal
# complexity, regardless of which specific algorithm the student used.


def _entry_router(state: TutorState) -> str:
    phase = state.get("phase", "INTRO")
    return {
        "INTRO": "intro",
        "COMPREHENSION_CHECK": "comprehension",
        "APPROACH_DISCUSSION": "brute_force",
        "HINT_LADDER": "optimal_approach",
        "CODING": "coding_pause",
        "ITERATION": "coding_pause",
        "EXECUTING": "executing",
        # Defensive only: COMPLEXITY_CHECK is always chained same-turn from
        # execution_feedback_node and should never be a resting phase a fresh
        # invocation enters at, but route it sanely rather than KeyError if it
        # somehow is.
        "COMPLEXITY_CHECK": "complexity_probe",
        "COMPLETE": "complete",
    }[phase]


def _complete_node(state: TutorState) -> dict:
    return {"narration": "This one's solved. Pick another problem whenever you're ready."}


def _after_comprehension(state: TutorState) -> str:
    return "loophole" if state["phase"] == "COMPREHENSION_REMEDIATION" else END


def _after_brute_force(state: TutorState) -> str:
    return "hint" if state["phase"] == "HINT_LADDER" else END


def _after_optimal_approach(state: TutorState) -> str:
    # skip_hint_this_turn distinguishes "resting at HINT_LADDER, not ready to
    # advance" (chain into hint_node, matching the graph's normal guiding
    # behavior) from "resting at HINT_LADDER because this turn wasn't a real
    # attempt at all" (end the turn as-is; a hint here would bury the
    # acknowledgment optimal_approach_node just gave). See state.py.
    if state["phase"] == "HINT_LADDER" and not state.get("skip_hint_this_turn"):
        return "hint"
    return END


def _after_execution_feedback(state: TutorState) -> str:
    phase = state["phase"]
    if phase == "HINT_LADDER":
        return "hint"
    if phase == "COMPLEXITY_CHECK":
        return "complexity_probe"
    return END


def build_graph():
    g = StateGraph(TutorState)

    g.add_node("intro", intro_node)
    g.add_node("comprehension", comprehension_node)
    g.add_node("loophole", loophole_node)
    g.add_node("brute_force", brute_force_node)
    g.add_node("optimal_approach", optimal_approach_node)
    g.add_node("hint", hint_node)
    g.add_node("coding_pause", coding_pause_node)
    g.add_node("executing", executing_node)
    g.add_node("execution_feedback", execution_feedback_node)
    g.add_node("complexity_probe", complexity_probe_node)
    g.add_node("complexity_feedback", complexity_feedback_node)
    g.add_node("complete", _complete_node)

    g.add_conditional_edges(
        START,
        _entry_router,
        {
            "intro": "intro",
            "comprehension": "comprehension",
            "brute_force": "brute_force",
            "optimal_approach": "optimal_approach",
            "coding_pause": "coding_pause",
            "executing": "executing",
            "complexity_probe": "complexity_probe",
            "complete": "complete",
        },
    )

    g.add_edge("intro", END)
    g.add_conditional_edges("comprehension", _after_comprehension, {"loophole": "loophole", END: END})
    g.add_edge("loophole", END)
    g.add_conditional_edges("brute_force", _after_brute_force, {"hint": "hint", END: END})
    g.add_conditional_edges("optimal_approach", _after_optimal_approach, {"hint": "hint", END: END})
    g.add_edge("hint", END)
    g.add_edge("coding_pause", END)
    g.add_edge("executing", "execution_feedback")
    g.add_conditional_edges(
        "execution_feedback",
        _after_execution_feedback,
        {"hint": "hint", "complexity_probe": "complexity_probe", END: END},
    )
    g.add_edge("complexity_probe", "complexity_feedback")
    g.add_edge("complexity_feedback", END)
    g.add_edge("complete", END)

    return g.compile()


_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph
