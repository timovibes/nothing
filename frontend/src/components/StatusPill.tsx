// the "stamp"-style status indicator from our design plan — sharp rectangular corners, uppercase
// monospace, colored only by our locked palette (never an arbitrary badge color).

interface StatusPillProps {
  status: string;
}

const STATUS_STYLES: Record<string, { color: string; border: string }> = {
  succeeded: { color: "#1E7A46", border: "#1E7A46" },
  paid: { color: "#1E7A46", border: "#1E7A46" },
  declined: { color: "#FF5449", border: "#FF5449" },
  failed: { color: "#FF5449", border: "#FF5449" },
  processing: { color: "#919191", border: "#919191" },
  requires_payment_method: { color: "#919191", border: "#919191" },
  canceled: { color: "#919191", border: "#919191" },
};

export function StatusPill({ status }: StatusPillProps) {
  const style = STATUS_STYLES[status] ?? { color: "#919191", border: "#919191" };

  return (
    <span
      className="inline-block font-mono text-[11px] uppercase tracking-wider px-2 py-0.5"
      style={{
        color: style.color,
        border: `1px solid ${style.border}`,
      }}
    >
      {status.replace(/_/g, " ")}
    </span>
  );
}