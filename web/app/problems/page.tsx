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
    <main className="mx-auto min-h-screen w-full max-w-3xl px-6 py-12">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">Pick a problem</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Choose a problem to start a tutoring session. You&apos;ll explain your approach out loud,
          write real code, and run it against real test cases.
        </p>
      </div>

      {state.status === "loading" && (
        <ul className="space-y-3" aria-label="Loading problems">
          {[0, 1, 2].map((i) => (
            <li
              key={i}
              className="h-16 animate-pulse rounded-lg border border-slate-200 bg-slate-100 dark:border-slate-800 dark:bg-slate-800/50"
            />
          ))}
        </ul>
      )}

      {state.status === "error" && (
        <p className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">
          Couldn&apos;t load problems: {state.message}
        </p>
      )}

      {state.status === "loaded" && (
        <>
          {state.usedMock && (
            <p className="mb-4 rounded-md bg-amber-50 px-3 py-2 text-xs text-amber-800 dark:bg-amber-500/10 dark:text-amber-300">
              Backend unreachable at the configured API URL. Showing offline sample problems.
            </p>
          )}
          <ul className="space-y-3">
            {state.problems.map((problem) => (
              <li key={problem.slug}>
                <Link
                  href={`/tutor/${problem.slug}`}
                  className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-4 py-4 transition-colors hover:border-slate-300 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:hover:border-slate-700 dark:hover:bg-slate-800/60"
                >
                  <span className="text-sm font-medium text-slate-900 dark:text-slate-100">
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
    </main>
  );
}
