"use client";

import { use, useCallback, useEffect, useState } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { Room, RoomEvent, type TextStreamHandler } from "livekit-client";
import { getProblem } from "@/lib/api";
import { difficultyBadgeClasses } from "@/lib/ui";
import { PLACEHOLDER_CHAT_MESSAGES, SAMPLE_SUBMISSION_RESULT } from "@/lib/mock-data";
import {
  buildCodeSubmitPayload,
  parseExecutionResult,
  TRANSCRIPTION_SEGMENT_ID_ATTRIBUTE,
  TRANSCRIPTION_TOPIC,
  upsertTranscriptMessage,
} from "@/lib/voice-session";
import ProblemStatementPanel from "@/components/ProblemStatementPanel";
import ChatPanel from "@/components/ChatPanel";
import VoiceControls from "@/components/VoiceControls";
import TestResultsPanel from "@/components/TestResultsPanel";
import type { ChatMessage, ProblemDetail, SubmissionResult } from "@/lib/types";

// Monaco touches `window`/`self` at import time, so it must be excluded from
// SSR entirely. Loaded lazily on the client only.
const CodeEditorPanel = dynamic(() => import("@/components/CodeEditorPanel"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full items-center justify-center bg-surface-code text-sm text-stone">
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

  // Lifted up from VoiceControls (see its `onConnected`/`onDisconnected`
  // props) so this page and ChatPanel can share the same LiveKit room / data
  // channel the worker listens on, instead of VoiceControls owning it
  // privately.
  const [room, setRoom] = useState<Room | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const voiceConnected = room !== null;

  const handleVoiceConnected = useCallback((connectedRoom: Room) => {
    setRoom(connectedRoom);
    setChatMessages([]);
  }, []);

  const handleVoiceDisconnected = useCallback(() => {
    setRoom(null);
    setSubmitting(false);
  }, []);

  // Real transcript + submission-result wiring: registered against the
  // actual connected room and torn down whenever it changes/disconnects.
  useEffect(() => {
    if (!room) return;

    const handleDataReceived = (payload: Uint8Array) => {
      const executionResult = parseExecutionResult(payload);
      if (!executionResult) return; // malformed/unknown message type -- ignore, don't throw
      setSubmission(executionResult);
      setSubmitting(false);
    };

    const handleTranscriptionStream: TextStreamHandler = (reader, participantInfo) => {
      const segmentId = reader.info.attributes?.[TRANSCRIPTION_SEGMENT_ID_ATTRIBUTE] ?? reader.info.id;
      // The worker forwards the student's own recognized speech back under
      // their own identity (sender_identity), and its own narration under
      // the agent's identity -- see web/lib/voice-session.ts for the source
      // evidence. Our own identity means "this is us being echoed back".
      const role: ChatMessage["role"] =
        participantInfo.identity === room.localParticipant.identity ? "user" : "tutor";

      void (async () => {
        // `TextStreamReader`'s async iterator yields each chunk's OWN text
        // per iteration, not the cumulative string so far (confirmed by
        // reading the installed livekit-client source -- its `next()` calls
        // `decoder.decode(result.value.content)` on just that one chunk;
        // only the separate, non-incremental `readAll()` method
        // accumulates). Every delta has to be appended here ourselves, or
        // each spoken word replaces the last instead of building a sentence.
        let accumulated = "";
        try {
          for await (const delta of reader) {
            accumulated += delta;
            setChatMessages((prev) => upsertTranscriptMessage(prev, segmentId, role, accumulated));
          }
        } catch (err) {
          console.error("[voice] transcription text stream failed", err);
        }
      })();
    };

    room.on(RoomEvent.DataReceived, handleDataReceived);
    room.registerTextStreamHandler(TRANSCRIPTION_TOPIC, handleTranscriptionStream);

    return () => {
      room.off(RoomEvent.DataReceived, handleDataReceived);
      try {
        room.unregisterTextStreamHandler(TRANSCRIPTION_TOPIC);
      } catch {
        // Already unregistered (e.g. the room tore itself down first) -- fine to ignore.
      }
    };
  }, [room]);

  const handleSubmitCode = useCallback(() => {
    if (!room) return;
    setSubmitting(true);
    room.localParticipant
      .publishData(buildCodeSubmitPayload(code), { reliable: true })
      .catch((err) => {
        console.error("[voice] publishData(code_submit) failed", err);
        setSubmitting(false);
      });
  }, [room, code]);

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
    <main className="flex min-h-screen flex-col bg-canvas text-ink">
      <header className="flex items-center gap-3 border-b border-hairline bg-surface px-6 py-3">
        <Link href="/" className="font-display text-base tracking-tight text-ink">
          Volna
        </Link>
        <span className="text-stone">/</span>
        <Link
          href="/problems"
          className="text-sm text-steel hover:text-ink"
        >
          ← Problems
        </Link>
        {state.status === "loaded" && (
          <>
            <span className="text-stone">/</span>
            <h1 className="text-sm font-semibold text-ink">
              {state.problem.title}
            </h1>
            <span className={difficultyBadgeClasses(state.problem.difficulty)}>
              {state.problem.difficulty}
            </span>
          </>
        )}
      </header>

      {state.status === "loading" && (
        <div className="flex flex-1 items-center justify-center text-sm text-stone">
          Loading problem…
        </div>
      )}

      {state.status === "error" && (
        <div className="flex flex-1 items-center justify-center px-6">
          <p className="rounded-md bg-rose-500/10 px-3 py-2 text-sm text-rose-300">
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
            <div className="h-[420px] shrink-0 overflow-hidden rounded-lg border border-hairline lg:h-[65%]">
              <CodeEditorPanel
                value={code}
                language={state.problem.language ?? "python"}
                onChange={setCode}
              />
            </div>
            <div className="flex shrink-0 items-center justify-between gap-2">
              <p className="text-xs text-stone">
                {voiceConnected
                  ? submitting
                    ? "Running your code against the tutor's test cases…"
                    : "Submits over the connected LiveKit data channel."
                  : "Connect voice to submit real code -- or preview sample layout below (dev only)."}
              </p>
              {voiceConnected ? (
                <button
                  type="button"
                  onClick={handleSubmitCode}
                  disabled={submitting}
                  className="shrink-0 rounded-md bg-primary px-2.5 py-1.5 text-xs font-medium text-on-primary hover:bg-primary-deep disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {submitting ? "Submitting…" : "Submit"}
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => setSubmission((r) => (r ? null : SAMPLE_SUBMISSION_RESULT))}
                  className="shrink-0 rounded-md border border-hairline-strong px-2.5 py-1.5 text-xs font-medium text-ink-tint hover:bg-surface-2"
                >
                  {submission ? "Clear sample result" : "Preview sample result (dev)"}
                </button>
              )}
            </div>
            <div className="min-h-0 flex-1 overflow-y-auto">
              <TestResultsPanel result={submission} />
            </div>

          </div>

          <div className="flex min-h-0 flex-col gap-4 lg:h-[calc(100vh-64px)]">
            <div className="shrink-0">
              <VoiceControls
                problemSlug={slug}
                onConnected={handleVoiceConnected}
                onDisconnected={handleVoiceDisconnected}
              />
            </div>
            <div className="min-h-0 flex-1 overflow-hidden">
              <ChatPanel
                messages={voiceConnected ? chatMessages : PLACEHOLDER_CHAT_MESSAGES}
                isLive={voiceConnected}
              />
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
