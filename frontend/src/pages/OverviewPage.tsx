/* the real dashboard Overview page — fetches live balance and recent payment activity from our
new JWT endpoints, styled per our locked palette and ledger-tape/stamp design language.*/

import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { StatusPill } from "../components/StatusPill";
import { formatMoney, formatDate, shortId } from "../lib/format";
import type { WalletBalance, PaymentIntent } from "../types";

export function OverviewPage() {
  const [balance, setBalance] = useState<WalletBalance | null>(null);
  const [intents, setIntents] = useState<PaymentIntent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [balanceRes, intentsRes] = await Promise.all([
          api.get("/api/v1/dashboard/wallet-balance"),
          api.get("/api/v1/dashboard/payment-intents"),
        ]);
        setBalance(balanceRes.data[0] ?? null);
        setIntents(intentsRes.data);
      } catch (err: any) {
        setError(err.response?.data?.detail ?? "Failed to load dashboard data");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return <div className="p-8 font-body text-secondary">Loading…</div>;
  }

  if (error) {
    return <div className="p-8 font-body text-error">{error}</div>;
  }

  return (
    <div className="min-h-screen bg-surface font-body">
      {/* Header */}
      <header className="flex items-center justify-between px-8 py-5 border-b border-border">
        <span className="font-display font-bold text-lg">nothing</span>
        <div className="flex items-center gap-4 text-sm">
          <span className="font-mono text-[11px] uppercase tracking-wider border border-secondary text-secondary px-2 py-0.5">
            Test mode
          </span>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-8 py-10">
        {/* Balance */}
        <section>
          <p className="text-xs uppercase tracking-wide text-secondary mb-2">
            Available balance
          </p>
          <p className="font-display font-bold text-4xl tabular-nums">
            {balance ? formatMoney(balance.available_balance_minor, balance.currency) : "—"}
          </p>
          <p className="text-sm text-secondary mt-2">
            Total settled to date:{" "}
            <span className="tabular-nums font-mono">
              {balance ? formatMoney(balance.total_settled_minor, balance.currency) : "—"}
            </span>
          </p>
        </section>

        <hr className="ledger-divider my-8" />

        {/* Recent activity */}
        <section>
          <p className="text-xs uppercase tracking-wide text-secondary mb-4">
            Recent activity
          </p>

          {intents.length === 0 ? (
            <p className="text-secondary text-sm">No payments yet.</p>
          ) : (
            <div>
              {intents.map((intent, index) => (
                <div key={intent.id}>
                  <div className="flex items-center justify-between py-3">
                    <div className="flex items-center gap-4">
                      <span className="font-mono text-sm tabular-nums w-28">
                        {formatMoney(intent.amount_minor, intent.currency)}
                      </span>
                      <StatusPill status={intent.status} />
                      {intent.failure_reason && (
                        <span className="text-xs text-secondary font-mono">
                          {intent.failure_reason}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-4 text-xs text-secondary font-mono">
                      <span>{formatDate(intent.created_at)}</span>
                      <span>{shortId(intent.id)}</span>
                    </div>
                  </div>
                  {index < intents.length - 1 && <hr className="ledger-divider" />}
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}