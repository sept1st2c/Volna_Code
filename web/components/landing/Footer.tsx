import Link from "next/link";

const columns = [
  {
    heading: "Why Volna",
    links: [
      { href: "#how-it-thinks", label: "How it thinks" },
      { href: "#problems-we-hit", label: "Engineering notes" },
    ],
  },
  {
    heading: "Explore",
    links: [
      { href: "/problems", label: "Problem bank" },
      { href: "#demo", label: "Sample session" },
    ],
  },
  {
    heading: "Build",
    links: [
      { href: "https://groq.com", label: "Groq" },
      { href: "https://livekit.io", label: "LiveKit" },
    ],
  },
];

export function Footer() {
  return (
    <footer className="border-t border-hairline-soft bg-footer-cream px-6 py-16 text-ink sm:px-8 sm:py-[64px]">
      <div className="mx-auto grid max-w-[1280px] gap-10 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <span className="font-display text-xl text-ink">Volna</span>
          <p className="mt-3 max-w-[220px] text-sm leading-[1.5] text-steel">
            A voice AI tutor that grades your approach against an authored
            problem bank instead of guessing along with you.
          </p>
        </div>

        {columns.map((column) => (
          <div key={column.heading}>
            <p className="text-sm font-semibold text-ink">{column.heading}</p>
            <ul className="mt-4 flex flex-col gap-2">
              {column.links.map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="link-underline text-sm text-slate transition-colors hover:text-primary"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <div className="mx-auto mt-12 max-w-[1280px] border-t border-hairline-soft pt-6 text-xs text-steel">
        Built as a single-user, no-auth MVP. Not affiliated with LeetCode.
      </div>
    </footer>
  );
}
