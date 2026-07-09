/**
 * sunset-stripe-band — mandatory brand-closing element per
 * DESIGN-mistral.ai.md ("the brand's most recognizable signature ...
 * never omit from any page bottom"). Purely decorative, no content.
 */
export function SunsetStripe() {
  return (
    <div
      role="presentation"
      className="h-10 w-full"
      style={{
        background:
          "linear-gradient(90deg, var(--color-primary) 0%, var(--color-sunshine-700) 30%, var(--color-sunshine-500) 55%, var(--color-yellow-saturated) 78%, var(--color-cream) 100%)",
      }}
    />
  );
}
