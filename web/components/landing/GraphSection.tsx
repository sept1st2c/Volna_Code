"use client";

import { useEffect, useRef, useState } from "react";
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

type Pt = { x: number; y: number };

type EdgeShape = "auto" | "arc-up" | "arc-down" | "self" | "back";

type EdgeSpec = {
  id: string;
  from: string;
  to: string;
  shape: EdgeShape;
  label?: string;
  // Loop/branch edges get the cool signal treatment rather than the ember spine.
  branch?: boolean;
  // Per-edge tuning for label placement and the long back curves.
  labelDx?: number;
  labelDy?: number;
  spread?: number;
  startDy?: number;
  // "auto" shape only: how far, and to which side, the curve bows away from
  // a straight line between the two nodes. Negative/positive picks the side.
  bow?: number;
};

const W = 200;
const H = 56;
const HALF_W = W / 2;
const HALF_H = H / 2;
const VB_W = 1180;
const VB_H = 680;

const clamp = (v: number, min: number, max: number) =>
  Math.min(Math.max(v, min), max);

// Node layout mirrors the Core State Machine mermaid diagram in PLAN.md:
// INTRO through COMPLETE, including the comprehension loop (CHECK <->
// REMEDIATION) and the iteration loop (FEEDBACK -> ITERATION -> CODING /
// HINT_LADDER). Captions describe what each node really does.
// Positions are scattered across a wide canvas rather than following
// reading order top-to-bottom -- this is meant to read as a real graph
// diagram (a web of nodes and connectors), not a flowchart. The numbered
// caption list below the diagram is what carries the "read this in
// sequence" job, so the diagram itself is free to just be a diagram.
const nodes: NodeSpec[] = [
  { id: "INTRO", label: "INTRO", kind: "Entry node", x: 150, y: 340, variant: "spine", caption: "Introduces the problem in our own wording. Nothing here is scraped LeetCode text." },
  { id: "COMPREHENSION_CHECK", label: "COMPREHENSION_CHECK", kind: "LLM-graded gate", x: 430, y: 130, variant: "spine", caption: "Grades your explanation against the problem's real edge cases, not vibes." },
  { id: "COMPREHENSION_REMEDIATION", label: "COMPREHENSION_REMEDIATION", kind: "Remediation loop", x: 700, y: 130, variant: "side", caption: "Surfaces one authored loophole at a time until you actually see it, then sends you back to explain again." },
  { id: "APPROACH_DISCUSSION", label: "APPROACH_DISCUSSION", kind: "Discussion node", x: 960, y: 230, variant: "spine", caption: "You describe an approach out loud before a single line of code gets written." },
  { id: "BRUTE_FORCE_ANALYSIS", label: "BRUTE_FORCE_ANALYSIS", kind: "LLM-graded gate", x: 1000, y: 420, variant: "spine", caption: "Grades your brute force against an authored 'why it's insufficient,' never an improvised excuse." },
  { id: "HINT_LADDER", label: "HINT_LADDER", kind: "Authored hint ladder", x: 700, y: 480, variant: "spine", caption: "Hints are pulled verbatim from an authored ladder. The model only decides when you've earned the next level." },
  { id: "CODING", label: "CODING", kind: "Editor node", x: 430, y: 460, variant: "spine", caption: "You write real code in the editor while the tutor asks why, referencing your actual diff." },
  { id: "EXECUTING", label: "EXECUTING", kind: "Sandbox call (Piston)", x: 150, y: 520, variant: "spine", caption: "Your code runs in a real sandbox against real test cases. Nothing here is simulated." },
  { id: "FEEDBACK", label: "FEEDBACK", kind: "Verdict narration", x: 280, y: 620, variant: "spine", caption: "Narrates Piston's actual result. It explains a verdict, it never invents one." },
  { id: "ITERATION", label: "ITERATION", kind: "Iteration router", x: 780, y: 600, variant: "side", caption: "Failed a test? Back to coding for another pass. A separate route back to the hint ladder for 'still fundamentally stuck' isn't wired yet, so it always retries through coding for now." },
  { id: "COMPLETE", label: "COMPLETE", kind: "Terminal node", x: 1000, y: 600, variant: "terminal", caption: "All test cases pass against the real sandbox. Done, for real this time." },
];

