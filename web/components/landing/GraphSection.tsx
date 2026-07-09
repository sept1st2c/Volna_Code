"use client";

import { useRef, useState } from "react";
import { motion, useInView, useReducedMotion } from "framer-motion";
import { GridBackground } from "./GridBackground";

type NodeSpec = {
  id: string;
  label: string;
  // Short classification of what kind of node this is in the graph. Truthful
  // to the architecture described in the caption, not invented flavor text.
  kind: string;
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
  // Loop/branch edges get a cooler treatment than the main spine.
  branch?: boolean;
};

const W = 200;
const H = 56;

// Node layout mirrors the Core State Machine mermaid diagram in PLAN.md
// verbatim: INTRO through COMPLETE, including the comprehension loop
// (CHECK <-> REMEDIATION) and the iteration loop (FEEDBACK -> ITERATION ->
// CODING / HINT_LADDER). Captions describe what each node really does.
const nodes: NodeSpec[] = [
  { id: "INTRO", label: "INTRO", kind: "Entry node", x: 200, y: 40, variant: "spine", caption: "Introduces the problem in our own wording. Nothing here is scraped LeetCode text." },
  { id: "COMPREHENSION_CHECK", label: "COMPREHENSION_CHECK", kind: "LLM-graded gate", x: 200, y: 180, variant: "spine", caption: "Grades your explanation against the problem's real edge cases, not vibes." },
  { id: "COMPREHENSION_REMEDIATION", label: "COMPREHENSION_REMEDIATION", kind: "Remediation loop", x: 500, y: 180, variant: "side", caption: "Surfaces one authored loophole at a time until you actually see it, then sends you back to explain again." },
  { id: "APPROACH_DISCUSSION", label: "APPROACH_DISCUSSION", kind: "Discussion node", x: 200, y: 320, variant: "spine", caption: "You describe an approach out loud before a single line of code gets written." },
  { id: "BRUTE_FORCE_ANALYSIS", label: "BRUTE_FORCE_ANALYSIS", kind: "LLM-graded gate", x: 200, y: 460, variant: "spine", caption: "Grades your brute force against an authored 'why it's insufficient,' never an improvised excuse." },
  { id: "HINT_LADDER", label: "HINT_LADDER", kind: "Authored hint ladder", x: 200, y: 600, variant: "spine", caption: "Hints are pulled verbatim from an authored ladder. The model only decides when you've earned the next level." },
  { id: "CODING", label: "CODING", kind: "Editor node", x: 200, y: 740, variant: "spine", caption: "You write real code in the editor while the tutor asks why, referencing your actual diff." },
  { id: "EXECUTING", label: "EXECUTING", kind: "Sandbox call (Piston)", x: 200, y: 880, variant: "spine", caption: "Your code runs in a real sandbox against real test cases. Nothing here is simulated." },
  { id: "FEEDBACK", label: "FEEDBACK", kind: "Verdict narration", x: 200, y: 1020, variant: "spine", caption: "Narrates Piston's actual result. It explains a verdict, it never invents one." },
  { id: "ITERATION", label: "ITERATION", kind: "Iteration router", x: 500, y: 1020, variant: "side", caption: "Failed a test, or complexity's off? Back to coding, or back to hints if you're fundamentally stuck." },
  { id: "COMPLETE", label: "COMPLETE", kind: "Terminal node", x: 200, y: 1160, variant: "terminal", caption: "All tests pass and the complexity holds up. Done, for real this time." },
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
  { id: "e-check-remediation", d: "M300,166 Q350,146 400,166", label: "gaps found", labelX: 350, labelY: 138, branch: true },
  { id: "e-remediation-check", d: "M400,196 Q350,216 300,196", branch: true },
  { id: "e-hint-self", d: "M300,588 C372,552 372,648 300,612", label: "stuck 2+ turns", labelX: 388, labelY: 600, branch: true },
  { id: "e-feedback-iteration", d: "M300,1010 Q350,998 400,1012", label: "tests failed / can improve", labelX: 350, labelY: 985, branch: true },
  { id: "e-iteration-coding", d: "M420,996 C 500,880 480,760 300,744", branch: true },
  { id: "e-iteration-hint", d: "M420,1044 C 580,900 560,640 300,610", label: "fundamentally stuck again", labelX: 470, labelY: 800, branch: true },
];

