"use client";

import { use, useEffect, useState } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { getProblem } from "@/lib/api";
import { difficultyBadgeClasses } from "@/lib/ui";
import { PLACEHOLDER_CHAT_MESSAGES, SAMPLE_SUBMISSION_RESULT } from "@/lib/mock-data";
import ProblemStatementPanel from "@/components/ProblemStatementPanel";
import ChatPanel from "@/components/ChatPanel";
import VoiceControls from "@/components/VoiceControls";
import TestResultsPanel from "@/components/TestResultsPanel";
import type { ProblemDetail, SubmissionResult } from "@/lib/types";

// Monaco touches `window`/`self` at import time, so it must be excluded from
// SSR entirely. Loaded lazily on the client only.
const CodeEditorPanel = dynamic(() => import("@/components/CodeEditorPanel"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full items-center justify-center text-sm text-slate-400 dark:text-slate-500">
      Loading editor…
    </div>
  ),
});

interface TutorSessionPageProps {
  params: Promise<{ slug: string }>;
}

type LoadResult =
  | { slug: string; status: "loaded"; problem: ProblemDetail; usedMock: boolean }
  | { slug: string; status: "error"; message: string };

export default function TutorSessionPage({ params }: TutorSessionPageProps) {
  const { slug } = use(params);

  // `result` is keyed by the slug it was fetched for. If it doesn't match the
  // current slug (first render for this slug, or slug just changed), the UI
  // below derives a "loading" view instead of a separate status flag — this
  // avoids resetting state imperatively inside the effect body.
  const [result, setLoadResult] = useState<LoadResult | null>(null);
  const [code, setCode] = useState<string>("");
  const [submission, setSubmission] = useState<SubmissionResult | null>(null);

  useEffect(() => {
    let cancelled = false;
    getProblem(slug)
      .then(({ problem, usedMock }) => {
        if (cancelled) return;
        setLoadResult({ slug, status: "loaded", problem, usedMock });
        setCode(problem.starter_code);
      })
      .catch((err) => {
        if (!cancelled) setLoadResult({ slug, status: "error", message: String(err) });
      });
    return () => {
      cancelled = true;
    };
  }, [slug]);

  const state: LoadResult | { status: "loading" } =
    result && result.slug === slug ? result : { status: "loading" };

  return (
    <main className="flex min-h-screen flex-col bg-slate-50 dark:bg-slate-950">
      <header className="flex items-center gap-3 border-b border-slate-200 bg-white px-6 py-3 dark:border-slate-800 dark:bg-slate-900">
        <Link
          href="/problems"
          className="text-sm text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200"
        >
          ← Problems
        </Link>
        {state.status === "loaded" && (
          <>
            <span className="text-slate-300 dark:text-slate-700">/</span>
            <h1 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
              {state.problem.title}
            </h1>
            <span className={difficultyBadgeClasses(state.problem.difficulty)}>
              {state.problem.difficulty}
            </span>
          </>
        )}
      </header>

      {state.status === "loading" && (
        <div className="flex flex-1 items-center justify-center text-sm text-slate-400 dark:text-slate-500">
          Loading problem…
        </div>
      )}

      {state.status === "error" && (
        <div className="flex flex-1 items-center justify-center px-6">
          <p className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">
            Couldn&apos;t load this problem: {state.message}
          </p>
        </div>
      )}

      {state.status === "loaded" && (
        <div className="grid flex-1 grid-cols-1 gap-4 p-4 lg:grid-cols-[360px_1fr_360px]">
          <div className="min-h-[320px] lg:h-[calc(100vh-64px)]">
            <ProblemStatementPanel problem={state.problem} usedMock={state.usedMock} />
          </div>

          <div className="flex min-h-0 flex-col gap-3 lg:h-[calc(100vh-64px)]">
            <div className="h-[420px] shrink-0 overflow-hidden rounded-lg border border-slate-200 dark:border-slate-800 lg:h-[65%]">
              <CodeEditorPanel
                value={code}
                language={state.problem.language ?? "python"}
                onChange={setCode}
              />
            </div>
            <div className="flex shrink-0 items-center justify-between gap-2">
              <p className="text-xs text-slate-400 dark:text-slate-500">
                Real submission runs over the LiveKit data channel once the agent worker exists.
              </p>
              <button
                type="button"
                onClick={() => setSubmission((r) => (r ? null : SAMPLE_SUBMISSION_RESULT))}
                className="shrink-0 rounded-md border border-slate-300 px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
              >
                {submission ? "Clear sample result" : "Preview sample result (dev)"}
              </button>
            </div>
            <div className="min-h-0 flex-1 overflow-y-auto">
              <TestResultsPanel result={submission} />
            </div>

          </div>

          <div className="flex min-h-0 flex-col gap-4 lg:h-[calc(100vh-64px)]">
            <div className="shrink-0">
              <VoiceControls problemSlug={slug} />
            </div>
            <div className="min-h-0 flex-1 overflow-hidden">
              <ChatPanel messages={PLACEHOLDER_CHAT_MESSAGES} />
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
