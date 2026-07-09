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
    <section className="flex h-full flex-col overflow-hidden rounded-lg border border-hairline bg-surface">
      <header className="flex items-center justify-between border-b border-hairline px-4 py-3">
        <h2 className="text-sm font-semibold text-ink">Tutor conversation</h2>
        <span
          className={`inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${
            isLive
              ? "bg-emerald-500/10 text-emerald-400 ring-emerald-500/20"
              : "bg-surface-2 text-steel ring-hairline-strong"
          }`}
        >
          <span className={`h-1.5 w-1.5 rounded-full ${isLive ? "bg-emerald-500" : "bg-stone"}`} />
          {isLive ? "Live" : "Example transcript"}
        </span>
      </header>

      <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
        {messages.length === 0 ? (
          <p className="text-sm text-steel">
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
                    ? "border border-transparent text-on-primary"
                    : "border border-hairline-soft bg-surface-2 text-ink"
                }`}
                style={
                  message.role === "user"
                    ? { background: "var(--gradient-ember-soft)" }
                    : undefined
                }
              >
                <p>{message.text}</p>
                {message.timestamp && (
                  <p
                    className={`mt-1 text-[10px] ${
                      message.role === "user" ? "text-white/70" : "text-stone"
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
