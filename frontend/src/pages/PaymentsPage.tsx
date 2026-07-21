/*
The real Payments list page — replaces the StubPage. Fetches every payment intent for the
logged-in merchant via the existing JWT dashboard endpoint, and lets the merchant expand any
row to see its refund history (if any) via the same-shaped refunds endpoint, filtered
client-side to that intent — mirrors the ledger-tape/stamp visual language from Overview.
*/

import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { StatusPill } from "../components/StatusPill";
import { formatMoney, formatDate, shortId } from "../lib/format";
import type { PaymentIntent, Refund } from "../types";

export function PaymentsPage() {
  const [intents, setIntents] = useState<PaymentIntent[]>([]);
  const [refundsByIntent, setRefundsByIntent] = useState<Record<string, Refund[]>>({});
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [intentsRes, refundsRes] = await Promise.all([
          api.get("/api/v1/dashboard/payment-intents"),
          api.get("/api/v1/dashboard/refunds"),
        ]);
        setIntents(intentsRes.data);

        const grouped: Record<string, Refund[]> = {};
        for (const refund of refundsRes.data as Refund[]) {
          if (!grouped[refund.payment_intent_id]) grouped[refund.payment_intent_id] = [];
          grouped[refund.payment_intent_id].push(refund);
        }
        setRefundsByIntent(grouped);
      } catch (err: any) {
        setError(err.response?.data?.detail ?? "Failed to load payments");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  function toggleExpanded(id: string) {
    setExpandedId((prev) => (prev === id ? null : id));
  }

  if (loading) {
    return <p className="text-secondary text-sm">Loading…</p>;
  }

  if (error) {
    return <p className="text-error text-sm">{error}</p>;
  }

  return (
    <div className="max-w-3xl">
      <p className="text-xs uppercase tracking-wide text-secondary mb-2">Payments</p>
      <p className="text-secondary text-sm mb-8">
        All payment intents created by your account, test and live.
      </p>

      {intents.length === 0 ? (
        <p className="text-secondary text-sm">No payments yet.</p>
      ) : (
        <div>
          {intents.map((intent, index) => {
            const refunds = refundsByIntent[intent.id] ?? [];
            const isExpanded = expandedId === intent.id;
            const isRefundable = intent.status === "succeeded";

            return (
              <div key={intent.id}>
                <button
                  onClick={() => toggleExpanded(intent.id)}
                  className="w-full flex items-center justify-between py-3 text-left"
                >
                  <div className="flex items-center gap-4">
                    <span className="font-mono text-sm tabular-nums w-28">
                      {formatMoney(intent.amount_minor, intent.currency)}
                    </span>
                    <StatusPill status={intent.status} />
                    {refunds.length > 0 && (
                      <span className="font-mono text-[11px] uppercase tracking-wider text-secondary">
                        {refunds.length} refund{refunds.length > 1 ? "s" : ""}
                      </span>
                    )}
                    {intent.description && (
                      <span className="text-sm text-secondary hidden sm:inline">
                        {intent.description}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-4 text-xs text-secondary font-mono">
                    <span>{formatDate(intent.created_at)}</span>
                    <span>{shortId(intent.id)}</span>
                  </div>
                </button>

                {isExpanded && (
                  <div className="bg-black/[0.02] px-4 py-4 mb-1">
                    <div className="grid grid-cols-2 gap-y-2 text-sm mb-3">
                      <span className="text-secondary">Intent ID</span>
                      <span className="font-mono text-xs break-all">{intent.id}</span>
                      <span className="text-secondary">Mode</span>
                      <span className="font-mono text-xs uppercase">{intent.is_live_mode}</span>
                      {intent.failure_reason && (
                        <>
                          <span className="text-secondary">Failure reason</span>
                          <span className="font-mono text-xs">{intent.failure_reason}</span>
                        </>
                      )}
                    </div>

                    {refunds.length > 0 && (
                      <>
                        <p className="text-xs uppercase tracking-wide text-secondary mt-4 mb-2">
                          Refund history
                        </p>
                        {refunds.map((refund) => (
                          <div key={refund.id} className="flex items-center justify-between py-1.5 text-sm">
                            <span className="font-mono tabular-nums">
                              {formatMoney(refund.amount_minor, refund.currency)}
                            </span>
                            <StatusPill status={refund.status} />
                            <span className="text-secondary text-xs">{refund.reason ?? "—"}</span>
                            <span className="font-mono text-xs text-secondary">
                              {formatDate(refund.created_at)}
                            </span>
                          </div>
                        ))}
                      </>
                    )}

                    {isRefundable && refunds.length === 0 && (
                      <p className="text-secondary text-xs mt-3">
                        No refunds issued for this payment.
                      </p>
                    )}
                  </div>
                )}

                {index < intents.length - 1 && <hr className="ledger-divider" />}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}