const edges: EdgeSpec[] = [
  { id: "e-intro-check", from: "INTRO", to: "COMPREHENSION_CHECK", shape: "auto", bow: -40 },
  { id: "e-check-approach", from: "COMPREHENSION_CHECK", to: "APPROACH_DISCUSSION", shape: "auto", bow: 34, label: "ready to advance", labelDy: -10 },
  { id: "e-approach-brute", from: "APPROACH_DISCUSSION", to: "BRUTE_FORCE_ANALYSIS", shape: "auto", bow: -28, label: "brute force described", labelDy: -10 },
  { id: "e-brute-hint", from: "BRUTE_FORCE_ANALYSIS", to: "HINT_LADDER", shape: "auto", bow: 30 },
  { id: "e-hint-coding", from: "HINT_LADDER", to: "CODING", shape: "auto", bow: -34, label: "optimal approach found", labelDx: -46, labelDy: 4 },
  { id: "e-coding-exec", from: "CODING", to: "EXECUTING", shape: "auto", bow: 44, label: "submit via data channel", labelDx: -30, labelDy: -22 },
  { id: "e-exec-feedback", from: "EXECUTING", to: "FEEDBACK", shape: "auto", bow: -28 },
  { id: "e-feedback-complete", from: "FEEDBACK", to: "COMPLETE", shape: "auto", bow: 60, label: "all tests pass", labelDy: -12 },
  { id: "e-check-remediation", from: "COMPREHENSION_CHECK", to: "COMPREHENSION_REMEDIATION", shape: "arc-up", branch: true, label: "gaps found", labelDx: 10, labelDy: -10 },
  { id: "e-remediation-check", from: "COMPREHENSION_REMEDIATION", to: "COMPREHENSION_CHECK", shape: "arc-down", branch: true },
  { id: "e-hint-self", from: "HINT_LADDER", to: "HINT_LADDER", shape: "self", branch: true, label: "stuck 2+ turns" },
  { id: "e-feedback-iteration", from: "FEEDBACK", to: "ITERATION", shape: "arc-up", branch: true, spread: 46, label: "tests failed", labelDx: 4, labelDy: -18 },
  { id: "e-iteration-coding", from: "ITERATION", to: "CODING", shape: "back", branch: true, spread: 90, startDy: -14 },
];

const VIEW_W = VB_W;
const TIP_W = 250;
const TIP_H = 128;

type BuiltEdge = {
  d: string;
  lx: number;
  ly: number;
  anchor: "start" | "middle";
};

// Where a ray from a box's centre toward some direction exits the box's
// rectangular boundary -- used so edges leave/enter from whichever side
// actually faces the other node, instead of assuming a fixed layout.
function rectExit(cx: number, cy: number, dirX: number, dirY: number): Pt {
  if (dirX === 0 && dirY === 0) return { x: cx, y: cy };
  const tx = dirX !== 0 ? HALF_W / Math.abs(dirX) : Infinity;
  const ty = dirY !== 0 ? HALF_H / Math.abs(dirY) : Infinity;
  const t = Math.min(tx, ty);
  return { x: cx + t * dirX, y: cy + t * dirY };
}

