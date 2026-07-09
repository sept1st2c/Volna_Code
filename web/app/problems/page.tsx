"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getProblems } from "@/lib/api";
import { difficultyBadgeClasses } from "@/lib/ui";
import type { ProblemSummary } from "@/lib/types";

type LoadState =
  | { status: "loading" }
  | { status: "loaded"; problems: ProblemSummary[]; usedMock: boolean }
  | { status: "error"; message: string };

export default function ProblemsPage() {
  const [state, setState] = useState<LoadState>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;
    getProblems()
      .then(({ problems, usedMock }) => {
        if (!cancelled) setState({ status: "loaded", problems, usedMock });
      })
      .catch((err) => {
        // getProblems() already falls back to mock data internally, so this
        // only fires on an unexpected error (e.g. a bug), not a network failure.
        if (!cancelled) {
          setState({ status: "error", message: String(err) });
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="min-h-screen bg-canvas text-ink">
      <header className="border-b border-hairline bg-surface px-6 py-3">
        <div className="mx-auto max-w-3xl">
          <Link href="/" className="font-display text-base tracking-tight text-ink">
            Volna
          </Link>
        </div>
      </header>

      <div className="mx-auto w-full max-w-3xl px-6 py-12">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-ink">Pick a problem</h1>
        <p className="mt-1 text-sm text-steel">
          Choose a problem to start a tutoring session. You&apos;ll explain your approach out loud,
          write real code, and run it against real test cases.
        </p>
      </div>

      {state.status === "loading" && (
        <ul className="space-y-3" aria-label="Loading problems">
          {[0, 1, 2].map((i) => (
            <li
              key={i}
              className="h-16 animate-pulse rounded-lg border border-hairline bg-surface-2"
            />
          ))}
        </ul>
      )}

      {state.status === "error" && (
        <p className="rounded-md bg-rose-500/10 px-3 py-2 text-sm text-rose-300">
          Couldn&apos;t load problems: {state.message}
        </p>
      )}

      {state.status === "loaded" && (
        <>
          {state.usedMock && (
            <p className="mb-4 rounded-md bg-amber-500/10 px-3 py-2 text-xs text-amber-300">
              Backend unreachable at the configured API URL. Showing offline sample problems.
            </p>
          )}
          <ul className="space-y-3">
            {state.problems.map((problem) => (
              <li key={problem.slug}>
                <Link
                  href={`/tutor/${problem.slug}`}
                  className="flex items-center justify-between rounded-lg border border-hairline bg-surface px-4 py-4 transition-colors hover:border-hairline-strong hover:bg-surface-2"
                >
                  <span className="text-sm font-medium text-ink">
                    {problem.title}
                  </span>
                  <span className={difficultyBadgeClasses(problem.difficulty)}>
                    {problem.difficulty}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </>
      )}
      </div>
    </main>
  );
}
