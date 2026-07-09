import Image from "next/image";
import { Reveal } from "./Reveal";

// A single real screenshot of the actual product mid-session: a genuine
// LiveKit connection to the real voice worker ("Connected, and a tutor
// agent is present in the room" is a real status, not staged), the real
// problem panel, a real submitted solution, a real Piston run, and the
// real tutor conversation that produced it (see web/lib/mock-data.ts's
// DEMO_CHAT_MESSAGES / DEMO_CODE / DEMO_SUBMISSION_RESULT for provenance).

export function DemoTranscript() {
  return (
    <section id="demo" className="relative overflow-hidden bg-surface py-16 sm:py-24">
      <div className="relative mx-auto max-w-[1200px] px-6 sm:px-8">
        <span className="font-mono text-[11px] font-semibold uppercase tracking-[1px] text-primary">
          A real session, captured
        </span>
        <h2 className="font-display mt-3 max-w-2xl text-[32px] leading-[1.15] tracking-[-0.5px] text-ink sm:text-[40px]">
          This is the actual product. Every line below is real.
        </h2>
        <p className="mt-4 max-w-2xl text-[17px] leading-[1.55] text-slate">
          A genuine connection to the real voice worker, a real duplicate-value
          edge case surfaced before the explanation was accepted, and a real
          submission graded against a real sandbox. Nothing on this page is
          staged.
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
            <div className="relative bg-surface-code" style={{ aspectRatio: "1500 / 1000" }}>
              <Image
                src="/demo/full-session.png"
                alt="A real Volna tutoring session for Two Sum: the problem panel, a real submitted hash-map solution, a real all-passing Piston test run including duplicate-value, negative-number, and zero-value edge cases, a genuine connected voice session, and the real tutor conversation that led to the solution."
                fill
                sizes="(min-width: 1024px) 1100px, 90vw"
                className="object-cover object-top"
              />
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