// Every edge is derived from live node centres so the paths follow a node the
// moment it is dragged. Curves are smooth cubic/quadratic beziers with soft
// control handles, so nothing reads as a hard mechanical elbow.
function buildEdge(edge: EdgeSpec, pos: Record<string, Pt>): BuiltEdge {
  const a = pos[edge.from];
  const b = pos[edge.to];

  switch (edge.shape) {
    case "auto": {
      // Nodes are scattered rather than stacked, so the exit/entry side is
      // derived from the actual direction between the two centres (works
      // for horizontal, vertical, or diagonal pairs alike), and the curve
      // bows gently away from the straight line rather than running dead
      // straight -- a hand-drawn feel instead of a wiring diagram.
      const dx = b.x - a.x;
      const dy = b.y - a.y;
      const len = Math.hypot(dx, dy) || 1;
      const ux = dx / len;
      const uy = dy / len;
      const s = rectExit(a.x, a.y, ux, uy);
      const e = rectExit(b.x, b.y, -ux, -uy);
      const mx = (s.x + e.x) / 2;
      const my = (s.y + e.y) / 2;
      const bow = edge.bow ?? 24;
      // perpendicular to the s->e direction
      const px = -uy;
      const py = ux;
      const cx = mx + px * bow;
      const cy = my + py * bow;
      return {
        d: `M ${s.x},${s.y} Q ${cx},${cy} ${e.x},${e.y}`,
        lx: cx + (edge.labelDx ?? 0),
        ly: cy + (edge.labelDy ?? 0),
        anchor: "middle",
      };
    }
    case "arc-up": {
      const nudge = 14;
      const bow = edge.spread ?? 26;
      const s = { x: a.x + HALF_W, y: a.y - nudge };
      const e = { x: b.x - HALF_W, y: b.y - nudge };
      const mx = (s.x + e.x) / 2;
      const my = (s.y + e.y) / 2 - bow;
      return {
        d: `M ${s.x},${s.y} Q ${mx},${my} ${e.x},${e.y}`,
        lx: mx + (edge.labelDx ?? 0),
        ly: my + (edge.labelDy ?? 0),
        anchor: "middle",
      };
    }
    case "arc-down": {
      const nudge = 14;
      const bow = 26;
      const s = { x: a.x - HALF_W, y: a.y + nudge };
      const e = { x: b.x + HALF_W, y: b.y + nudge };
      const mx = (s.x + e.x) / 2;
      const my = (s.y + e.y) / 2 + bow;
      return {
        d: `M ${s.x},${s.y} Q ${mx},${my} ${e.x},${e.y}`,
        lx: mx,
        ly: my,
        anchor: "middle",
      };
    }
    case "self": {
      const x = a.x + HALF_W;
      return {
        d: `M ${x},${a.y - 12} C ${x + 76},${a.y - 44} ${x + 76},${a.y + 44} ${x},${a.y + 12}`,
        lx: x + 82,
        ly: a.y + 4,
        anchor: "start",
      };
    }
    case "back": {
      const spread = edge.spread ?? 120;
      const sdy = edge.startDy ?? 0;
      const s = { x: a.x - HALF_W, y: a.y + sdy };
      const e = { x: b.x + HALF_W, y: b.y };
      const c1 = { x: a.x + spread, y: a.y + sdy };
      const c2 = { x: b.x + HALF_W + spread, y: b.y };
      return {
        d: `M ${s.x},${s.y} C ${c1.x},${c1.y} ${c2.x},${c2.y} ${e.x},${e.y}`,
        lx: (s.x + e.x) / 2 + (edge.labelDx ?? 0),
        ly: (s.y + e.y) / 2 + (edge.labelDy ?? 0),
        anchor: "middle",
      };
    }
  }
}

function baseFill(variant: NodeSpec["variant"]) {
  if (variant === "terminal") return "url(#grad-terminal)";
  if (variant === "side") return "url(#grad-side)";
  return "url(#grad-spine)";
}

function hotFill(variant: NodeSpec["variant"]) {
  if (variant === "terminal") return "url(#grad-terminal-hot)";
  if (variant === "side") return "url(#grad-side-hot)";
  return "url(#grad-spine-hot)";
}

function nodeStroke(variant: NodeSpec["variant"], hot: boolean) {
  if (variant === "terminal") return hot ? "#ffcf7a" : "rgba(255,138,42,0.7)";
  if (variant === "side") return hot ? "#4bb8ff" : "rgba(75,184,255,0.4)";
  return hot ? "rgba(255,138,42,0.85)" : "rgba(255,255,255,0.12)";
}

