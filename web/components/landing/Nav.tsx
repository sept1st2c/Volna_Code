import Link from "next/link";

const links = [
  { href: "#how-it-thinks", label: "How it thinks" },
  { href: "#problems-we-hit", label: "Engineering notes" },
  { href: "#demo", label: "Demo" },
];

export function Nav() {
  return (
    <header className="sticky top-0 z-50 border-b border-hairline-soft bg-canvas/70 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-[1280px] items-center justify-between px-6 sm:px-8">
        <Link
          href="#top"
          className="font-display text-xl tracking-tight text-ink"
        >
          Volna
        </Link>

        <nav className="hidden items-center gap-8 md:flex">
          {links.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="link-underline text-sm font-medium text-steel transition-colors hover:text-ink"
            >
              {link.label}
            </a>
          ))}
        </nav>

        <Link
          href="/problems"
          className="btn-ember rounded-md px-5 py-2.5 text-sm font-semibold"
        >
          Try it
        </Link>
      </div>
    </header>
  );
}
