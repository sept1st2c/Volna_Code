import { Reveal } from "./Reveal";

const codeLines: { text: string; tone?: "comment" | "keyword" | "string" | "plain" }[] = [
  { text: "# problems/two_sum.py: authored, not scraped from LeetCode", tone: "comment" },
  { text: "hint_ladder = [", tone: "plain" },
  { text: "    Hint(level=1, text=(", tone: "plain" },
  { text: '        "What if you didn\'t have to re-scan the array "', tone: "string" },
  { text: '        "for every number?"', tone: "string" },
  { text: "    )),", tone: "plain" },
  { text: "    Hint(level=2, text=(", tone: "plain" },
  { text: '        "A hash map turns \'have I seen this value before\' "', tone: "string" },
  { text: '        "into an O(1) lookup."', tone: "string" },
  { text: "    )),", tone: "plain" },
  { text: "]", tone: "plain" },
  { text: "", tone: "plain" },
  { text: "GRADE_PROMPT = (", tone: "keyword" },
  { text: '    "Grade solely using the context below. "', tone: "string" },
  { text: '    "Ignore your own memorized knowledge of this problem."', tone: "string" },
  { text: ")", tone: "keyword" },
];

const toneClass: Record<string, string> = {
  comment: "text-on-dark-muted",
  keyword: "text-[#ff9d4d]",
  string: "text-[#7ee0c3]",
  plain: "text-ink-tint",
};

export function CodeShowcase() {
  return (
    <section className="mx-auto max-w-[1280px] px-6 py-16 sm:px-8 sm:py-24">
      <div className="grid gap-10 lg:grid-cols-[0.9fr_1.1fr] lg:items-center">
        <div>
          <span className="font-mono text-[11px] font-semibold uppercase tracking-[1px] text-primary">
            Authored, not improvised
          </span>
          <h2 className="font-display mt-3 text-[32px] leading-[1.15] tracking-[-0.5px] text-ink sm:text-[40px]">
            The hint ladder is a file, not a guess.
          </h2>
          <p className="mt-4 max-w-md text-[17px] leading-[1.55] text-slate">
            Every hint the tutor delivers is written ahead of time by us and
            pulled verbatim. The grading prompt explicitly tells the model to
            ignore its own memorized version of the problem and judge only
            against what&apos;s in the file.
          </p>
        </div>

        <Reveal>
          <div className="glow-border overflow-hidden rounded-xl border border-hairline-soft shadow-[0_24px_60px_-20px_rgba(0,0,0,0.8)]">
            <div className="flex items-center gap-2 border-b border-hairline-soft bg-surface-2 px-4 py-3">
              <span className="h-3 w-3 rounded-full bg-[#ff5f57]" />
              <span className="h-3 w-3 rounded-full bg-[#febc2e]" />
              <span className="h-3 w-3 rounded-full bg-[#28c840]" />
              <span className="ml-3 font-mono text-xs text-on-dark-muted">
                problems/two_sum.py
              </span>
            </div>
            <pre className="overflow-x-auto bg-surface-code px-5 py-5 font-mono text-[13px] leading-[1.6]">
              <code>
                {codeLines.map((line, i) => (
                  <div key={i} className={toneClass[line.tone ?? "plain"]}>
                    {line.text || " "}
                  </div>
                ))}
              </code>
            </pre>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
