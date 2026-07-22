/*
Payouts page — replaces the StubPage. Payouts are generated automatically by the T+2 daily
settlement sweep (Celery Beat), not manually created by the merchant — this page is the real,
live view into that process: what's been paid, what's in transit, and when the next batch
lands, using the existing JWT dashboard payouts endpoint.
*/

import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { StatusPill } from "../components/StatusPill";
import { formatMoney, formatDate } from "../lib/format";

interface Payout {
  id: string;
  amount_minor: number;
  currency: string;
  status: "in_transit" | "paid" | "failed" | string;
  failure_reason: string | null;
  initiated_at: string;
  expected_arrival_at: string;
  paid_at: string | null;
}

export function PayoutsPage() {
  const [payouts, setPayouts] = useState<Payout[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadPayouts() {
      try {
        const response = await api.get("/api/v1/dashboard/payouts");
        setPayouts(response.data);
      } catch (err: any) {
        setError(err.response?.data?.detail ?? "Failed to load payouts");
      } finally {
        setLoading(false);
      }
    }
    loadPayouts();
  }, []);

  if (loading) return <p className="text-secondary text-sm">Loading…</p>;
  if (error) return <p className="text-error text-sm">{error}</p>;

  return (
    <div className="max-w-3xl">
      <p className="text-xs uppercase tracking-wide text-secondary mb-2">Payouts</p>
      <p className="text-secondary text-sm mb-8">
        Your available balance is swept to your bank account automatically, T+2 days after
        settlement. Nothing to trigger here.
      </p>

      {payouts.length === 0 ? (
        <p className="text-secondary text-sm">
          No payouts yet. Once you have settled balance, the next scheduled sweep will create one.
        </p>
      ) : (
        <div>
          {payouts.map((payout, index) => (
            <div key={payout.id}>
              <div className="flex items-center justify-between py-3">
                <div className="flex items-center gap-4">
                  <span className="font-mono text-sm tabular-nums w-28">
                    {formatMoney(payout.amount_minor, payout.currency)}
                  </span>
                  <StatusPill status={payout.status} />
                  {payout.failure_reason && (
                    <span className="text-xs text-secondary font-mono">{payout.failure_reason}</span>
                  )}
                </div>
                <div className="flex items-center gap-6 text-xs text-secondary font-mono">
                  <span title="Initiated">{formatDate(payout.initiated_at)}</span>
                  <span title={payout.paid_at ? "Paid" : "Expected arrival"}>
                    {payout.paid_at ? formatDate(payout.paid_at) : `→ ${formatDate(payout.expected_arrival_at)}`}
                  </span>
                </div>
              </div>
              {index < payouts.length - 1 && <hr className="ledger-divider" />}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}