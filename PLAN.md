# Voice AI DSA Tutor — MVP Plan

## Context

The goal is a voice-driven AI tutor that walks a user through solving one DSA problem at a time the way a patient human tutor would: explain the problem, probe comprehension (surfacing edge cases/"loopholes" most people miss), grade the user's spoken approach (brute force first, then guide toward optimal via a hint ladder — never skipping ahead), let the user type real code while asking "why" about their decisions, then actually execute that code against test cases and give spoken feedback, looping until the problem is genuinely solved well.

This is a from-scratch build in an empty directory — no existing code to integrate with. Decisions locked in with the user before this plan:
- **Scope**: web app, single-user, local MVP, no auth/accounts — nail the core tutoring loop for one problem first.
- **Code execution**: must be real sandboxed execution (not just LLM reasoning about code), via **Piston** (`https://emkc.org/api/v2/piston/execute`), a free public API requiring no key.
- **Problems**: a small in-house curated problem bank (our own wording, not scraped LeetCode text) — a few classic DSA problems, each with statement, constraints, test cases (incl. deliberate edge cases), reference solution, brute-force description + why it's insufficient, an ordered hint ladder, and known loopholes.
- **Budget**: effectively $0, so **Groq** is the unified provider for LLM (Llama 3.3 70B, free tier), STT (Whisper large-v3, free tier), and TTS (PlayAI TTS, free tier) — one API key, one provider, near-zero cost. Browser `SpeechSynthesis`/`SpeechRecognition` is the zero-cost fallback if Groq TTS/STT proves insufficient.
- **LLM abstraction**: thin interface so the provider could be swapped later (e.g. to Claude) without a redesign — not over-engineered.

## Tech Stack

**Next.js 14+ (App Router) + TypeScript**, single deployable app — frontend and backend (API routes) in one process, ideal for a solo zero-budget MVP. No database: session state is single-user and ephemeral, held in an in-memory server-side store. Tailwind for styling. `@monaco-editor/react` (client-only, dynamically imported) for the code editor. Plain `fetch` request/response per turn — not WebSockets/SSE; the interaction is inherently turn-based (record → transcribe → grade → speak), so streaming is a later optimization, not a day-1 requirement.

## Core State Machine

A deterministic FSM drives the session; the LLM is invoked *inside* states as a grader/narrator returning structured JSON, and a pure transition function `(state, validatedGraderOutput) => newState` decides what happens next — the LLM never picks its own next phase.

**Phases**: `INTRO → COMPREHENSION_CHECK ⇄ COMPREHENSION_REMEDIATION → APPROACH_DISCUSSION (brute force) → BRUTE_FORCE_ANALYSIS → HINT_LADDER → CODING → SUBMITTED/EXECUTING → FEEDBACK → ITERATION (loop to CODING or HINT_LADDER) → COMPLETE`

**Session shape** (conceptual): `sessionId, problemId, phase, history[]`, plus per-phase tracking objects — `comprehension{score, gaps, edgeCasesPresented, passed}`, `approach{bruteForceGradeScore, optimalApproachFound, hintsRevealed, stuckSignalStreak}`, `coding{currentCode, probingQuestionsAsked, lastActivityTimestamp}`, `execution{submissions, lastResult}`.

**Structured grader contracts** (Zod-validated): `ComprehensionGrade{score, dimensions, gaps, readyToAdvance, feedbackToUser}`, `ApproachGrade{identifiedApproach, complexityCorrect, matchesExpected, readyToAdvance, userSeemsStuck, feedbackToUser}`, `StuckSignal{userSeemsStuck, confidence, reasoning}`. Groq is called with `response_format: json_object`; on schema-validation failure, one repair retry, then a safe deterministic fallback (e.g. `readyToAdvance:false`) — the FSM must never crash or hang on a bad LLM response.

**Anti-rushing guardrail**: the hint ladder only advances a level after `userSeemsStuck` is true for **2+ consecutive turns** *and* at least one probing question has already been asked at that level. A manual "give me a hint" button is a user-controlled override regardless of auto stuck-detection, since stuck-detection is inherently fuzzy.

## Problem Bank

`/problems/<slug>/problem.ts`, each conforming to a shared Zod schema in `/problems/schema.ts` (type-checked at author time). Shape: `id, slug, title, difficulty, statement (markdown, original wording), constraints[], starterCode{[lang]}, testCases[{id, input, expectedOutput, isEdgeCase, edgeCaseTag, explanationIfFailed}], referenceSolution{[lang]}, bruteForce{description, complexity, whyInsufficient}, optimalApproach{description, complexity}, hintLadder[{level, text}], commonLoopholes[{id, description, relatedTestCaseId}], comprehensionRubric{keyPoints[]}, executionHarnessTemplate{[lang]}`. **One language only for MVP** (Python or JS) to minimize harness-authoring work; expand later.

## Groq Integration

