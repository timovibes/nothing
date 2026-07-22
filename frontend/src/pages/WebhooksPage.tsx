/*
Webhooks page — replaces the StubPage. Lets the merchant register new endpoints (revealing
the signing secret once, at creation) and view every delivery attempt across all endpoints,
matching WebhookService's real fan-out/retry/backoff behavior.
*/

import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { StatusPill } from "../components/StatusPill";
import { formatDate} from "../lib/format";

interface WebhookEndpointDashboard {
  id: string;
  url: string;
  masked_secret: string;
  subscribed_events: string[];
  is_active: string;
  created_at: string;
}

interface WebhookEndpointCreated {
  id: string;
  url: string;
  signing_secret: string;
  subscribed_events: string[];
  is_active: string;
  created_at: string;
}

interface WebhookDelivery {
  id: string;
  webhook_event_id: string;
  webhook_endpoint_id: string;
  status: string;
  attempt_count: number;
  next_retry_at: string | null;
  last_attempted_at: string | null;
  last_response_status_code: number | null;
  created_at: string;
}

export function WebhooksPage() {
  const [endpoints, setEndpoints] = useState<WebhookEndpointDashboard[]>([]);
  const [deliveries, setDeliveries] = useState<WebhookDelivery[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showForm, setShowForm] = useState(false);
  const [url, setUrl] = useState("");
  const [eventsInput, setEventsInput] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [revealedSecret, setRevealedSecret] = useState<WebhookEndpointCreated | null>(null);

  async function loadData() {
    setLoading(true);
    try {
      const [endpointsRes, deliveriesRes] = await Promise.all([
        api.get("/api/v1/dashboard/webhook-endpoints"),
        api.get("/api/v1/dashboard/webhook-deliveries"),
      ]);
      setEndpoints(endpointsRes.data);
      setDeliveries(deliveriesRes.data);
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Failed to load webhooks");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setFormError(null);
    try {
      const subscribed_events = eventsInput
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);

      const response = await api.post<WebhookEndpointCreated>("/api/v1/dashboard/webhook-endpoints", {
        url,
        subscribed_events,
      });

      setRevealedSecret(response.data);
      setShowForm(false);
      setUrl("");
      setEventsInput("");
      await loadData();
    } catch (err: any) {
      setFormError(err.response?.data?.detail ?? "Failed to register endpoint");
    } finally {
      setSubmitting(false);
    }
  }

  function copyToClipboard(text: string) {
    navigator.clipboard.writeText(text);
  }

  function deliveriesForEndpoint(endpointId: string) {
    return deliveries.filter((d) => d.webhook_endpoint_id === endpointId);
  }

  if (loading) return <p className="text-secondary text-sm">Loading…</p>;
  if (error) return <p className="text-error text-sm">{error}</p>;

  return (
    <div className="max-w-3xl">
      <div className="flex items-start justify-between mb-8">
        <div>
          <p className="text-xs uppercase tracking-wide text-secondary mb-2">Webhooks</p>
          <p className="text-secondary text-sm">
            Endpoints we deliver events to, signed with HMAC-SHA256, retried on failure.
          </p>
        </div>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="bg-primary text-white px-4 py-2 text-sm font-medium shrink-0"
        >
          {showForm ? "Cancel" : "Add endpoint"}
        </button>
      </div>

      {revealedSecret && (
        <div className="border border-primary p-4 mb-8">
          <p className="font-mono text-[11px] uppercase tracking-wider text-error mb-3">
            Save this now — the full signing secret will not be shown again
          </p>
          <p className="text-xs text-secondary mb-1">{revealedSecret.url}</p>
          <div className="flex items-center justify-between">
            <p className="font-mono text-sm break-all">{revealedSecret.signing_secret}</p>
            <button
              onClick={() => copyToClipboard(revealedSecret.signing_secret)}
              className="text-xs uppercase tracking-wide border border-primary px-2 py-1 shrink-0 ml-4"
            >
              Copy
            </button>
          </div>
          <button
            onClick={() => setRevealedSecret(null)}
            className="text-xs text-secondary underline mt-3"
          >
            Dismiss
          </button>
        </div>
      )}

      {showForm && (
        <form onSubmit={handleSubmit} className="border border-border p-5 mb-8 flex flex-col gap-4">
          <div>
            <label className="text-xs uppercase tracking-wide text-secondary block mb-1">Endpoint URL</label>
            <input
              type="url"
              required
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com/webhooks/payflow"
              className="w-full border border-border px-3 py-2 text-sm font-mono focus:outline-none focus:border-primary"
            />
          </div>
          <div>
            <label className="text-xs uppercase tracking-wide text-secondary block mb-1">
              Subscribed events (comma-separated, leave blank for all)
            </label>
            <input
              type="text"
              value={eventsInput}
              onChange={(e) => setEventsInput(e.target.value)}
              placeholder="payment_intent.succeeded, payment_intent.refunded"
              className="w-full border border-border px-3 py-2 text-sm font-mono focus:outline-none focus:border-primary"
            />
          </div>
          {formError && <p className="text-error text-sm">{formError}</p>}
          <button
            type="submit"
            disabled={submitting}
            className="bg-primary text-white px-4 py-2 text-sm font-medium disabled:opacity-50 self-start"
          >
            {submitting ? "Registering…" : "Register endpoint"}
          </button>
        </form>
      )}

      {endpoints.length === 0 ? (
        <p className="text-secondary text-sm">No webhook endpoints yet.</p>
      ) : (
        <div>
          {endpoints.map((endpoint, index) => {
            const endpointDeliveries = deliveriesForEndpoint(endpoint.id);
            return (
              <div key={endpoint.id}>
                <div className="py-4">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-mono text-sm break-all">{endpoint.url}</span>
                    <span className="font-mono text-[11px] uppercase tracking-wider text-secondary shrink-0 ml-4">
                      {endpoint.is_active}
                    </span>
                  </div>
                  <p className="font-mono text-xs text-secondary mb-3">{endpoint.masked_secret}</p>
                  <p className="text-xs text-secondary mb-3">
                    {endpoint.subscribed_events.length === 0
                      ? "Subscribed to all events"
                      : endpoint.subscribed_events.join(", ")}
                  </p>

                  {endpointDeliveries.length > 0 && (
                    <div className="bg-black/[0.02] px-3 py-3">
                      <p className="text-xs uppercase tracking-wide text-secondary mb-2">
                        Delivery attempts
                      </p>
                      {endpointDeliveries.map((delivery) => (
                        <div key={delivery.id} className="flex items-center justify-between py-1.5 text-sm">
                          <StatusPill status={delivery.status} />
                          <span className="font-mono text-xs text-secondary">
                            attempt {delivery.attempt_count}
                          </span>
                          <span className="font-mono text-xs text-secondary">
                            {delivery.last_response_status_code ?? "—"}
                          </span>
                          <span className="font-mono text-xs text-secondary">
                            {formatDate(delivery.created_at)}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                {index < endpoints.length - 1 && <hr className="ledger-divider" />}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}