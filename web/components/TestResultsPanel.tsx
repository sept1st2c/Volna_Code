import type { SubmissionResult } from "@/lib/types";

export interface TestResultsPanelProps {
  /** null = no submission yet (empty state). Populated once Piston execution results arrive. */
  result: SubmissionResult | null;
}

/**
 * Renders the outcome of running the user's code against the problem's test
 * cases. Per PLAN.md, the real result arrives over the LiveKit data channel
 * after the agent worker calls Piston — this component only renders whatever
 * `SubmissionResult` it's handed, so wiring the real data source in later is
 * just passing a different `result` prop.
 */
export default function TestResultsPanel({ result }: TestResultsPanelProps) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
      <header className="flex items-center justify-between border-b border-slate-200 px-4 py-3 dark:border-slate-800">
        <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">Test results</h2>
        {result && (
          <span
            className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${
              result.allPassed
                ? "bg-emerald-50 text-emerald-700 ring-emerald-600/20 dark:bg-emerald-500/10 dark:text-emerald-400 dark:ring-emerald-500/20"
                : "bg-rose-50 text-rose-700 ring-rose-600/20 dark:bg-rose-500/10 dark:text-rose-400 dark:ring-rose-500/20"
            }`}
          >
            {result.allPassed ? "All passed" : "Failing"}
          </span>
        )}
      </header>

      <div className="px-4 py-4">
        {!result ? (
          <div className="flex flex-col items-center gap-2 py-6 text-center">
            <EmptyIcon />
            <p className="text-sm text-slate-500 dark:text-slate-400">No submission yet.</p>
            <p className="text-xs text-slate-400 dark:text-slate-500">
              Submit your code from the editor to run it against the problem&apos;s test cases.
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            <p className="text-xs text-slate-400 dark:text-slate-500">
              Submitted {new Date(result.submittedAt).toLocaleTimeString()}
            </p>
            <ul className="divide-y divide-slate-100 dark:divide-slate-800">
              {result.cases.map((testCase) => (
                <li key={testCase.id} className="flex items-start gap-3 py-2">
                  <StatusDot status={testCase.status} />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="truncate text-sm font-medium text-slate-800 dark:text-slate-200">
                        {testCase.label}
                      </span>
                      {testCase.isEdgeCase && (
                        <span className="inline-flex shrink-0 items-center rounded-md bg-sky-50 px-1.5 py-0.5 text-[10px] font-medium text-sky-700 ring-1 ring-inset ring-sky-600/20 dark:bg-sky-500/10 dark:text-sky-300 dark:ring-sky-500/20">
                          edge case
                        </span>
                      )}
                    </div>
                    {testCase.message && (
                      <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">{testCase.message}</p>
                    )}
                  </div>
                  <span
                    className={`shrink-0 text-xs font-medium ${
                      testCase.status === "pass"
                        ? "text-emerald-600 dark:text-emerald-400"
                        : "text-rose-600 dark:text-rose-400"
                    }`}
                  >
                    {testCase.status === "pass" ? "Pass" : "Fail"}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </section>
  );
}

function StatusDot({ status }: { status: "pass" | "fail" }) {
  return (
    <span
      className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${
        status === "pass" ? "bg-emerald-500" : "bg-rose-500"
      }`}
    />
  );
}

function EmptyIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      className="h-8 w-8 text-slate-300 dark:text-slate-700"
    >
      <path
        d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