const VIEW_W = 640;
const TIP_W = 250;
const TIP_H = 128;

function nodeFill(variant: NodeSpec["variant"], hovered: boolean) {
  if (variant === "terminal") return "url(#grad-terminal)";
  if (variant === "side") return hovered ? "url(#grad-side-hot)" : "url(#grad-side)";
  return hovered ? "url(#grad-spine-hot)" : "url(#grad-spine)";
}

function nodeStroke(variant: NodeSpec["variant"], hovered: boolean) {
  if (variant === "terminal") return hovered ? "#ffcf7a" : "rgba(255,138,42,0.7)";
  if (variant === "side") return hovered ? "#4bb8ff" : "rgba(75,184,255,0.4)";
  return hovered ? "rgba(255,138,42,0.8)" : "rgba(255,255,255,0.12)";
}

export function GraphSection() {
  const shouldReduceMotion = useReducedMotion();
  const svgRef = useRef<SVGSVGElement>(null);
  const inView = useInView(svgRef, { once: true, amount: 0.15 });
  const [hovered, setHovered] = useState<string | null>(null);
  const active = inView && !shouldReduceMotion;

  const hoveredNode = nodes.find((n) => n.id === hovered) ?? null;

  // Clamp the detail tooltip so it stays inside the viewBox, and flip it above
  // the node when the node sits near the bottom of the diagram.
  let tipX = 0;
  let tipY = 0;
  if (hoveredNode) {
    tipX = Math.min(Math.max(hoveredNode.x - TIP_W / 2, 12), VIEW_W - 12 - TIP_W);
    tipY =
      hoveredNode.y > 980
        ? hoveredNode.y - H / 2 - TIP_H - 12
        : hoveredNode.y + H / 2 + 12;
  }

  return (
    <section
      id="how-it-thinks"
      className="relative overflow-hidden bg-surface py-16 sm:py-24"
    >
      <GridBackground variant="dots" aurora />

      <div className="relative mx-auto max-w-[1280px] px-6 sm:px-8">
        <span className="inline-flex items-center gap-2 font-mono text-[11px] font-semibold uppercase tracking-[1px] text-primary">
          <span className="h-px w-6 bg-gradient-to-r from-transparent to-primary" />
          How it actually thinks
        </span>
        <h2 className="font-display mt-3 max-w-2xl text-[32px] leading-[1.15] tracking-[-0.5px] text-ink sm:text-[40px]">
          A state machine grading real answers, not a chatbot guessing what to
          say next.
        </h2>
        <p className="mt-4 max-w-2xl text-[17px] leading-[1.55] text-slate">
          This is the actual LangGraph running the tutoring session: every phase
          is a node, every transition is a conditional edge reading structured
          output, and the LLM never chooses its own next step. Hover any node to
          see what it really does. Scroll to watch the graph come alive.
        </p>

        <div className="mt-12 overflow-x-auto">
          <svg
            ref={svgRef}
            viewBox="0 0 640 1220"
            className="mx-auto w-full max-w-[680px]"
            role="img"
            aria-label="LangGraph state machine diagram from INTRO to COMPLETE, including the comprehension and hint/coding/execution loops"
          >
            <defs>
              <linearGradient id="grad-spine" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#17171d" />
                <stop offset="100%" stopColor="#0f0f13" />
              </linearGradient>
              <linearGradient id="grad-spine-hot" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#3a1c0d" />
                <stop offset="100%" stopColor="#241009" />
              </linearGradient>
              <linearGradient id="grad-side" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#101820" />
                <stop offset="100%" stopColor="#0c1116" />
              </linearGradient>
              <linearGradient id="grad-side-hot" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#0e2733" />
                <stop offset="100%" stopColor="#0b1a22" />
              </linearGradient>
              <linearGradient id="grad-terminal" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#fa520f" />
                <stop offset="100%" stopColor="#ff8a2a" />
              </linearGradient>
              <linearGradient id="grad-edge" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#ff8a2a" />
                <stop offset="100%" stopColor="#ffb03e" />
              </linearGradient>
              <linearGradient id="grad-branch" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#2fd6c3" />
                <stop offset="100%" stopColor="#4bb8ff" />
              </linearGradient>
              <filter id="glow" x="-60%" y="-60%" width="220%" height="220%">
                <feGaussianBlur stdDeviation="6" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            {/* Edges: a faint base rail, an animated flowing overlay, and a
                traveling signal particle when the graph is in view. */}
            {edges.map((edge, i) => {
              const stroke = edge.branch ? "url(#grad-branch)" : "url(#grad-edge)";
              return (
                <g key={edge.id}>
                  <path
                    id={edge.id}
                    d={edge.d}
                    fill="none"
                    stroke="rgba(255,255,255,0.09)"
                    strokeWidth={2}
                  />
                  <motion.path
                    d={edge.d}
                    fill="none"
                    stroke={stroke}
                    strokeWidth={2}
                    strokeLinecap="round"
                    className={active ? "edge-flow" : undefined}
                    strokeDasharray="5 23"
                    initial={
                      shouldReduceMotion
                        ? { pathLength: 1, opacity: 0.9 }
                        : { pathLength: 0, opacity: 0 }
                    }
                    animate={
                      active
                        ? { pathLength: 1, opacity: 0.95 }
                        : shouldReduceMotion
                          ? { pathLength: 1, opacity: 0.9 }
                          : { pathLength: 0, opacity: 0 }
                    }
                    transition={{
                      duration: shouldReduceMotion ? 0 : 0.5,
                      delay: shouldReduceMotion ? 0 : i * 0.1,
                      ease: "easeInOut",
                    }}
                  />
                  {active ? (
                    <circle
                      r={3}
                      fill={edge.branch ? "#4bb8ff" : "#ffb03e"}
                      opacity={0.9}
                    >
                      <animateMotion
                        dur={`${2.6 + (i % 4) * 0.5}s`}
                        begin={`${i * 0.18}s`}
                        repeatCount="indefinite"
                        rotate="auto"
                      >
                        <mpath href={`#${edge.id}`} />
                      </animateMotion>
                    </circle>
                  ) : null}
                  {edge.label ? (
                    <motion.text
                      x={edge.labelX}
                      y={edge.labelY}
                      fontSize="11"
                      fill="var(--color-steel)"
                      fontFamily="var(--font-sans)"
                      initial={shouldReduceMotion ? { opacity: 1 } : { opacity: 0 }}
                      animate={active || shouldReduceMotion ? { opacity: 1 } : { opacity: 0 }}
                      transition={{
                        duration: shouldReduceMotion ? 0 : 0.25,
                        delay: shouldReduceMotion ? 0 : i * 0.1 + 0.3,
                      }}
                    >
                      {edge.label}
                    </motion.text>
                  ) : null}
                </g>
              );
            })}

            {/* Nodes: staggered reveal, glow + scale on hover, keyboard focus. */}
            {nodes.map((node, i) => {
              const isHovered = hovered === node.id;
              return (
                <motion.g
                  key={node.id}
                  tabIndex={0}
                  role="button"
                  aria-label={`${node.label}: ${node.kind}. ${node.caption}`}
                  onMouseEnter={() => setHovered(node.id)}
                  onMouseLeave={() => setHovered((h) => (h === node.id ? null : h))}
                  onFocus={() => setHovered(node.id)}
                  onBlur={() => setHovered((h) => (h === node.id ? null : h))}
                  className="cursor-pointer outline-none"
                  initial={
                    shouldReduceMotion ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.92 }
                  }
                  animate={
                    active
                      ? { opacity: 1, scale: 1 }
                      : shouldReduceMotion
                        ? { opacity: 1, scale: 1 }
                        : { opacity: 0, scale: 0.92 }
                  }
                  whileHover={shouldReduceMotion ? undefined : { scale: 1.04 }}
                  transition={{
                    duration: shouldReduceMotion ? 0 : 0.35,
                    delay: shouldReduceMotion ? 0 : i * 0.12 + 0.15,
                    ease: "easeOut",
                  }}
                  style={{ transformOrigin: `${node.x}px ${node.y}px` }}
                  filter={isHovered ? "url(#glow)" : undefined}
                >
                  <rect
                    x={node.x - W / 2}
                    y={node.y - H / 2}
                    width={W}
                    height={H}
                    rx={node.variant === "side" ? 14 : 10}
                    fill={nodeFill(node.variant, isHovered)}
                    stroke={nodeStroke(node.variant, isHovered)}
                    strokeWidth={isHovered ? 1.5 : 1}
                  />
                  <text
                    x={node.x}
                    y={node.y + 4}
                    textAnchor="middle"
                    fontSize="11"
                    fontWeight={600}
                    fontFamily="var(--font-mono)"
                    fill={node.variant === "terminal" ? "#1a0d04" : "#f5f5f7"}
                  >
                    {node.label}
                  </text>
                </motion.g>
              );
            })}

            {/* Hover / focus detail panel, in SVG space so it scales with the
                diagram. Content differs per node (kind + real caption). */}
            {hoveredNode ? (
              <foreignObject
                x={tipX}
                y={tipY}
                width={TIP_W}
                height={TIP_H}
                style={{ overflow: "visible", pointerEvents: "none" }}
              >
                <div className="glow-border rounded-lg border border-hairline-strong bg-surface-3/95 p-3.5 shadow-[0_16px_40px_-12px_rgba(0,0,0,0.8)] backdrop-blur">
                  <p className="font-mono text-[10px] font-semibold uppercase tracking-wide text-primary">
                    {hoveredNode.kind}
                  </p>
                  <p className="mt-1 font-mono text-[11px] font-semibold text-ink">
                    {hoveredNode.label}
                  </p>
                  <p className="mt-1.5 text-[11px] leading-[1.45] text-slate">
                    {hoveredNode.caption}
                  </p>
                </div>
              </foreignObject>
            ) : null}
          </svg>
        </div>

        {/* Legend for the two edge tones. */}
        <div className="mt-8 flex flex-wrap justify-center gap-6 font-mono text-[11px] text-steel">
          <span className="inline-flex items-center gap-2">
            <span className="h-2 w-6 rounded-full" style={{ background: "linear-gradient(90deg,#ff8a2a,#ffb03e)" }} />
            forward transition
          </span>
          <span className="inline-flex items-center gap-2">
            <span className="h-2 w-6 rounded-full" style={{ background: "linear-gradient(90deg,#2fd6c3,#4bb8ff)" }} />
            loop / branch back
          </span>
        </div>

        {/* Captions rendered as accessible text alongside the diagram, in graph
            order, so the "what really happens here" content is available
            without relying on hover/tooltips inside the SVG. */}
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
              className="group flex gap-3 rounded-lg border border-transparent p-2 transition-colors hover:border-hairline-soft hover:bg-white/[0.02]"
            >
              <span className="mt-0.5 font-mono text-xs font-semibold text-primary">
                {String(i + 1).padStart(2, "0")}
              </span>
              <div>
                <p className="font-mono text-xs font-semibold text-ink">
                  {node.label}
                  <span className="ml-2 font-sans font-normal text-steel">
                    {node.kind}
                  </span>
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
