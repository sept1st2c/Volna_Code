"use client";

import { useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";

const features = [
  {
    title: "Understand the problem",
    body: "You explain the problem back in your own words. The tutor checks that explanation against the problem's real edge cases before it lets you move on, not a vague nod that you 'got it.'",
  },
  {
    title: "Find the approach",
    body: "Say your brute force approach out loud first and defend it. The tutor grades it against an authored explanation of why it falls short, then walks you up a hint ladder toward the optimal approach, one level at a time.",
  },
  {
    title: "Write & defend your code",
    body: "Type real code in the editor. The tutor asks why you made specific decisions while you're mid-thought, then runs your code against real test cases, including the edge cases most people forget.",
  },
];

export function FeatureRow() {
  const [active, setActive] = useState(0);
  const shouldReduceMotion = useReducedMotion();
  const activeFeature = features[active];

  return (
    <section className="relative overflow-hidden py-20 sm:py-28">
      {/* Giant ghost numeral watermark behind the content, echoing the active step. */}
      <AnimatePresence mode="wait">
        <motion.span
          key={active}
          aria-hidden
          initial={shouldReduceMotion ? false : { opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
          className="font-display pointer-events-none absolute left-1/2 top-1/2 -z-0 -translate-x-1/2 -translate-y-1/2 select-none text-[46vw] leading-none text-white/[0.025] sm:text-[32vw]"
        >
          {String(active + 1).padStart(2, "0")}
        </motion.span>
      </AnimatePresence>

      <div className="relative mx-auto max-w-[900px] px-6 sm:px-8">
        {/* Horizontal numeral selector with a sliding indicator underneath. */}
        <div className="flex items-end justify-center gap-10 sm:gap-16">
          {features.map((feature, i) => {
            const isActive = i === active;
            return (
              <button
                key={feature.title}
                type="button"
                onMouseEnter={() => setActive(i)}
                onFocus={() => setActive(i)}
                aria-label={feature.title}
                aria-pressed={isActive}
                className="group/num relative flex flex-col items-center gap-4 outline-none"
              >
                <span
                  className={`font-display text-[56px] leading-none transition-all duration-300 sm:text-[80px] ${
                    isActive
                      ? "scale-100 text-ink opacity-100"
                      : "scale-[0.72] text-stone opacity-50 group-hover/num:opacity-75"
                  }`}
                  style={
                    isActive
                      ? {
                          backgroundImage: "var(--gradient-ember)",
                          WebkitBackgroundClip: "text",
                          backgroundClip: "text",
                          color: "transparent",
                        }
                      : undefined
                  }
                >
                  {String(i + 1).padStart(2, "0")}
                </span>
                {isActive && (
                  <motion.span
                    layoutId="feature-indicator"
                    className="h-[3px] w-10 rounded-full"
                    style={{ background: "var(--gradient-ember)" }}
                    transition={
                      shouldReduceMotion
                        ? { duration: 0 }
                        : { type: "spring", stiffness: 380, damping: 32 }
                    }
                  />
                )}
              </button>
            );
          })}
        </div>

        {/* Crossfading content tied to whichever step is active. */}
        <div className="relative mt-14 min-h-[168px] text-center sm:min-h-[140px]">
          <AnimatePresence mode="wait">
            <motion.div
              key={active}
              initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.25, ease: "easeOut" }}
            >
              <h3 className="text-[26px] font-medium leading-[1.25] text-ink sm:text-[30px]">
                {activeFeature.title}
              </h3>
              <p className="mx-auto mt-4 max-w-[520px] text-[16px] leading-[1.6] text-slate">
                {activeFeature.body}
              </p>
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </section>
  );
}