All Groq calls are **server-side only** (API key never reaches the client):
- `POST /api/session/start` — creates session, returns intro narration.
- `POST /api/session/[id]/turn` — main turn endpoint: takes transcribed user text + phase, runs the phase's grader prompt via Groq JSON-mode, applies the transition function, returns `{newPhase, narratorText, ...}`.
- `POST /api/audio/transcribe` — browser `MediaRecorder` blob → Groq `whisper-large-v3` → transcript text.
- `POST /api/audio/speak` — narrator text → Groq PlayAI TTS → audio bytes.
- `POST /api/execute` — code submission → Piston (below).

Abstraction: `/lib/llm/provider.ts` (interface `LlmProvider.generateStructured<T>(prompt, schema)`), `/lib/llm/groq.ts` (implementation), `/lib/audio/stt.ts` + `/lib/audio/tts.ts` (thin Groq wrappers, not over-abstracted). Browser Web Speech API is a separate client-side fallback UI mode, not a drop-in behind the same server interface.

## Piston Integration

**One Piston call per submission**, not per test case (Piston is a shared free instance with unpublished rate limits — minimize calls). The user's function is embedded into a per-language harness template (from the problem bank) that also embeds all test cases and prints a JSON array of per-case results to stdout. `/lib/execution/harness.ts` renders the final source (structural substitution, not naive string concat); `/lib/execution/piston.ts` POSTs `{language, version, files, run_timeout:~5000ms}` to Piston and parses `run.stdout`/`stderr`. Compile/runtime failures map to a friendly "your code didn't run: <reason>" result. On success, compute pass/fail, prioritize surfacing the first failing **edge case** with its `explanationIfFailed` — this deterministic result feeds both the FSM transition and the LLM's spoken narration (LLM explains *why*, never decides pass/fail).

## Build Sequencing (voice deliberately last — highest-risk, most novel integration)

1. **M0 — Scaffolding**: Next.js+TS+Tailwind init, repo layout, `.env.local` (`GROQ_API_KEY`, gitignored).
2. **M1 — Problem bank**: author 2 problems (e.g. two-sum, sliding-window-max) against the schema; page to list/select/render statement. Zero AI involved — validates the data shape.
3. **M2 — FSM skeleton, stubbed grading**: session store + phases + transition function driven by hardcoded canned grader responses, exercised via a plain text chat UI. Proves the state machine end-to-end before any external dependency.
4. **M3 — Real Groq LLM grading**: swap stubs for real Groq JSON-mode calls + Zod validation + retry/fallback for comprehension and approach discussion; still text-input via textbox.
5. **M4 — Monaco + Piston**: code editor in CODING phase, `/api/execute`, harness rendering, results parsed into FSM.
6. **M5 — Iteration + hint gating polish**: stuck-streak gating, "make it better" loop after first pass, full manual text-only playthrough of one problem start to finish.
7. **M6 — Voice layer**: Groq Whisper STT (mic capture/upload/transcribe) + Groq TTS (narration playback) wired into the already-proven text pipeline from M3.
8. **M7 — Hardening**: coding-pause probing questions, Groq/Piston failure/loading states, 1-2 more problems, light styling.

## Key Files/Folders

```
/app/page.tsx
/app/tutor/[problemId]/page.tsx
/app/api/session/start/route.ts
/app/api/session/[id]/turn/route.ts
/app/api/audio/transcribe/route.ts
/app/api/audio/speak/route.ts
/app/api/execute/route.ts

/lib/fsm/types.ts
/lib/fsm/transitions.ts
/lib/fsm/sessionStore.ts
/lib/llm/provider.ts
/lib/llm/groq.ts
/lib/llm/schemas.ts
/lib/llm/prompts/{comprehension,approach,probe,feedback}.ts
/lib/audio/stt.ts
/lib/audio/tts.ts
/lib/execution/piston.ts
/lib/execution/harness.ts

/problems/schema.ts
/problems/index.ts
/problems/two-sum/problem.ts
/problems/sliding-window-max/problem.ts

/components/{ProblemStatement,ChatPanel,CodeEditor,VoiceControls,TestResultsPanel}.tsx

.env.local, package.json, tsconfig.json, tailwind.config.ts, next.config.js
```

## Risks / Open Questions

- Groq PlayAI TTS free-tier availability/quality is unverified — check Groq's current model page before M6; browser `SpeechSynthesis` is the fallback.
- Per-turn voice latency (STT → LLM → TTS, three sequential hops) could reach 3-6s+; plan a visible "thinking..." state, consider shortening narrator text later.
- Groq free-tier rate limits — JSON-repair retries double some calls; monitor once building.
- Piston has no documented SLA/rate limit; design for graceful "execution unavailable, try again"; self-hosting via Docker is a later escape hatch, not needed for MVP.
- Never `eval` LLM output; Zod validation + fallback defaults handle malformed grading JSON.
- Confirm Groq Whisper accepts the browser `MediaRecorder` default container (webm/opus) directly, or whether transcoding is needed, when M6 is implemented.
- Exactly one language for MVP to minimize harness-authoring burden.

## LLM Brain — Anti-Hallucination & Prompt Architecture

