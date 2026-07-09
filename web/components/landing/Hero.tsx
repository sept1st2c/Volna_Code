"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { GridBackground } from "./GridBackground";

const headline = [
  "Your",
  "DSA",
  "tutor",
  "that",
  "never",
  "skips",
  "to",
  "the",
  "answer.",
];

// The word that carries the ember gradient accent in the headline.
const accentWords = new Set(["never", "skips"]);

export function Hero() {
  const shouldReduceMotion = useReducedMotion();

  return (
    <section id="top" className="relative overflow-hidden bg-canvas">
      <GridBackground variant="grid" aurora animated />

      {/* Top hairline of warm light, echoing the sunset brand at the seam. */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-px"
        style={{
          background:
            "linear-gradient(90deg, transparent, rgba(255,138,42,0.6), transparent)",
        }}
      />

      <div className="relative mx-auto grid max-w-[1280px] gap-14 px-6 py-24 sm:px-8 sm:py-32 lg:grid-cols-[1.08fr_0.92fr] lg:items-center lg:py-[128px]">
        <div>
          <motion.span
            initial={shouldReduceMotion ? false : { opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="inline-flex items-center gap-2 rounded-full border border-hairline-strong bg-white/[0.03] px-3 py-1 text-xs font-semibold uppercase tracking-wider text-ink-tint backdrop-blur"
          >
            <span className="relative flex h-1.5 w-1.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-75" />
              <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-primary" />
            </span>
            Voice AI DSA tutor
          </motion.span>

          <h1 className="font-display mt-6 text-[40px] leading-[1.04] tracking-[-0.5px] text-ink sm:text-[52px] lg:text-[64px] xl:text-[80px] xl:tracking-[-1.5px]">
            {headline.map((word, i) => (
              <motion.span
                key={`${word}-${i}`}
                initial={
                  shouldReduceMotion
                    ? false
                    : { opacity: 0, y: "0.4em", filter: "blur(6px)" }
                }
                animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
                transition={{
                  duration: 0.5,
                  delay: shouldReduceMotion ? 0 : 0.15 + i * 0.06,
                  ease: [0.22, 1, 0.36, 1],
                }}
                className={`inline-block ${
                  accentWords.has(word) ? "text-gradient-ember" : ""
                }`}
              >
                {word}
                {i < headline.length - 1 ? " " : ""}
              </motion.span>
            ))}
          </h1>

          <motion.p
            initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: shouldReduceMotion ? 0 : 0.75 }}
            className="mt-6 max-w-xl text-lg leading-[1.55] text-slate"
          >
            Explain the problem back. Defend your approach out loud. Watch real
            test cases catch what you missed. Then do it again, better.
          </motion.p>

          <motion.div
            initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: shouldReduceMotion ? 0 : 0.88 }}
            className="mt-10 flex flex-wrap items-center gap-4"
          >
            <Link
              href="/problems"
              className="btn-ember rounded-md px-5 py-2.5 text-sm font-semibold"
            >
              Try it
            </Link>
            <a
              href="#how-it-thinks"
              className="btn-ghost rounded-md px-5 py-2.5 text-sm font-medium"
            >
              See how it thinks
            </a>
          </motion.div>
        </div>

        <HeroPanel />
      </div>
    </section>
  );
}

/**
 * Right-side hero visual: a glass panel showing the tutoring loop as a live
 * "signal" moving between phases. Replaces the previous empty placeholder box.
 */
function HeroPanel() {
  const shouldReduceMotion = useReducedMotion();
  const phases = ["Explain", "Approach", "Code", "Execute", "Iterate"];

  return (
    <motion.div
      aria-hidden
      initial={shouldReduceMotion ? false : { opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: shouldReduceMotion ? 0 : 0.5 }}
      className="hidden lg:block"
    >
      <div className="glow-border relative ml-auto w-full max-w-[440px] overflow-hidden rounded-xl border border-hairline-soft bg-surface-2/80 p-6 backdrop-blur">
        <div className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-[#ff5f57]" />
          <span className="h-2.5 w-2.5 rounded-full bg-[#febc2e]" />
          <span className="h-2.5 w-2.5 rounded-full bg-[#28c840]" />
          <span className="ml-2 font-mono text-[11px] text-steel">
            session.state
          </span>
        </div>

        <div className="mt-6 flex flex-col gap-2.5">
          {phases.map((phase, i) => (
            <div
              key={phase}
              className="relative flex items-center gap-3 rounded-lg border border-hairline-soft bg-white/[0.02] px-3.5 py-2.5"
            >
              <span className="font-mono text-[11px] text-stone">
                {String(i + 1).padStart(2, "0")}
              </span>
              <span className="font-mono text-sm text-ink-tint">{phase}</span>
              {!shouldReduceMotion ? (
                <motion.span
                  className="absolute right-3 h-1.5 w-1.5 rounded-full bg-signal-1"
                  style={{ boxShadow: "0 0 10px 2px rgba(47,214,195,0.8)" }}
                  animate={{ opacity: [0.15, 1, 0.15] }}
                  transition={{
                    duration: 2.4,
                    repeat: Infinity,
                    delay: i * 0.48,
                    ease: "easeInOut",
                  }}
                />
              ) : null}
            </div>
          ))}
        </div>

        <div className="mt-6 rounded-lg border border-hairline-soft bg-surface-code px-4 py-3 font-mono text-[12px] leading-relaxed">
          <span className="text-on-dark-muted"># conditional edge</span>
          <br />
          <span className="text-[#4bb8ff]">if</span>{" "}
          <span className="text-ink-tint">grade.passed:</span>{" "}
          <span className="text-[#2fd6c3]">advance()</span>
        </div>
      </div>
    </motion.div>
  );
}
