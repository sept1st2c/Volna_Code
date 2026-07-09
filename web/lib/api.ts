import { DEFAULT_MOCK_SLUG, MOCK_PROBLEM_DETAILS, MOCK_PROBLEM_SUMMARIES } from "./mock-data";
import type { LiveKitTokenResponse, ProblemDetail, ProblemSummary } from "./types";

/**
 * Typed client for the FastAPI backend described in PLAN.md:
 *   GET  /problems           -> ProblemSummary[]
 *   GET  /problems/{slug}    -> ProblemDetail
 *   POST /livekit/token      -> LiveKitTokenResponse
 *
 * The backend may not be running yet (or ever, during frontend-only dev), so
 * `getProblems` / `getProblem` fall back to realistic mock data on any network
 * or non-2xx failure and log a clear console warning when they do. Callers get
 * an `usedMock` flag back so the UI can optionally surface that state.
 *
 * `createLiveKitToken` intentionally does NOT fall back to mock data: faking a
 * successful token would make VoiceControls lie about being connected to a real
 * voice backend. Callers must handle the rejection themselves.
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

export interface GetProblemsResult {
  problems: ProblemSummary[];
  usedMock: boolean;
}

export interface GetProblemResult {
  problem: ProblemDetail;
  usedMock: boolean;
}

export async function getProblems(): Promise<GetProblemsResult> {
  try {
    const res = await fetch(`${API_BASE_URL}/problems`, { cache: "no-store" });
    if (!res.ok) {
      throw new Error(`GET /problems responded with ${res.status}`);
    }
    const problems = (await res.json()) as ProblemSummary[];
    return { problems, usedMock: false };
  } catch (err) {
    console.warn(
      "[api] GET /problems unreachable (is the FastAPI backend running at " +
        `${API_BASE_URL}?). Falling back to mock problem list.`,
      err,
    );
    return { problems: MOCK_PROBLEM_SUMMARIES, usedMock: true };
  }
}

export async function getProblem(slug: string): Promise<GetProblemResult> {
  try {
    const res = await fetch(`${API_BASE_URL}/problems/${encodeURIComponent(slug)}`, {
      cache: "no-store",
    });
    if (!res.ok) {
      throw new Error(`GET /problems/${slug} responded with ${res.status}`);
    }
    const problem = (await res.json()) as ProblemDetail;
    return { problem, usedMock: false };
  } catch (err) {
    console.warn(
      `[api] GET /problems/${slug} unreachable (is the FastAPI backend running at ` +
        `${API_BASE_URL}?). Falling back to mock problem data.`,
      err,
    );
    const mock = MOCK_PROBLEM_DETAILS[slug] ?? MOCK_PROBLEM_DETAILS[DEFAULT_MOCK_SLUG];
    return { problem: mock, usedMock: true };
  }
}

export interface CreateLiveKitTokenParams {
  room: string;
  identity: string;
}

/**
 * Requests a real LiveKit room-join token from the backend. No mock fallback:
 * if this fails, the caller (VoiceControls) should show an honest "not
 * connected to voice backend" state rather than a fake success.
 */
export async function createLiveKitToken(
  params: CreateLiveKitTokenParams,
): Promise<LiveKitTokenResponse> {
  const res = await fetch(`${API_BASE_URL}/livekit/token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    throw new Error(`POST /livekit/token responded with ${res.status}`);
  }
  return (await res.json()) as LiveKitTokenResponse;
}
