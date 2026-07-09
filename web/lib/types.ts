/**
 * Shared types for the tutor frontend <-> FastAPI backend contract.
 *
 * These mirror the Pydantic models described in PLAN.md ("Problem Bank" section).
 * The backend is the source of truth; keep this file in sync if the contract changes.
 */

export type Difficulty = "easy" | "medium" | "hard" | string;

/** Shape returned by `GET /problems` (list item). */
export interface ProblemSummary {
  slug: string;
  title: string;
  difficulty: Difficulty;
}

/** One rung of the vague -> specific hint ladder, delivered verbatim by the tutor. */
export interface HintLadderEntry {
  level: number;
  text: string;
}

/** One authored test case, as surfaced to the frontend (no reference solution). */
export interface TestCasePreview {
  id: string;
  description: string;
  is_edge_case: boolean;
  edge_case_tag?: string;
}

export interface ApproachSummary {
  description: string;
  complexity: string;
}

/** Shape returned by `GET /problems/{slug}` (full detail). */
export interface ProblemDetail extends ProblemSummary {
  statement: string;
  constraints: string[];
  starter_code: string;
  language: string;
  hint_ladder: HintLadderEntry[];
  test_cases?: TestCasePreview[];
  brute_force?: ApproachSummary;
  optimal_approach?: ApproachSummary;
}

/** Shape returned by `POST /livekit/token`. */
export interface LiveKitTokenResponse {
  token: string;
  url: string;
  room: string;
}

/** Chat transcript entry rendered in the ChatPanel. */
export interface ChatMessage {
  id: string;
  role: "tutor" | "user";
  text: string;
  timestamp?: string;
}

/** Per-test-case row rendered in the TestResultsPanel. */
export type TestCaseStatus = "pass" | "fail";

export interface TestCaseResult {
  id: string;
  label: string;
  status: TestCaseStatus;
  isEdgeCase?: boolean;
  message?: string;
}

/** Full submission result, published back over the data channel in the real system. */
export interface SubmissionResult {
  submittedAt: string;
  allPassed: boolean;
  cases: TestCaseResult[];
}
