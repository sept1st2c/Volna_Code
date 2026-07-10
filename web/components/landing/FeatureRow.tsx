import { Reveal } from "./Reveal";
import { SpotlightCard } from "./SpotlightCard";

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
  return (
    <section className="mx-auto max-w-[1280px] px-6 py-16 sm:px-8 sm:py-24">
      <div className="grid gap-6 md:grid-cols-3">
        {features.map((feature, i) => (
          <Reveal key={feature.title} delay={i * 0.08} className="h-full">
            <SpotlightCard className="group/card h-full rounded-xl border border-hairline-soft bg-white/[0.015] p-8">
              <div className="flex items-baseline gap-3">
                <span className="font-mono text-[13px] text-stone transition-colors duration-300 group-hover/card:text-primary">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <span className="h-px flex-1 bg-hairline-soft transition-colors duration-300 group-hover/card:bg-primary/40" />
                {i < features.length - 1 && (
                  <span className="font-mono text-[10px] uppercase tracking-wide text-stone/70">
                    next
                  </span>
                )}
              </div>
              <h3 className="mt-6 text-[22px] font-medium leading-[1.3] text-ink">
                {feature.title}
              </h3>
              <p className="mt-3 text-[16px] leading-[1.55] text-slate">
                {feature.body}
              </p>
            </SpotlightCard>
          </Reveal>
        ))}
      </div>
    </section>
  );
}
