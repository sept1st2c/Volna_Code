"use client";

import { motion, useReducedMotion } from "framer-motion";

type NodeSpec = {
  id: string;
  label: string;
  caption: string;
  x: number;
  y: number;
  variant: "spine" | "side" | "terminal";
};

type EdgeSpec = {
  id: string;
  d: string;
  label?: string;
  labelX?: number;
  labelY?: number;
};

const W = 200;
const H = 56;

// Node layout mirrors the Core State Machine mermaid diagram in PLAN.md
// verbatim: INTRO through COMPLETE, including the comprehension loop
// (CHECK <-> REMEDIATION) and the iteration loop (FEEDBACK -> ITERATION ->
// CODING / HINT_LADDER).
const nodes: NodeSpec[] = [
  { id: "INTRO", label: "INTRO", x: 200, y: 40, variant: "spine", caption: "Introduces the problem in our own wording. Nothing here is scraped LeetCode text." },
  { id: "COMPREHENSION_CHECK", label: "COMPREHENSION_CHECK", x: 200, y: 180, variant: "spine", caption: "Grades your explanation against the problem's real edge cases, not vibes." },
  { id: "COMPREHENSION_REMEDIATION", label: "COMPREHENSION_REMEDIATION", x: 500, y: 180, variant: "side", caption: "Surfaces one authored loophole at a time until you actually see it, then sends you back to explain again." },
  { id: "APPROACH_DISCUSSION", label: "APPROACH_DISCUSSION", x: 200, y: 320, variant: "spine", caption: "You describe an approach out loud before a single line of code gets written." },
  { id: "BRUTE_FORCE_ANALYSIS", label: "BRUTE_FORCE_ANALYSIS", x: 200, y: 460, variant: "spine", caption: "Grades your brute force against an authored 'why it's insufficient,' never an improvised excuse." },
  { id: "HINT_LADDER", label: "HINT_LADDER", x: 200, y: 600, variant: "spine", caption: "Hints are pulled verbatim from an authored ladder. The model only decides when you've earned the next level." },
  { id: "CODING", label: "CODING", x: 200, y: 740, variant: "spine", caption: "You write real code in the editor while the tutor asks why, referencing your actual diff." },
  { id: "EXECUTING", label: "EXECUTING", x: 200, y: 880, variant: "spine", caption: "Your code runs in a real sandbox against real test cases. Nothing here is simulated." },
  { id: "FEEDBACK", label: "FEEDBACK", x: 200, y: 1020, variant: "spine", caption: "Narrates Piston's actual result. It explains a verdict, it never invents one." },
  { id: "ITERATION", label: "ITERATION", x: 500, y: 1020, variant: "side", caption: "Failed a test, or complexity's off? Back to coding, or back to hints if you're fundamentally stuck." },
  { id: "COMPLETE", label: "COMPLETE", x: 200, y: 1160, variant: "terminal", caption: "All tests pass and the complexity holds up. Done, for real this time." },
];

const edges: EdgeSpec[] = [
  { id: "e-intro-check", d: "M200,68 L200,152" },
  { id: "e-check-approach", d: "M200,208 L200,292", label: "ready to advance", labelX: 214, labelY: 250 },
  { id: "e-approach-brute", d: "M200,348 L200,432", label: "brute force described", labelX: 214, labelY: 390 },
  { id: "e-brute-hint", d: "M200,488 L200,572" },
  { id: "e-hint-coding", d: "M200,628 L200,712", label: "optimal approach found", labelX: 214, labelY: 670 },
  { id: "e-coding-exec", d: "M200,768 L200,852", label: "submit via data channel", labelX: 214, labelY: 810 },
  { id: "e-exec-feedback", d: "M200,908 L200,992" },
  { id: "e-feedback-complete", d: "M200,1048 L200,1132", label: "all pass + good complexity", labelX: 214, labelY: 1090 },
  { id: "e-check-remediation", d: "M300,166 Q350,146 400,166", label: "gaps found", labelX: 350, labelY: 138 },
  { id: "e-remediation-check", d: "M400,196 Q350,216 300,196" },
  { id: "e-hint-self", d: "M300,588 C372,552 372,648 300,612", label: "stuck 2+ turns", labelX: 388, labelY: 600 },
  { id: "e-feedback-iteration", d: "M300,1010 Q350,998 400,1012", label: "tests failed / can improve", labelX: 350, labelY: 985 },
  { id: "e-iteration-coding", d: "M420,996 C 500,880 480,760 300,744" },
  { id: "e-iteration-hint", d: "M420,1044 C 580,900 560,640 300,610", label: "fundamentally stuck again", labelX: 470, labelY: 800 },
];

function nodeFill(variant: NodeSpec["variant"]) {
  if (variant === "terminal") return "var(--color-primary)";
  if (variant === "side") return "var(--color-cream)";
  return "var(--color-ink)";
}

