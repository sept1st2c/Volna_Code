"use client";

import { motion, useReducedMotion } from "framer-motion";
import { GridBackground } from "./GridBackground";

type Turn = { role: "tutor" | "you"; text: string };

// A scripted, fake conversation. The tutor doesn't exist yet (voice is M7 in
// PLAN.md's build sequencing): this is staged copy to show what the loop will
// feel like, not a recording of a real session.
const script: Turn[] = [
  { role: "tutor", text: "Let's start with Two Sum. Tell me the problem back in your own words." },
  { role: "you", text: "Given an array of numbers and a target, find two that add up to it and return their indices." },
  { role: "tutor", text: "Good. Now, what happens if the same value shows up twice, could one number satisfy the target using itself?" },
  { role: "you", text: "Oh. I guess I'd need to make sure I'm not using the same element twice." },
  { role: "tutor", text: "That's the loophole most people miss on this one. What's your first approach? Brute force is fine to start." },
  { role: "you", text: "Check every pair with two nested loops. That's O(n squared)." },
  { role: "tutor", text: "Why isn't that good enough once the input gets large?" },
  { role: "you", text: "It's quadratic, too slow for big arrays." },
  { role: "tutor", text: "Good, you defended it instead of just naming it. What if you didn't have to re-scan the array for every number?" },
  { role: "tutor", text: "Test 4 failed: duplicate value edge case. The same one you flagged earlier. Check your hash map lookup order." },
  { role: "tutor", text: "All five tests pass now, including the edge cases. Time complexity's O(n). That's a genuinely optimal solution, not just a passing one." },
];

export function DemoTranscript() {
  const shouldReduceMotion = useReducedMotion();

  return (
    <section id="demo" className="relative overflow-hidden bg-surface py-16 sm:py-24">
      <GridBackground variant="grid" />

      <div className="relative mx-auto max-w-[720px] px-6 sm:px-8">
        <span className="font-mono text-[11px] font-semibold uppercase tracking-[1px] text-primary">
          What a session sounds like
        </span>
        <h2 className="font-display mt-3 text-[32px] leading-[1.15] tracking-[-0.5px] text-ink sm:text-[40px]">
          A scripted preview, not a live demo yet.
        </h2>
        <p className="mt-4 text-[17px] leading-[1.55] text-slate">
          The voice loop ships in a later milestone. This is a realistic but
          fake transcript of the session it&apos;s being built toward, staged here
          so you can see the shape of the conversation before it exists.
        </p>

        <motion.ol
          className="mt-10 flex flex-col gap-4"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.15 }}
          variants={{
            hidden: {},
            visible: {
              transition: {
                staggerChildren: shouldReduceMotion ? 0 : 0.28,
              },
            },
          }}
        >
          {script.map((turn, i) => (
            <motion.li
              key={i}
              className={`flex ${turn.role === "you" ? "justify-end" : "justify-start"}`}
              variants={{
                hidden: shouldReduceMotion
                  ? { opacity: 1, y: 0 }
                  : { opacity: 0, y: 10 },
                visible: {
                  opacity: 1,
                  y: 0,
                  transition: { duration: shouldReduceMotion ? 0 : 0.22, ease: "easeOut" },
                },
              }}
            >
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 text-[15px] leading-[1.5] ${
                  turn.role === "tutor"
                    ? "rounded-tl-sm border border-hairline-soft bg-surface-2 text-ink"
                    : "rounded-tr-sm border border-transparent text-on-primary"
                }`}
                style={
                  turn.role === "you"
                    ? { background: "var(--gradient-ember-soft)" }
                    : undefined
                }
              >
                <p className="mb-1 font-mono text-[11px] font-semibold uppercase tracking-wide opacity-70">
                  {turn.role === "tutor" ? "Tutor" : "You"}
                </p>
                {turn.text}
              </div>
            </motion.li>
          ))}
        </motion.ol>
      </div>
    </section>
  );
}
