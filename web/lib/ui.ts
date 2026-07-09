import type { Difficulty } from "./types";

/** Tailwind classes for a difficulty pill, shared between the list and session pages. */
export function difficultyBadgeClasses(difficulty: Difficulty): string {
  const base = "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset";
  switch (difficulty.toLowerCase()) {
    case "easy":
      return `${base} bg-emerald-500/10 text-emerald-400 ring-emerald-500/20`;
    case "medium":
      return `${base} bg-amber-500/10 text-amber-400 ring-amber-500/20`;
    case "hard":
      return `${base} bg-rose-500/10 text-rose-400 ring-rose-500/20`;
    default:
      return `${base} bg-surface-3 text-ink-tint ring-hairline-strong`;
  }
}
