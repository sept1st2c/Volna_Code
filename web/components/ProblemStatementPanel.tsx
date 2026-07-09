import { difficultyBadgeClasses } from "@/lib/ui";
import type { ProblemDetail, TestCasePreview } from "@/lib/types";

/** Backend sends raw `args`, not prose -- render `nums=[2,7,11,15], target=9`. */
function formatArgs(args: Record<string, unknown>): string {
  return Object.entries(args)
    .map(([key, value]) => `${key}=${JSON.stringify(value)}`)
    .join(", ");
}

/** All test cases exist for grading, not display -- showing all of them (a
 * problem can have 100+) would overwhelm this panel. Curate a small, useful
 * set: every edge case (there are only ever a handful), plus enough plain
 * cases to round out to at least 3 total. */
function curateExampleCases(testCases: TestCasePreview[]): TestCasePreview[] {
  const edgeCases = testCases.filter((tc) => tc.is_edge_case);
  const plainCases = testCases.filter((tc) => !tc.is_edge_case);
  const plainNeeded = Math.max(0, 3 - edgeCases.length);
  return [...plainCases.slice(0, plainNeeded), ...edgeCases];
}

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
    <section className="flex h-full flex-col overflow-hidden rounded-lg border border-hairline bg-surface">
      <header className="border-b border-hairline px-5 py-4">
        <div className="flex items-start justify-between gap-2">
          <h1 className="text-lg font-semibold text-ink">{problem.title}</h1>
          <span className={difficultyBadgeClasses(problem.difficulty)}>{problem.difficulty}</span>
        </div>
        {usedMock && (
          <p className="mt-2 rounded-md bg-amber-500/10 px-2 py-1 text-xs text-amber-300">
            Backend unreachable. Showing offline sample data.
          </p>
        )}
      </header>

      <div className="flex-1 space-y-6 overflow-y-auto px-5 py-4">
        <div>
          <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-steel">
            Statement
          </h2>
          <p className="whitespace-pre-line text-sm leading-6 text-ink-tint">
            {problem.statement}
          </p>
        </div>

        <div>
          <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-steel">
            Constraints
          </h2>
          <ul className="list-inside list-disc space-y-1 text-sm text-ink-tint">
            {problem.constraints.map((constraint) => (
              <li key={constraint} className="font-mono text-[13px]">
                {constraint}
              </li>
            ))}
          </ul>
        </div>

        {problem.test_cases && problem.test_cases.length > 0 && (
          <div>
            <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-steel">
              Example cases
            </h2>
            <ul className="space-y-2">
              {curateExampleCases(problem.test_cases).map((tc) => (
                <li
                  key={tc.id}
                  className="rounded-md border border-hairline bg-surface-2 px-3 py-2 text-xs text-ink-tint"
                >
                  <span className="font-mono">{formatArgs(tc.args)}</span>
                  {tc.is_edge_case && (
                    <span className="ml-2 inline-flex items-center rounded-md bg-sky-500/10 px-1.5 py-0.5 text-[10px] font-medium text-sky-300 ring-1 ring-inset ring-sky-500/20">
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
            <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-steel">
              Brute force (starting point)
            </h2>
            <p className="text-sm text-ink-tint">{problem.brute_force.description}</p>
            <p className="mt-1 font-mono text-xs text-steel">
              {problem.brute_force.complexity}
            </p>
          </div>
        )}
      </div>
    </section>
  );
}
