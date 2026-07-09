# Volna — build status

Last updated: 2026-07-10. See `PLAN.md` for the original architecture/design spec, `README.md` for how to actually run everything, and the [manual test sheet](https://claude.ai/code/artifact/76d9b1c2-bc38-4b88-ba33-c78239b27fa9) for a live checklist.

## Done and verified

| Piece | State | How it was verified |
|---|---|---|
| Problem bank (5 problems, ~418 test cases) | Done | All reference solutions pass 100% via real Piston execution |
| Sandboxed code execution (self-hosted Piston) | Done | Root-caused and fixed a real stdio-buffer-limit bug; verified live |
| Stateless FastAPI (`/problems`, `/problems/{slug}`, `/livekit/token`) | Done | Endpoints curl-tested directly: no answer/solution leakage, correct 404/422 error codes, CORS confirmed for `localhost:3000` |
| LangGraph tutoring brain (8 nodes + StateGraph wiring) | Done | Full live playthrough for two-sum: intro to comprehension gate to brute-force check to gated hint ladder to optimal-approach check to real execution to completion, all against real Groq + real Piston |
| Landing page (dark mode, copy rules, sunset stripe) | Done | Build/lint clean, em-dash and banned-word grep clean, dark theme colors confirmed in rendered CSS |
| Tutor app frontend shell (Monaco, problem list, panels) | Done | Build/lint clean, real browser smoke test |
| LiveKit voice agent worker | Done | Registered live against the real LiveKit Cloud project; graph integration confirmed via real Groq calls |
| Frontend to backend real-time wiring (transcript + code submission over data channel) | Done | Investigated and confirmed the actual `livekit-agents` text-stream mechanism against installed source (not assumed); build/lint clean |
| Two real integration bugs found by crosschecking frontend against backend | Fixed | `/livekit/token` was missing `url`/`room` in its response; room name convention mismatch between frontend and worker |
| Dark-mode visual consistency across `/problems` and `/tutor` routes | Done | Independently re-verified: diff read, build/lint re-run, rendered CSS checked for real (not purged) token classes |
| Failure-state hardening (Groq API failures, Piston network failures, unhandled exceptions in the voice worker) | Done | Independently re-verified: 10/10 new failure-injection tests pass, all 418 happy-path tests still pass |

## In progress right now (subagents, being independently reviewed before merge)

- Interactive/polish pass on the landing page's animated graph visualization (drag, better hover feedback, smoother edges, cursor-reactive background)
- Audit of LangGraph *logic* edge cases (hint ladder exhaustion, comprehension-gate infinite loop risk, concurrent code submissions, malformed state access) — already confirmed fixing the comprehension-gate infinite-loop risk with an honest, narrated escape hatch after repeated attempts

## Never yet tested

- **A real human voice round trip.** Everything up to the microphone is verified (worker registers, STT/TTS plugins construct correctly, the graph responds correctly to text input). Nobody has actually spoken to it yet.

## Known rough edges (not bugs, just things to know)

- `ITERATION` phase currently routes identically to `CODING` — there's no distinct "you seem fundamentally stuck again after a failed submission, let's revisit hints" path yet, per a documented simplification in `graph/build.py`.
- The frontend's dev-only "preview sample result" button is a deliberate fallback for when voice isn't connected, not leftover cruft.
- Backend `ProblemDetail` doesn't send a `language` field; the frontend defaults to `"python"`, which happens to be correct for all 5 current problems but is a latent gap if a non-Python problem is ever added.

## Realistic next steps, roughly in order

1. Merge and verify the four in-progress subagent tasks above.
2. Do the first real human voice test (see `README.md` for the 4-process startup).
3. Decide whether to expand the problem bank past 5, and whether `ITERATION` needs its own grading node.
4. Revisit the TTS/STT provider choice if voice quality or latency disappoints in real use (Deepgram TTS + Groq Whisper were the free-tier picks, not load-tested under a real conversation yet).
