import Link from "next/link";

export function Hero() {
  return (
    <section
      id="top"
      className="relative overflow-hidden"
      style={{
        background:
          "linear-gradient(135deg, var(--color-sunshine-700) 0%, var(--color-sunshine-900) 60%, var(--color-primary) 100%)",
      }}
    >
      {/* Atmospheric sunset glow standing in for hero photography, per the
          design doc's allowance for "atmospheric gradient sky" as a substitute
          for mountain photography. */}
      <div
        aria-hidden
        className="pointer-events-none absolute -right-40 top-1/2 h-[520px] w-[520px] -translate-y-1/2 rounded-full opacity-70 blur-3xl"
        style={{
          background:
            "radial-gradient(circle, var(--color-yellow-saturated) 0%, transparent 70%)",
        }}
      />

      <div className="relative mx-auto grid max-w-[1280px] gap-12 px-6 py-24 sm:px-8 sm:py-32 lg:grid-cols-[1.1fr_0.9fr] lg:items-center lg:py-[120px]">
        <div>
          <span className="inline-flex rounded-full bg-ink px-3 py-1 text-xs font-semibold uppercase tracking-wider text-on-dark">
            Voice AI DSA tutor
          </span>

          <h1 className="font-display mt-6 text-[40px] leading-[1.05] tracking-[-0.5px] text-ink sm:text-[52px] lg:text-[64px] xl:text-[84px] xl:tracking-[-1.5px]">
            Your DSA tutor that never skips to the answer.
          </h1>

          <p className="mt-6 max-w-xl text-lg leading-[1.5] text-ink-tint">
            Explain the problem back. Defend your approach out loud. Watch
            real test cases catch what you missed. Then do it again, better.
          </p>

          <div className="mt-10 flex flex-wrap items-center gap-4">
            <Link
              href="/problems"
              className="rounded-md bg-ink px-5 py-2.5 text-sm font-medium text-on-dark"
            >
              Try it
            </Link>
            <a
              href="#how-it-thinks"
              className="rounded-md border border-hairline-strong px-5 py-2.5 text-sm font-medium text-ink"
            >
              See how it thinks
            </a>
          </div>
        </div>

        <div className="hidden lg:block" aria-hidden>
          <div className="ml-auto h-[360px] w-full max-w-[420px] rounded-lg border border-white/20 bg-white/10 backdrop-blur-sm" />
        </div>
      </div>
    </section>
  );
}