function nodeText(variant: NodeSpec["variant"]) {
  if (variant === "side") return "var(--color-ink)";
  return "var(--color-on-dark)";
}

export function GraphSection() {
  const shouldReduceMotion = useReducedMotion();

  return (
    <section id="how-it-thinks" className="bg-surface py-16 sm:py-24">
      <div className="mx-auto max-w-[1280px] px-6 sm:px-8">
        <span className="text-[11px] font-semibold uppercase tracking-[1px] text-primary">
          How it actually thinks
        </span>
        <h2 className="font-display mt-3 max-w-2xl text-[32px] leading-[1.15] tracking-[-0.5px] text-ink sm:text-[40px]">
          A state machine grading real answers, not a chatbot guessing what to
          say next.
        </h2>
        <p className="mt-4 max-w-2xl text-[17px] leading-[1.55] text-slate">
          This is the actual LangGraph running the tutoring session: every
          phase is a node, every transition is a conditional edge reading
          structured output, and the LLM never chooses its own next step.
          Scroll to watch it draw.
        </p>

        <div className="mt-12 overflow-x-auto">
          <svg
            viewBox="0 0 640 1220"
            className="mx-auto w-full max-w-[640px]"
            role="img"
            aria-label="LangGraph state machine diagram from INTRO to COMPLETE, including the comprehension and hint/coding/execution loops"
          >
            {edges.map((edge, i) => (
              <g key={edge.id}>
                <motion.path
                  d={edge.d}
                  fill="none"
                  stroke="var(--color-hairline-strong)"
                  strokeWidth={2}
                  initial={shouldReduceMotion ? { pathLength: 1, opacity: 1 } : { pathLength: 0, opacity: 0 }}
                  whileInView={{ pathLength: 1, opacity: 1 }}
                  viewport={{ once: true, amount: 0.2 }}
                  transition={{
                    duration: shouldReduceMotion ? 0 : 0.25,
                    delay: shouldReduceMotion ? 0 : i * 0.15,
                    ease: "easeInOut",
                  }}
                />
                {edge.label ? (
                  <motion.text
                    x={edge.labelX}
                    y={edge.labelY}
                    fontSize="11"
                    fill="var(--color-steel)"
                    fontFamily="var(--font-sans)"
                    initial={shouldReduceMotion ? { opacity: 1 } : { opacity: 0 }}
                    whileInView={{ opacity: 1 }}
                    viewport={{ once: true, amount: 0.2 }}
                    transition={{
                      duration: shouldReduceMotion ? 0 : 0.2,
                      delay: shouldReduceMotion ? 0 : i * 0.15 + 0.15,
                    }}
                  >
                    {edge.label}
                  </motion.text>
                ) : null}
              </g>
            ))}

            {nodes.map((node, i) => (
              <motion.g
                key={node.id}
                initial={shouldReduceMotion ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.92 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true, amount: 0.2 }}
                transition={{
                  duration: shouldReduceMotion ? 0 : 0.22,
                  delay: shouldReduceMotion ? 0 : i * 0.18 + 0.1,
                  ease: "easeOut",
                }}
                style={{ transformOrigin: `${node.x}px ${node.y}px` }}
              >
                <rect
                  x={node.x - W / 2}
                  y={node.y - H / 2}
                  width={W}
                  height={H}
                  rx={node.variant === "side" ? 12 : 8}
                  fill={nodeFill(node.variant)}
                  stroke={node.variant === "side" ? "var(--color-beige-deep)" : "transparent"}
                />
                <text
                  x={node.x}
                  y={node.y + 4}
                  textAnchor="middle"
                  fontSize="11"
                  fontWeight={600}
                  fontFamily="var(--font-mono)"
                  fill={nodeText(node.variant)}
                >
                  {node.label}
                </text>
              </motion.g>
            ))}
          </svg>
        </div>

        {/* Captions rendered as accessible text alongside the diagram, in
            graph order, so the "what really happens here" content is
            available without relying on hover/tooltips inside the SVG. */}
        <ol className="mt-14 grid gap-x-8 gap-y-6 sm:grid-cols-2">
          {nodes.map((node, i) => (
            <motion.li
              key={node.id}
              initial={shouldReduceMotion ? { opacity: 1, y: 0 } : { opacity: 0, y: 8 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.4 }}
              transition={{
                duration: shouldReduceMotion ? 0 : 0.2,
                delay: shouldReduceMotion ? 0 : i * 0.06,
              }}
              className="flex gap-3"
            >
              <span className="mt-0.5 font-mono text-xs font-semibold text-primary">
                {String(i + 1).padStart(2, "0")}
              </span>
              <div>
                <p className="font-mono text-xs font-semibold text-ink">
                  {node.label}
                </p>
                <p className="mt-1 text-sm leading-[1.5] text-slate">
                  {node.caption}
                </p>
              </div>
            </motion.li>
          ))}
        </ol>
      </div>
    </section>
  );
}
