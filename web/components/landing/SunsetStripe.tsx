/**
 * sunset-stripe-band: mandatory brand-closing element per DESIGN-mistral.ai.md
 * ("the brand's most recognizable signature ... never omit from any page
 * bottom"). Purely decorative, no content. Restyled for the dark theme as a
 * glowing ember signature bar rather than the original cream-tailed gradient.
 */
export function SunsetStripe() {
  return (
    <div role="presentation" className="relative h-10 w-full bg-footer-cream">
      {/* Soft ember glow rising off the bar. */}
      <div
        aria-hidden
        className="absolute inset-x-0 bottom-0 h-16"
        style={{
          background:
            "linear-gradient(to top, rgba(250,82,15,0.35) 0%, transparent 100%)",
        }}
      />
      <div
        aria-hidden
        className="absolute inset-x-0 bottom-0 h-1.5"
        style={{
          background:
            "linear-gradient(90deg, #fa520f 0%, #ff7a1a 32%, #ffb03e 60%, #ffd06a 82%, #ff7a1a 100%)",
        }}
      />
    </div>
  );
}