export function GraphSection() {
  const shouldReduceMotion = useReducedMotion();
  const svgRef = useRef<SVGSVGElement>(null);
  const sectionRef = useRef<HTMLElement>(null);
  const inView = useInView(svgRef, { once: true, amount: 0.15 });
  const [hovered, setHovered] = useState<string | null>(null);
  const [dragging, setDragging] = useState<string | null>(null);
  const [positions, setPositions] = useState<Record<string, Pt>>(() =>
    Object.fromEntries(nodes.map((n) => [n.id, { x: n.x, y: n.y }])),
  );
  const active = inView && !shouldReduceMotion;

  // --- Drag state (kept in refs so pointer moves never re-render on their own) ---
  const dragRef = useRef<{ id: string; offx: number; offy: number } | null>(null);
  const dragFrame = useRef<number | null>(null);
  const dragPending = useRef<Pt | null>(null);

  // --- Cursor-reactive background spotlight (CSS vars only, no React state) ---
  const spotFrame = useRef<number | null>(null);
  const spotPending = useRef<{ x: number; y: number } | null>(null);

  useEffect(() => {
    return () => {
      if (dragFrame.current != null) cancelAnimationFrame(dragFrame.current);
      if (spotFrame.current != null) cancelAnimationFrame(spotFrame.current);
    };
  }, []);

  function clientToSvg(clientX: number, clientY: number): Pt | null {
    const svg = svgRef.current;
    if (!svg) return null;
    const pt = svg.createSVGPoint();
    pt.x = clientX;
    pt.y = clientY;
    const ctm = svg.getScreenCTM();
    if (!ctm) return null;
    const p = pt.matrixTransform(ctm.inverse());
    return { x: p.x, y: p.y };
  }

  function startDrag(e: React.PointerEvent<SVGGElement>, id: string) {
    const p = clientToSvg(e.clientX, e.clientY);
    if (!p) return;
    const c = positions[id];
    dragRef.current = { id, offx: p.x - c.x, offy: p.y - c.y };
    setDragging(id);
    setHovered(id);
    e.currentTarget.setPointerCapture?.(e.pointerId);
    e.preventDefault();
  }

  function moveDrag(e: React.PointerEvent<SVGGElement>) {
    if (!dragRef.current) return;
    const p = clientToSvg(e.clientX, e.clientY);
    if (!p) return;
    dragPending.current = p;
    // Coalesce to at most one position update per animation frame so a fast
    // pointer never triggers more setState calls than the display can paint.
    if (dragFrame.current == null) {
      dragFrame.current = requestAnimationFrame(() => {
        dragFrame.current = null;
        const drag = dragRef.current;
        const pt = dragPending.current;
        if (!drag || !pt) return;
        const nx = clamp(pt.x - drag.offx, HALF_W, VB_W - HALF_W);
        const ny = clamp(pt.y - drag.offy, HALF_H, VB_H - HALF_H);
        setPositions((prev) => {
          const cur = prev[drag.id];
          if (cur.x === nx && cur.y === ny) return prev;
          return { ...prev, [drag.id]: { x: nx, y: ny } };
        });
      });
    }
  }

  function endDrag(e: React.PointerEvent<SVGGElement>) {
    if (!dragRef.current) return;
    dragRef.current = null;
    setDragging(null);
    if (dragFrame.current != null) {
      cancelAnimationFrame(dragFrame.current);
      dragFrame.current = null;
    }
    try {
      e.currentTarget.releasePointerCapture?.(e.pointerId);
    } catch {
      /* pointer already released */
    }
  }

  function moveSpotlight(e: React.MouseEvent<HTMLElement>) {
    spotPending.current = { x: e.clientX, y: e.clientY };
    if (spotFrame.current == null) {
      spotFrame.current = requestAnimationFrame(() => {
        spotFrame.current = null;
        const el = sectionRef.current;
        const pt = spotPending.current;
        if (!el || !pt) return;
        const r = el.getBoundingClientRect();
        el.style.setProperty("--gx", `${pt.x - r.left}px`);
        el.style.setProperty("--gy", `${pt.y - r.top}px`);
      });
    }
  }

  const hoveredNode = hovered ? nodes.find((n) => n.id === hovered) ?? null : null;
  const hoveredPos = hoveredNode ? positions[hoveredNode.id] : null;

  // Clamp the detail tooltip so it stays inside the viewBox, and flip it above
  // the node when the node sits near the bottom of the diagram.
  let tipX = 0;
  let tipY = 0;
  if (hoveredNode && hoveredPos) {
    tipX = Math.min(Math.max(hoveredPos.x - TIP_W / 2, 12), VIEW_W - 12 - TIP_W);
    tipY =
      hoveredPos.y > VB_H - TIP_H - HALF_H - 24
        ? hoveredPos.y - H / 2 - TIP_H - 12
        : hoveredPos.y + H / 2 + 12;
  }

  return (
    <section
      ref={sectionRef}
      id="how-it-thinks"
      onMouseMove={moveSpotlight}
      className="group relative overflow-hidden bg-surface py-16 sm:py-24"
    >
      <GridBackground variant="dots" aurora />

      {/* Cursor-reactive ember spotlight scoped to this section. It only moves
          with the pointer (no ambient loop), so it needs no reduced-motion
          gate; opacity is driven purely by CSS hover. */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-500 group-hover:opacity-100"
        style={{
          background:
            "radial-gradient(560px circle at var(--gx, 50%) var(--gy, 30%), rgba(255,138,42,0.10), rgba(75,184,255,0.05) 40%, transparent 66%)",
        }}
      />

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
          see what it really does, drag one to rearrange the graph, and scroll to
          watch it come alive.
        </p>

        <div className="mt-12 overflow-x-auto">
          <svg
            ref={svgRef}
            viewBox="0 0 1180 680"
            className="mx-auto w-full max-w-[1180px] touch-none select-none"
            role="img"
            aria-label="Interactive LangGraph state machine diagram from INTRO to COMPLETE, including the comprehension and hint/coding/execution loops. Nodes can be dragged."
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
              <linearGradient id="grad-terminal-hot" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#ff7a1f" />
                <stop offset="100%" stopColor="#ffb45a" />
              </linearGradient>
              <linearGradient id="grad-edge" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#ff8a2a" />
                <stop offset="100%" stopColor="#ffb03e" />
              </linearGradient>
              <linearGradient id="grad-branch" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#2fd6c3" />
                <stop offset="100%" stopColor="#4bb8ff" />
              </linearGradient>
              {/* Soft-edged travelling signal dots (no hard circle rim). */}
              <radialGradient id="part-ember" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#ffe0b0" />
                <stop offset="45%" stopColor="#ffb03e" />
                <stop offset="100%" stopColor="#ffb03e" stopOpacity="0" />
              </radialGradient>
              <radialGradient id="part-signal" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#c7f0ff" />
                <stop offset="45%" stopColor="#4bb8ff" />
                <stop offset="100%" stopColor="#4bb8ff" stopOpacity="0" />
              </radialGradient>
              <filter id="glow" x="-60%" y="-60%" width="220%" height="220%">
                <feGaussianBlur stdDeviation="6" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            {/* Edges: a faint base rail, a smooth colour rail that brightens when
                a connected node is hovered, and a soft signal dot that fades in
                and out as it flows (so it never pops at the endpoints). */}
            {edges.map((edge, i) => {
              const built = buildEdge(edge, positions);
              const stroke = edge.branch ? "url(#grad-branch)" : "url(#grad-edge)";
              const connected =
                hovered != null && (edge.from === hovered || edge.to === hovered);
              const dimmed = hovered != null && !connected;
              const dur = 2.8 + (i % 3) * 0.5;
              const begin = i * 0.2;
              return (
                <g
                  key={edge.id}
                  style={{
                    opacity: dimmed ? 0.2 : 1,
                    transition: "opacity 200ms ease",
                  }}
                >
                  <path
                    id={edge.id}
                    d={built.d}
                    fill="none"
                    stroke="rgba(255,255,255,0.08)"
                    strokeWidth={2}
                    strokeLinecap="round"
                  />
                  <motion.path
                    d={built.d}
                    fill="none"
                    stroke={stroke}
                    strokeLinecap="round"
                    style={{
                      strokeWidth: connected ? 2.75 : 2,
                      transition:
                        "opacity 200ms ease, stroke-width 200ms ease",
                    }}
                    initial={
                      shouldReduceMotion
                        ? { pathLength: 1, opacity: connected ? 1 : 0.55 }
                        : { pathLength: 0, opacity: 0 }
                    }
                    animate={
                      active
                        ? { pathLength: 1, opacity: connected ? 1 : 0.55 }
                        : shouldReduceMotion
                          ? { pathLength: 1, opacity: connected ? 1 : 0.55 }
                          : { pathLength: 0, opacity: 0 }
                    }
                    transition={{
                      pathLength: {
                        duration: shouldReduceMotion ? 0 : 0.7,
                        delay: shouldReduceMotion ? 0 : i * 0.08,
                        ease: [0.22, 1, 0.36, 1],
                      },
                      opacity: { duration: 0.2 },
                    }}
                  />
                  {active ? (
                    <circle r={4.5} fill={edge.branch ? "url(#part-signal)" : "url(#part-ember)"}>
                      <animateMotion
                        dur={`${dur}s`}
                        begin={`${begin}s`}
                        repeatCount="indefinite"
                      >
                        <mpath href={`#${edge.id}`} />
                      </animateMotion>
                      <animate
                        attributeName="opacity"
                        dur={`${dur}s`}
                        begin={`${begin}s`}
                        repeatCount="indefinite"
                        values="0;1;1;0"
                        keyTimes="0;0.12;0.85;1"
                      />
                    </circle>
                  ) : null}
                  {edge.label ? (
                    <motion.text
                      x={built.lx}
                      y={built.ly}
                      textAnchor={built.anchor}
                      fontSize="11"
                      fill="var(--color-steel)"
                      fontFamily="var(--font-sans)"
                      initial={shouldReduceMotion ? { opacity: 1 } : { opacity: 0 }}
                      animate={active || shouldReduceMotion ? { opacity: 1 } : { opacity: 0 }}
                      transition={{
                        duration: shouldReduceMotion ? 0 : 0.25,
                        delay: shouldReduceMotion ? 0 : i * 0.08 + 0.3,
                      }}
                    >
                      {edge.label}
                    </motion.text>
                  ) : null}
                </g>
              );
            })}

            {/* Nodes: staggered reveal, glow + scale on hover, draggable. */}
            {nodes.map((node, i) => {
              const p = positions[node.id];
              const isHovered = hovered === node.id;
              const isDragging = dragging === node.id;
              const hot = isHovered || isDragging;
              return (
                <motion.g
                  key={node.id}
                  tabIndex={0}
                  role="button"
                  aria-label={`${node.label}: ${node.kind}. ${node.caption}`}
                  onPointerDown={(e) => startDrag(e, node.id)}
                  onPointerMove={moveDrag}
                  onPointerUp={endDrag}
                  onPointerCancel={endDrag}
                  onMouseEnter={() => setHovered(node.id)}
                  onMouseLeave={() =>
                    setHovered((h) =>
                      dragRef.current ? h : h === node.id ? null : h,
                    )
                  }
                  onFocus={() => setHovered(node.id)}
                  onBlur={() => setHovered((h) => (h === node.id ? null : h))}
                  className={`outline-none ${isDragging ? "cursor-grabbing" : "cursor-grab"}`}
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
                  whileHover={shouldReduceMotion ? undefined : { scale: 1.05 }}
                  transition={{
                    duration: shouldReduceMotion ? 0 : 0.35,
                    delay: shouldReduceMotion || isDragging ? 0 : i * 0.12 + 0.15,
                    ease: "easeOut",
                  }}
                  style={{ transformOrigin: `${p.x}px ${p.y}px` }}
                  filter={hot ? "url(#glow)" : undefined}
                >
                  <rect
                    x={p.x - W / 2}
                    y={p.y - H / 2}
                    width={W}
                    height={H}
                    rx={node.variant === "side" ? 14 : 10}
                    fill={baseFill(node.variant)}
                    stroke={nodeStroke(node.variant, hot)}
                    style={{
                      strokeWidth: hot ? 1.5 : 1,
                      transition: "stroke 200ms ease, stroke-width 200ms ease",
                    }}
                  />
                  {/* Hover glow cross-fade (gradient fills cannot be tweened, so
                      the hot variant is a separate rect faded in on top). */}
                  <rect
                    x={p.x - W / 2}
                    y={p.y - H / 2}
                    width={W}
                    height={H}
                    rx={node.variant === "side" ? 14 : 10}
                    fill={hotFill(node.variant)}
                    pointerEvents="none"
                    style={{
                      opacity: hot ? 1 : 0,
                      transition: "opacity 200ms ease",
                    }}
                  />
                  <text
                    x={p.x}
                    y={p.y + 4}
                    textAnchor="middle"
                    fontSize="11"
                    fontWeight={600}
                    fontFamily="var(--font-mono)"
                    fill={node.variant === "terminal" ? "#1a0d04" : "#f5f5f7"}
                    pointerEvents="none"
                  >
                    {node.label}
                  </text>
                </motion.g>
              );
            })}

            {/* Hover / focus detail panel, in SVG space so it scales with the
                diagram. Keyed on the node id so it re-animates in per node
                rather than popping. */}
            {hoveredNode && hoveredPos ? (
              <foreignObject
                x={tipX}
                y={tipY}
                width={TIP_W}
                height={TIP_H}
                style={{ overflow: "visible", pointerEvents: "none" }}
              >
                <motion.div
                  key={hoveredNode.id}
                  initial={
                    shouldReduceMotion
                      ? { opacity: 1, scale: 1, y: 0 }
                      : { opacity: 0, scale: 0.96, y: 6 }
                  }
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  transition={{ duration: shouldReduceMotion ? 0 : 0.18, ease: "easeOut" }}
                  className="glow-border rounded-lg border border-hairline-strong bg-surface-3/95 p-3.5 shadow-[0_16px_40px_-12px_rgba(0,0,0,0.8)] backdrop-blur"
                >
                  <p className="font-mono text-[10px] font-semibold uppercase tracking-wide text-primary">
                    {hoveredNode.kind}
                  </p>
                  <p className="mt-1 font-mono text-[11px] font-semibold text-ink">
                    {hoveredNode.label}
                  </p>
                  <p className="mt-1.5 text-[11px] leading-[1.45] text-slate">
                    {hoveredNode.caption}
                  </p>
                </motion.div>
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
              className="group/item flex gap-3 rounded-lg border border-transparent p-2 transition-colors hover:border-hairline-soft hover:bg-white/[0.02]"
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
