/* the real dashboard Overview page — fetches live balance and recent payment activity from our
new JWT endpoints, styled per our locked palette and soft neumorphic depth language. */

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { StatusPill } from "../components/StatusPill";
import { ChevronIcon } from "../components/ChevronIcon";
import { formatMoney, formatDate, shortId } from "../lib/format";
import type { WalletBalance, PaymentIntent } from "../types";

const ACTIVITIES_PER_PAGE = 5;

export function OverviewPage() {
  const navigate = useNavigate();
  const [balance, setBalance] = useState<WalletBalance | null>(null);
  const [intents, setIntents] = useState<PaymentIntent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [visibleCount, setVisibleCount] = useState(ACTIVITIES_PER_PAGE);

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
        if (err.response?.data?.detail === "This user has no merchant account yet") {
          navigate("/onboarding");
          return;
        }
        setError(err.response?.data?.detail ?? "Failed to load dashboard data");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [navigate]);

  if (loading) {
    return <div className="p-8 font-body text-secondary">Loading…</div>;
  }

  if (error) {
    return <div className="p-8 font-body text-error">{error}</div>;
  }

  const visibleIntents = intents.slice(0, visibleCount);

  return (
    <div className="max-w-3xl flex flex-col gap-6">
      {/* Balance */}
      <section className="rounded-neu-lg shadow-neu-raised-sm bg-surface p-6">
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

      {/* Recent activity */}
      <section className="rounded-neu-lg shadow-neu-raised-sm bg-surface p-6">
        <p className="text-xs uppercase tracking-wide text-secondary mb-4">
          Recent activity
        </p>

        {intents.length === 0 ? (
          <p className="text-secondary text-sm">No payments yet.</p>
        ) : (
          <>
            <div>
              {visibleIntents.map((intent, index) => (
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
                  {index < visibleIntents.length - 1 && <hr className="ledger-divider" />}
                </div>
              ))}
            </div>

            {(intents.length > visibleCount || visibleCount > ACTIVITIES_PER_PAGE) && (
              <div className="flex items-center gap-4 mt-4">
                {intents.length > visibleCount && (
                  <button
                    onClick={() => setVisibleCount((n) => n + ACTIVITIES_PER_PAGE)}
                    className="flex items-center gap-1 text-xs uppercase tracking-wide text-secondary px-2 py-1 rounded-neu-sm hover:shadow-neu-raised-sm transition-shadow"
                  >
                    Show more <ChevronIcon direction="down" />
                  </button>
                )}
                {visibleCount > ACTIVITIES_PER_PAGE && (
                  <button
                    onClick={() => setVisibleCount(ACTIVITIES_PER_PAGE)}
                    className="flex items-center gap-1 text-xs uppercase tracking-wide text-secondary px-2 py-1 rounded-neu-sm hover:shadow-neu-raised-sm transition-shadow"
                  >
                    Show less <ChevronIcon direction="up" />
                  </button>
                )}
              </div>
            )}
          </>
        )}
      </section>
    </div>
  );
}