// src/components/ChevronIcon.tsx
// Small inline chevron used by "show more / show less" toggles.
// Dependency-free (no icon library in this project) — just SVG.

export function ChevronIcon({ direction = "down" }: { direction?: "down" | "up" }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      style={{
        transform: direction === "up" ? "rotate(180deg)" : undefined,
        transition: "transform 0.15s ease",
      }}
    >
      <polyline points="6 9 12 15 18 9" />
    </svg>
  );
}