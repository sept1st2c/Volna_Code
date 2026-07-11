import { ImageResponse } from "next/og";

export const size = { width: 32, height: 32 };
export const contentType = "image/png";

// Branded favicon: the ember gradient from globals.css's `.text-gradient-ember`,
// applied to a bold "V" on the same off-black canvas as the rest of the site,
// so the browser tab matches the wordmark in Nav.tsx/Footer.tsx instead of
// showing the stock Next.js default.
export default function Icon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "#0a0a0c",
          borderRadius: 7,
        }}
      >
        <span
          style={{
            fontSize: 22,
            fontWeight: 700,
            backgroundImage: "linear-gradient(120deg, #ffcf7a 0%, #ff8a2a 42%, #fa520f 100%)",
            backgroundClip: "text",
            color: "transparent",
          }}
        >
          V
        </span>
      </div>
    ),
    { ...size },
  );
}
