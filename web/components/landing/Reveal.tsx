"use client";

import { motion, useReducedMotion, type Variant } from "framer-motion";
import type { ReactNode } from "react";

type RevealProps = {
  children: ReactNode;
  className?: string;
  delay?: number;
  y?: number;
  as?: "div" | "li";
};

/**
 * Snappy scroll-triggered fade/rise reveal (150-250ms), used for feature
 * cards, stat tiles, and section transitions per PLAN.md's animation
 * approach. Respects prefers-reduced-motion by skipping motion entirely.
 */
export function Reveal({
  children,
  className,
  delay = 0,
  y = 12,
  as = "div",
}: RevealProps) {
  const shouldReduceMotion = useReducedMotion();

  const hidden: Variant = shouldReduceMotion
    ? { opacity: 1, y: 0 }
    : { opacity: 0, y };
  const shown: Variant = { opacity: 1, y: 0 };

  const Component = as === "li" ? motion.li : motion.div;

  return (
    <Component
      className={className}
      initial={hidden}
      whileInView={shown}
      viewport={{ once: true, amount: 0.3 }}
      transition={{
        duration: shouldReduceMotion ? 0 : 0.2,
        delay: shouldReduceMotion ? 0 : delay,
        ease: "easeOut",
      }}
    >
      {children}
    </Component>
  );
}
