"use client";

import { useEffect, useRef } from "react";
import type { ChatMessage } from "@/lib/types";

export interface ChatPanelProps {
  messages: ChatMessage[];
  /** Optional: lets the page show a "live" vs "example transcript" indicator. */
  isLive?: boolean;
}

/**
 * Transcript area for the tutoring conversation. Currently seeded with
 * placeholder messages passed in by the page; once the LiveKit agent worker
 * exists, the same component renders the real streamed transcript by simply
 * pushing new ChatMessage entries into the `messages` array.
 */
export default function ChatPanel({ messages, isLive = false }: ChatPanelProps) {
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  return (
    <section className="flex h-full flex-col overflow-hidden rounded-lg border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
      <header className="flex items-center justify-between border-b border-slate-200 px-4 py-3 dark:border-slate-800">
        <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">Tutor conversation</h2>
        <span
          className={`inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${
            isLive
              ? "bg-emerald-50 text-emerald-700 ring-emerald-600/20 dark:bg-emerald-500/10 dark:text-emerald-400 dark:ring-emerald-500/20"
              : "bg-slate-100 text-slate-600 ring-slate-600/20 dark:bg-slate-500/10 dark:text-slate-300 dark:ring-slate-500/20"
          }`}
        >
          <span className={`h-1.5 w-1.5 rounded-full ${isLive ? "bg-emerald-500" : "bg-slate-400"}`} />
          {isLive ? "Live" : "Example transcript"}
        </span>
      </header>

      <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
        {messages.length === 0 ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">
            No conversation yet. Connect voice to start the session.
          </p>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[85%] rounded-lg px-3 py-2 text-sm leading-5 ${
                  message.role === "user"
                    ? "bg-slate-900 text-slate-50 dark:bg-slate-100 dark:text-slate-900"
                    : "bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-200"
                }`}
              >
                <p>{message.text}</p>
                {message.timestamp && (
                  <p
                    className={`mt-1 text-[10px] ${
                      message.role === "user"
                        ? "text-slate-300 dark:text-slate-600"
                        : "text-slate-400 dark:text-slate-500"
                    }`}
                  >
                    {message.timestamp}
                  </p>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </section>
  );
}
