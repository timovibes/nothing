interface StatusPillProps {
  status: string;
}

const STATUS_STYLES: Record<string, { color: string; bg: string }> = {
  succeeded: { color: "#1E7A46", bg: "rgba(30, 122, 70, 0.08)" },
  paid: { color: "#1E7A46", bg: "rgba(30, 122, 70, 0.08)" },
  declined: { color: "#FF5449", bg: "rgba(255, 84, 73, 0.08)" },
  failed: { color: "#FF5449", bg: "rgba(255, 84, 73, 0.08)" },
  processing: { color: "#919191", bg: "rgba(145, 145, 145, 0.08)" },
  requires_payment_method: { color: "#919191", bg: "rgba(145, 145, 145, 0.08)" },
  canceled: { color: "#919191", bg: "rgba(145, 145, 145, 0.08)" },
};

export function StatusPill({ status }: StatusPillProps) {
  const style = STATUS_STYLES[status] ?? { color: "#919191", bg: "rgba(145, 145, 145, 0.08)" };

  return (
    <span
      className="inline-block font-mono text-[11px] uppercase tracking-wider px-3 py-1 rounded-neu-full shadow-neu-raised-sm"
      style={{
        color: style.color,
        backgroundColor: style.bg,
      }}
    >
      {status.replace(/_/g, " ")}
    </span>
  );
}