/*
Refunds page — replaces the StubPage. Lists every refund the merchant has issued, and lets
them issue a new one against any succeeded, not-fully-refunded payment intent, directly from
the dashboard (JWT-authenticated), not just via sk_test/curl.
*/

import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { StatusPill } from "../components/StatusPill";
import { formatMoney, formatDate, shortId } from "../lib/format";
import type { Refund, PaymentIntent } from "../types";

export function RefundsPage() {
  const [refunds, setRefunds] = useState<Refund[]>([]);
  const [intents, setIntents] = useState<PaymentIntent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showForm, setShowForm] = useState(false);
  const [selectedIntentId, setSelectedIntentId] = useState("");
  const [amountMajor, setAmountMajor] = useState(""); // entered in KES, converted to minor units on submit
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  async function loadData() {
    setLoading(true);
    try {
      const [refundsRes, intentsRes] = await Promise.all([
        api.get("/api/v1/dashboard/refunds"),
        api.get("/api/v1/dashboard/payment-intents"),
      ]);
      setRefunds(refundsRes.data);
      setIntents(intentsRes.data);
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Failed to load refunds");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  // Only succeeded intents can be refunded at all — mirrors the backend's own check
  const refundableIntents = intents.filter((i) => i.status === "succeeded");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedIntentId) {
      setFormError("Choose a payment to refund.");
      return;
    }
    setSubmitting(true);
    setFormError(null);
    try {
      const body: { amount_minor?: number; reason?: string } = {};
      if (amountMajor.trim() !== "") {
        body.amount_minor = Math.round(parseFloat(amountMajor) * 100);
      }
      if (reason.trim() !== "") {
        body.reason = reason.trim();
      }

      await api.post(`/api/v1/dashboard/payment-intents/${selectedIntentId}/refund`, body);

      setShowForm(false);
      setSelectedIntentId("");
      setAmountMajor("");
      setReason("");
      await loadData();
    } catch (err: any) {
      setFormError(err.response?.data?.detail ?? "Failed to issue refund");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return <p className="text-secondary text-sm">Loading…</p>;
  }

  if (error) {
    return <p className="text-error text-sm">{error}</p>;
  }

  return (
    <div className="max-w-3xl">
      <div className="flex items-start justify-between mb-8">
        <div>
          <p className="text-xs uppercase tracking-wide text-secondary mb-2">Refunds</p>
          <p className="text-secondary text-sm">
            Full or partial refunds. The platform fee is never reversed.
          </p>
        </div>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="bg-primary text-white px-4 py-2 text-sm font-medium shrink-0"
        >
          {showForm ? "Cancel" : "Issue refund"}
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={handleSubmit}
          className="border border-border p-5 mb-8 flex flex-col gap-4"
        >
          <div>
            <label className="text-xs uppercase tracking-wide text-secondary block mb-1">
              Payment to refund
            </label>
            <select
              value={selectedIntentId}
              onChange={(e) => setSelectedIntentId(e.target.value)}
              className="w-full border border-border px-3 py-2 text-sm font-mono focus:outline-none focus:border-primary"
            >
              <option value="">Select a payment…</option>
              {refundableIntents.map((intent) => (
                <option key={intent.id} value={intent.id}>
                  {formatMoney(intent.amount_minor, intent.currency)} — {shortId(intent.id)}
                  {intent.description ? ` — ${intent.description}` : ""}
                </option>
              ))}
            </select>
            {refundableIntents.length === 0 && (
              <p className="text-xs text-secondary mt-1">
                No succeeded payments available to refund.
              </p>
            )}
          </div>

          <div>
            <label className="text-xs uppercase tracking-wide text-secondary block mb-1">
              Amount (leave blank for full refund of remaining balance)
            </label>
            <input
              type="text"
              inputMode="decimal"
              value={amountMajor}
              onChange={(e) => setAmountMajor(e.target.value)}
              placeholder="e.g. 500.00"
              className="w-full border border-border px-3 py-2 text-sm font-mono focus:outline-none focus:border-primary"
            />
          </div>

          <div>
            <label className="text-xs uppercase tracking-wide text-secondary block mb-1">
              Reason (optional)
            </label>
            <input
              type="text"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="e.g. Customer requested refund"
              className="w-full border border-border px-3 py-2 text-sm focus:outline-none focus:border-primary"
            />
          </div>

          {formError && <p className="text-error text-sm">{formError}</p>}

          <button
            type="submit"
            disabled={submitting}
            className="bg-primary text-white px-4 py-2 text-sm font-medium disabled:opacity-50 self-start"
          >
            {submitting ? "Processing…" : "Confirm refund"}
          </button>
        </form>
      )}

      {refunds.length === 0 ? (
        <p className="text-secondary text-sm">No refunds yet.</p>
      ) : (
        <div>
          {refunds.map((refund, index) => (
            <div key={refund.id}>
              <div className="flex items-center justify-between py-3">
                <div className="flex items-center gap-4">
                  <span className="font-mono text-sm tabular-nums w-28">
                    {formatMoney(refund.amount_minor, refund.currency)}
                  </span>
                  <StatusPill status={refund.status} />
                  {refund.reason && (
                    <span className="text-sm text-secondary hidden sm:inline">
                      {refund.reason}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-4 text-xs text-secondary font-mono">
                  <span>{formatDate(refund.created_at)}</span>
                  <span title={`Payment intent ${refund.payment_intent_id}`}>
                    {shortId(refund.payment_intent_id)}
                  </span>
                </div>
              </div>
              {index < refunds.length - 1 && <hr className="ledger-divider" />}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}