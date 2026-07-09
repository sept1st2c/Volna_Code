type GridBackgroundProps = {
  /** "grid" draws ruled lines, "dots" draws a dot matrix. */
  variant?: "grid" | "dots";
  /** Render drifting ember/signal aurora glows behind the texture. */
  aurora?: boolean;
  /** Slowly pan the grid (ignored under prefers-reduced-motion). */
  animated?: boolean;
};

/**
 * Purely decorative dark-theme background texture: a masked engineering grid
 * (or dot matrix) with optional drifting aurora glows. Common on dark
 * dev-tool marketing pages (Vercel, Linear); kept very low opacity so it
 * reads as texture, not noise.
 */
export function GridBackground({
  variant = "grid",
  aurora = false,
  animated = false,
}: GridBackgroundProps) {
  const textureClass = variant === "dots" ? "bg-dots" : "bg-grid";

  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden">
      <div
        className={`absolute inset-0 mask-fade ${textureClass} ${
          animated ? "animate-grid-pan" : ""
        }`}
      />
      {aurora ? (
        <>
          <div
            className="animate-aurora absolute -left-32 -top-40 h-[520px] w-[520px] rounded-full blur-[120px]"
            style={{
              background:
                "radial-gradient(circle, rgba(250,82,15,0.5) 0%, rgba(250,82,15,0) 70%)",
            }}
          />
          <div
            className="animate-aurora absolute -right-40 top-10 h-[480px] w-[480px] rounded-full blur-[130px]"
            style={{
              animationDelay: "-6s",
              background:
                "radial-gradient(circle, rgba(75,184,255,0.28) 0%, rgba(75,184,255,0) 70%)",
            }}
          />
        </>
      ) : null}
    </div>
  );
}
