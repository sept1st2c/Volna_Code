import { difficultyBadgeClasses } from "@/lib/ui";
import type { ProblemDetail } from "@/lib/types";

export interface ProblemStatementPanelProps {
  problem: ProblemDetail;
  /** Shown as a small banner when the detail came from local mock data. */
  usedMock?: boolean;
}

/**
 * Left-hand panel of the tutor session: problem statement, constraints, and
 * the authored brute-force / optimal approach summaries. Pure presentation,
 * takes a fully-resolved ProblemDetail so swapping mock data for a real fetch
 * is a no-op here.
 */
export default function ProblemStatementPanel({ problem, usedMock }: ProblemStatementPanelProps) {
  return (
    <section className="flex h-full flex-col overflow-hidden rounded-lg border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
      <header className="border-b border-slate-200 px-5 py-4 dark:border-slate-800">
        <div className="flex items-start justify-between gap-2">
          <h1 className="text-lg font-semibold text-slate-900 dark:text-slate-100">{problem.title}</h1>
          <span className={difficultyBadgeClasses(problem.difficulty)}>{problem.difficulty}</span>
        </div>
        {usedMock && (
          <p className="mt-2 rounded-md bg-amber-50 px-2 py-1 text-xs text-amber-800 dark:bg-amber-500/10 dark:text-amber-300">
            Backend unreachable. Showing offline sample data.
          </p>
        )}
      </header>

      <div className="flex-1 space-y-6 overflow-y-auto px-5 py-4">
        <div>
          <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
            Statement
          </h2>
          <p className="whitespace-pre-line text-sm leading-6 text-slate-700 dark:text-slate-300">
            {problem.statement}
          </p>
        </div>

        <div>
          <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
            Constraints
          </h2>
          <ul className="list-inside list-disc space-y-1 text-sm text-slate-700 dark:text-slate-300">
            {problem.constraints.map((constraint) => (
              <li key={constraint} className="font-mono text-[13px]">
                {constraint}
              </li>
            ))}
          </ul>
        </div>

        {problem.test_cases && problem.test_cases.length > 0 && (
          <div>
            <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
              Example cases
            </h2>
            <ul className="space-y-2">
              {problem.test_cases.map((tc) => (
                <li
                  key={tc.id}
                  className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600 dark:border-slate-800 dark:bg-slate-800/50 dark:text-slate-300"
                >
                  <span className="font-mono">{tc.description}</span>
                  {tc.is_edge_case && (
                    <span className="ml-2 inline-flex items-center rounded-md bg-sky-50 px-1.5 py-0.5 text-[10px] font-medium text-sky-700 ring-1 ring-inset ring-sky-600/20 dark:bg-sky-500/10 dark:text-sky-300 dark:ring-sky-500/20">
                      edge case{tc.edge_case_tag ? `: ${tc.edge_case_tag}` : ""}
                    </span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        {problem.brute_force && (
          <div>
            <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
              Brute force (starting point)
            </h2>
            <p className="text-sm text-slate-700 dark:text-slate-300">{problem.brute_force.description}</p>
            <p className="mt-1 font-mono text-xs text-slate-500 dark:text-slate-400">
              {problem.brute_force.complexity}
            </p>
          </div>
        )}
      </div>
    </section>
  );
}
