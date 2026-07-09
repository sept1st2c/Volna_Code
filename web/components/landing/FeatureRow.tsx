import { Reveal } from "./Reveal";

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
    <section className="mx-auto max-w-[880px] px-6 py-16 sm:px-8 sm:py-24">
      <div className="feature-list flex flex-col gap-3">
        {features.map((feature, i) => (
          <Reveal key={feature.title} delay={i * 0.08}>
            <div
              tabIndex={0}
              className="feature-row group rounded-xl border border-hairline-soft bg-surface-2 px-7 py-6 outline-none transition-[colors,opacity] duration-300 hover:border-primary/30 focus-visible:border-primary/30 focus-visible:ring-2 focus-visible:ring-primary/40"
            >
              <div className="flex items-baseline gap-4">
                <span className="font-mono text-[13px] text-stone transition-colors duration-300 group-hover:text-primary">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <h3 className="text-[22px] font-medium leading-[1.3] text-ink">
                  {feature.title}
                </h3>
              </div>

              <div className="grid grid-rows-[0fr] transition-[grid-template-rows] duration-300 ease-out group-hover:grid-rows-[1fr] group-focus-within:grid-rows-[1fr]">
                <div className="overflow-hidden">
                  <p className="ml-[calc(13px+1rem)] max-w-[600px] pt-3 text-[16px] leading-[1.55] text-slate opacity-0 transition-opacity duration-300 group-hover:opacity-100 group-focus-within:opacity-100">
                    {feature.body}
                  </p>
                </div>
              </div>
            </div>
          </Reveal>
        ))}
      </div>
    </section>
  );
}
