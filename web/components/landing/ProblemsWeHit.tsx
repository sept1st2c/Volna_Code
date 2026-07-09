import { Reveal } from "./Reveal";
import { SpotlightCard } from "./SpotlightCard";

const items = [
  {
    title: "Piston's sandbox went whitelist-only mid-build",
    body: "The public Piston API we planned around started requiring a whitelisted key partway through the build. We're working through the access process instead of pretending it was never a problem.",
  },
  {
    title: "Near-zero-cost, on purpose",
    body: "Groq covers the model and the speech-to-text. Deepgram covers voice. LiveKit's free tier covers the room itself. The budget was $0, and the architecture had to fit that, not the other way around.",
  },
  {
    title: "The model doesn't get to invent a hint",
    body: "Every hint, every edge case, every explanation of why the brute force falls short comes from an authored problem bank. The model only judges your answer against it and narrates the verdict, it never makes one up.",
  },
];

export function ProblemsWeHit() {
  return (
    <section id="problems-we-hit" className="mx-auto max-w-[1280px] px-6 py-16 sm:px-8 sm:py-24">
      <span className="font-mono text-[11px] font-semibold uppercase tracking-[1px] text-primary">
        Problems we hit building this
      </span>
      <h2 className="font-display mt-3 max-w-2xl text-[32px] leading-[1.15] tracking-[-0.5px] text-ink sm:text-[40px]">
        The honest version, not the highlight reel.
      </h2>

      <div className="mt-10 grid gap-6 md:grid-cols-3">
        {items.map((item, i) => (
          <Reveal key={item.title} delay={i * 0.08} className="h-full">
            <SpotlightCard className="h-full rounded-xl border border-hairline-soft bg-surface-2 p-8 text-ink">
              <h3 className="text-[18px] font-medium leading-[1.4]">
                {item.title}
              </h3>
              <p className="mt-3 text-[15px] leading-[1.6] text-slate">
                {item.body}
              </p>
            </SpotlightCard>
          </Reveal>
        ))}
      </div>
    </section>
  );
}
