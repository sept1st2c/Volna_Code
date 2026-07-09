import Link from "next/link";
import { Reveal } from "./Reveal";

export function ClosingCta() {
  return (
    <section className="mx-auto max-w-[1280px] px-6 pb-16 sm:px-8 sm:pb-24">
      <Reveal>
        <div className="rounded-lg bg-cream px-8 py-16 text-center text-ink sm:px-16 sm:py-[64px]">
          <h2 className="font-display mx-auto max-w-2xl text-[32px] leading-[1.15] tracking-[-0.5px] sm:text-[44px]">
            Pick a problem. Explain it back. Defend your approach.
          </h2>
          <p className="mx-auto mt-4 max-w-lg text-[17px] leading-[1.55] text-ink-tint">
            No account, no setup. Just a problem, a hint ladder you have to
            earn, and real test cases waiting to catch what you missed.
          </p>
          <div className="mt-8 flex justify-center">
            <Link
              href="/problems"
              className="rounded-md bg-ink px-6 py-3 text-sm font-medium text-on-dark"
            >
              Try it
            </Link>
          </div>
        </div>
      </Reveal>
    </section>
  );
}
