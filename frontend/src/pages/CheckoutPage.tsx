/*
The hosted Customer Checkout page — a customer lands here via a merchant-generated link
containing the payment intent id, its client_secret, and the merchant's publishable (pk_)
key as query params. No JWT, no dashboard layout, no merchant auth of any kind. This is the
one page in the whole system a person outside the merchant's team ever sees.

Flow: load intent details -> customer enters card -> tokenize -> confirm -> show outcome.
*/

import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { createCheckoutClient } from "../lib/checkoutApi";
import { formatMoney } from "../lib/format";
import { StatusPill } from "../components/StatusPill";
import type { CheckoutIntent, CheckoutPaymentMethodCreated } from "../types";

export function CheckoutPage() {
  const { intentId } = useParams<{ intentId: string }>();
  const [searchParams] = useSearchParams();
  const clientSecret = searchParams.get("client_secret") ?? "";
  const publishableKey = searchParams.get("pk") ?? "";

  const [intent, setIntent] = useState<CheckoutIntent | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [cardNumber, setCardNumber] = useState("");
  const [expMonth, setExpMonth] = useState("");
  const [expYear, setExpYear] = useState("");
  const [cvv, setCvv] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const client = createCheckoutClient(publishableKey);

  useEffect(() => {
    if (!intentId || !clientSecret || !publishableKey) {
      setLoadError("This checkout link is missing required information.");
      setLoading(false);
      return;
    }

    async function loadIntent() {
      try {
        const response = await client.get(
          `/api/v1/checkout/payment-intents/${intentId}`,
          { params: { client_secret: clientSecret } }
        );
        setIntent(response.data);
      } catch (err: any) {
        setLoadError(err.response?.data?.detail ?? "This payment link is invalid or has expired.");
      } finally {
        setLoading(false);
      }
    }
    loadIntent();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [intentId, clientSecret, publishableKey]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!intent) return;

    setSubmitting(true);
    setSubmitError(null);

    try {
      const tokenizeRes = await client.post<CheckoutPaymentMethodCreated>(
        "/api/v1/checkout/payment-methods",
        {
          card_number: cardNumber.replace(/\s/g, ""),
          exp_month: Number(expMonth),
          exp_year: Number(expYear),
          cvv,
        }
      );
      const paymentMethodId = tokenizeRes.data.id;

      const confirmRes = await client.post(
        `/api/v1/checkout/payment-intents/${intentId}/confirm`,
        { payment_method_id: paymentMethodId },
        { params: { client_secret: clientSecret } }
      );

      setIntent((prev) => (prev ? { ...prev, status: confirmRes.data.status } : prev));
    } catch (err: any) {
      setSubmitError(err.response?.data?.detail ?? "Payment could not be processed. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface">
        <p className="font-body text-secondary text-sm">Loading…</p>
      </div>
    );
  }

  if (loadError || !intent) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface px-6">
        <p className="font-body text-error text-sm max-w-sm text-center">{loadError}</p>
      </div>
    );
  }

  const isFinal = intent.status === "succeeded" || intent.status === "declined" || intent.status === "canceled";

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center px-6 py-12">
      <div className="w-full max-w-sm">
        <p className="font-display font-bold text-lg mb-8">nothing</p>

        <div className="mb-8">
          <p className="text-xs uppercase tracking-wide text-secondary mb-2">Amount due</p>
          <p className="font-display font-bold text-3xl tabular-nums">
            {formatMoney(intent.amount_minor, intent.currency)}
          </p>
          {intent.description && (
            <p className="text-sm text-secondary mt-1">{intent.description}</p>
          )}
        </div>

        <hr className="ledger-divider mb-8" />

        {isFinal ? (
          <div className="flex flex-col items-start gap-3">
            <StatusPill status={intent.status} />
            <p className="text-sm text-secondary">
              {intent.status === "succeeded" && "Payment received. You may close this page."}
              {intent.status === "declined" && "This payment was declined. Please try a different card."}
              {intent.status === "canceled" && "This payment was canceled."}
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div>
              <label className="text-xs uppercase tracking-wide text-secondary block mb-1">
                Card number
              </label>
              <input
                type="text"
                inputMode="numeric"
                required
                value={cardNumber}
                onChange={(e) => setCardNumber(e.target.value)}
                placeholder="4242 4242 4242 4242"
                className="w-full border border-border px-3 py-2 font-mono text-sm focus:outline-none focus:border-primary"
              />
            </div>

            <div className="flex gap-3">
              <div className="flex-1">
                <label className="text-xs uppercase tracking-wide text-secondary block mb-1">
                  Month
                </label>
                <input
                  type="text"
                  inputMode="numeric"
                  required
                  value={expMonth}
                  onChange={(e) => setExpMonth(e.target.value)}
                  placeholder="12"
                  className="w-full border border-border px-3 py-2 font-mono text-sm focus:outline-none focus:border-primary"
                />
              </div>
              <div className="flex-1">
                <label className="text-xs uppercase tracking-wide text-secondary block mb-1">
                  Year
                </label>
                <input
                  type="text"
                  inputMode="numeric"
                  required
                  value={expYear}
                  onChange={(e) => setExpYear(e.target.value)}
                  placeholder="2027"
                  className="w-full border border-border px-3 py-2 font-mono text-sm focus:outline-none focus:border-primary"
                />
              </div>
              <div className="flex-1">
                <label className="text-xs uppercase tracking-wide text-secondary block mb-1">
                  CVV
                </label>
                <input
                  type="text"
                  inputMode="numeric"
                  required
                  value={cvv}
                  onChange={(e) => setCvv(e.target.value)}
                  placeholder="123"
                  className="w-full border border-border px-3 py-2 font-mono text-sm focus:outline-none focus:border-primary"
                />
              </div>
            </div>

            {submitError && <p className="text-error text-sm">{submitError}</p>}

            <button
              type="submit"
              disabled={submitting}
              className="bg-primary text-white px-4 py-3 text-sm font-medium disabled:opacity-50 mt-2"
            >
              {submitting ? "Processing…" : `Pay ${formatMoney(intent.amount_minor, intent.currency)}`}
            </button>

            <p className="text-xs text-secondary text-center mt-1">
              Test mode — card ending in .00 approves, .01/.02 decline, .03 times out.
            </p>
          </form>
        )}
      </div>
    </div>
  );
}