**Core principle: the LLM is never the source of DSA truth.** Every fact the tutor asserts — the optimal approach, why brute force fails, each hint, each edge case, each pass/fail result — lives in the authored problem bank or comes from Piston's actual execution output. The LLM's only two jobs per turn are: (1) **judge** the user's input against that authored ground truth, and (2) **narrate** the judgment in a warm, patient tutor voice. It is never asked to "know" DSA from its training data — this is what eliminates most hallucination risk, because classic problems (two-sum, etc.) are exactly the kind of thing a model has memorized variants of, and its memorized "well-known" answer may not match our specific authored wording/constraints.

**Per-phase prompt "nodes"** — each FSM phase that calls the LLM has a defined node with fixed inputs/outputs:

| Node | Grounding context injected | Output schema | Content source for what's said |
|---|---|---|---|
| Comprehension grader | `comprehensionRubric.keyPoints`, `constraints`, user's spoken explanation | `ComprehensionGrade` | LLM judges coverage against keyPoints only |
| Edge-case remediation | one `commonLoopholes` entry + its `relatedTestCaseId` | narration only | Loophole text is authored verbatim; LLM rephrases delivery, doesn't invent the edge case |
| Approach grader (brute force) | `bruteForce.description`, `bruteForce.whyInsufficient`, user's spoken approach | `ApproachGrade` | "why insufficient" explanation is authored, not generated |
| Approach grader (optimal) | `optimalApproach.description`, `optimalApproach.complexity`, user's spoken approach | `ApproachGrade` | — |
| Hint delivery | current `hintLadder[level].text`, `stuckSignalStreak` | `StuckSignal` + narration | Hint text is pulled **verbatim** from the ladder — LLM decides *when* to reveal it and phrases the delivery, never invents new hint content |
| Coding-pause probe | current code diff (actual lines, not paraphrase) | narration question only | Question must reference real code the user wrote |
| Execution feedback | Piston's actual parsed result (`pass/fail`, real input/output values, matched `edgeCaseTag` + `explanationIfFailed`) | narration only | LLM explains the *why* behind a real result; never allowed to state a pass/fail it wasn't given |

**Concrete anti-hallucination mechanisms:**
1. **Explicit "don't use memorized knowledge" instruction** in every grading system prompt: *"Grade solely using the rubric/context provided below. Do not rely on your own memorized knowledge of this or similar problems — the rubric may differ from what you recall."*
2. **Combined single call per turn** (not separate grade+narrate calls) to keep latency/rate-limit cost down — but structure the JSON schema with a `reasoning` field placed *before* the scoring/verdict fields, so the model effectively does chain-of-thought inside the object before committing to a score (field order matters in JSON-mode generation).
3. **Authored content is quoted, not regenerated**: hints, loophole descriptions, and the "why brute force fails" explanation are always injected as literal text the LLM is told to *deliver/rephrase*, never asked to *produce from scratch*. This is the single biggest lever against DSA-fact hallucination.
4. **Piston output is the only source of pass/fail truth**; the feedback prompt receives the actual parsed result object and is instructed never to state a test outcome not present in that object.
5. **Bounded context per call**: instead of the full raw transcript, each prompt gets a compact rolling `sessionFacts` summary (current phase, comprehension gaps found, hints already revealed, last code version) — keeps grounding tight and prevents drift/contradiction over a long session, and keeps token usage (and Groq free-tier consumption) low.
6. **Low-ish temperature (~0.2–0.3)** for all grading/judging calls — this is a classification-and-narration task, not creative writing; reserve higher temperature only if a separate "warmth pass" is ever split out later.
7. **Schema validation is the hard backstop** (already in the FSM design): Zod-validate every response; one repair retry; deterministic fallback (`readyToAdvance:false`, ask user to clarify) on repeated failure. This catches structural hallucination (wrong shape) even if content hallucination (wrong judgment) slips through.
8. **Log every grading call's (prompt, response) pair** during M3–M5 to a local file/console — this is how prompts actually get tuned; expect the hint-gating and approach-grading prompts to need iteration once real user phrasing is observed.

**Trade-off flagged, not yet decided**: combining grading + narration in one call (point 2) is the recommended default for latency/cost, but if grading quality suffers from blending "strict judge" and "warm tutor voice" in one prompt, the escape hatch is splitting into two sequential calls (a pure-JSON grader with temperature ~0.2, then a narrator call that only rephrases the already-decided verdict). Worth revisiting during M3 once real grading output is observed — not a decision to pre-solve before seeing it fail.

## Verification

- **M1**: run dev server, navigate to problem list/detail pages, confirm statement/constraints/test cases render correctly from the schema-validated problem files.
- **M2**: play through the full FSM via the text chat UI with canned responses, confirming every phase transition fires correctly with no Groq/Piston calls yet.
- **M3**: same playthrough with real Groq calls; manually try a few "understood well" and "confused" style answers to confirm grading and remediation/hint paths both trigger appropriately.
- **M4**: submit correct, incorrect, and edge-case-failing code for a seeded problem; confirm Piston results map to the right pass/fail + edge-case narration.
- **M5**: full manual start-to-finish text-only playthrough of one problem, confirming hint-ladder pacing (no premature advancement) and the "make it better" iteration loop.
- **M6**: full voice playthrough — record an answer, confirm transcription accuracy on DSA vocabulary, confirm TTS playback quality/latency are acceptable.
