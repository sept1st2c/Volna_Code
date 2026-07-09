import Image from "next/image";
import { Reveal } from "./Reveal";

// Real screenshots of the real product (see web/lib/mock-data.ts's
// DEMO_CHAT_MESSAGES / DEMO_CODE / DEMO_SUBMISSION_RESULT for provenance):
// every tutor line is actual output from the live LangGraph brain running
// against the real Groq API for the two-sum problem, the code is what was
// actually submitted, and the test results are a real subset of the real
// 75-case Piston run against it. Nothing here is staged copy.

export function DemoTranscript() {
  return (
    <section id="demo" className="relative overflow-hidden bg-surface py-16 sm:py-24">
      <div className="relative mx-auto max-w-[1100px] px-6 sm:px-8">
        <span className="font-mono text-[11px] font-semibold uppercase tracking-[1px] text-primary">
          A real session, captured
        </span>
        <h2 className="font-display mt-3 max-w-2xl text-[32px] leading-[1.15] tracking-[-0.5px] text-ink sm:text-[40px]">
          This actually happened. Every line below is real.
        </h2>
        <p className="mt-4 max-w-2xl text-[17px] leading-[1.55] text-slate">
          The tutor caught a duplicate-value edge case before accepting the explanation,
          held the line on brute force before handing out a hint, and graded a real
          submission against a real sandbox. Nothing on this page is scripted.
        </p>

        <Reveal>
          <div className="glow-border mt-10 overflow-hidden rounded-xl border border-hairline-soft shadow-[0_24px_60px_-20px_rgba(0,0,0,0.8)]">
            <div className="flex items-center gap-2 border-b border-hairline-soft bg-surface-2 px-4 py-3">
              <span className="h-3 w-3 rounded-full bg-[#ff5f57]" />
              <span className="h-3 w-3 rounded-full bg-[#febc2e]" />
              <span className="h-3 w-3 rounded-full bg-[#28c840]" />
              <span className="ml-3 font-mono text-xs text-on-dark-muted">
                volna &middot; tutor/two-sum
              </span>
            </div>

            <div className="grid grid-cols-1 gap-px bg-hairline-soft sm:grid-cols-[1.1fr_1fr]">
              <div className="relative bg-surface-code" style={{ aspectRatio: "1000 / 1200" }}>
                <Image
                  src="/demo/chat.png"
                  alt="Real tutor conversation transcript for the Two Sum problem, showing the tutor surfacing a duplicate-values edge case, grading a brute-force description, delivering a hint, and confirming a correct optimal approach."
                  fill
                  sizes="(min-width: 640px) 45vw, 90vw"
                  className="object-cover object-top"
                />
              </div>
              <div className="flex flex-col gap-px bg-hairline-soft">
                <div className="relative bg-surface-code" style={{ aspectRatio: "1000 / 840" }}>
                  <Image
                    src="/demo/code.png"
                    alt="The real Python solution submitted during the session, using a hash map for an O(n) Two Sum solution."
                    fill
                    sizes="(min-width: 640px) 40vw, 90vw"
                    className="object-cover object-top"
                  />
                </div>
                <div className="relative bg-surface-code" style={{ aspectRatio: "1000 / 574" }}>
                  <Image
                    src="/demo/results.png"
                    alt="Real test results panel showing all cases passed, including duplicate-value, negative-number, zero-value, and minimal-size edge cases."
                    fill
                    sizes="(min-width: 640px) 40vw, 90vw"
                    className="object-cover object-top"
                  />
                </div>
              </div>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
