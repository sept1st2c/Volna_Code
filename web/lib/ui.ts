import type { Difficulty } from "./types";

/** Tailwind classes for a difficulty pill, shared between the list and session pages. */
export function difficultyBadgeClasses(difficulty: Difficulty): string {
  const base = "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset";
  switch (difficulty.toLowerCase()) {
    case "easy":
      return `${base} bg-emerald-50 text-emerald-700 ring-emerald-600/20 dark:bg-emerald-500/10 dark:text-emerald-400 dark:ring-emerald-500/20`;
    case "medium":
      return `${base} bg-amber-50 text-amber-700 ring-amber-600/20 dark:bg-amber-500/10 dark:text-amber-400 dark:ring-amber-500/20`;
    case "hard":
      return `${base} bg-rose-50 text-rose-700 ring-rose-600/20 dark:bg-rose-500/10 dark:text-rose-400 dark:ring-rose-500/20`;
    default:
      return `${base} bg-slate-100 text-slate-700 ring-slate-600/20 dark:bg-slate-500/10 dark:text-slate-300 dark:ring-slate-500/20`;
  }
}
