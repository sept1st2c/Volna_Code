import { Reveal } from "./Reveal";

// PLAN.md defers the real stat/latency row until after M7, once the voice
// pipeline is instrumented and there are honest measured numbers to show.
// Until then: qualitative badges only, no fabricated metrics.
const badges = [
  "Real sandboxed execution against test cases",
  "Hints gated until you're actually stuck",
  "Grading grounded in an authored problem bank",
  "No scraped problem text",
];

export function QualitativeBadges() {
  return (
    <section className="mx-auto max-w-[1280px] px-6 pb-16 sm:px-8 sm:pb-24">
      <Reveal>
        <ul className="flex flex-wrap justify-center gap-3">
          {badges.map((badge) => (
            <li
              key={badge}
              className="rounded-full bg-cream-deeper px-4 py-1.5 text-sm font-semibold text-ink"
            >
              {badge}
            </li>
          ))}
        </ul>
      </Reveal>
    </section>
  );
}
