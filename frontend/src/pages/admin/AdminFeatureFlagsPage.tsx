/*
Feature flags — global or per-merchant rollout toggles.
*/

import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import { shortId } from "../../lib/format";
import type { FeatureFlag } from "../../types";

export function AdminFeatureFlagsPage() {
  const [flags, setFlags] = useState<FeatureFlag[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [key, setKey] = useState("");
  const [merchantId, setMerchantId] = useState("");
  const [enabled, setEnabled] = useState(true);
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  async function loadFlags() {
    setLoading(true);
    try {
      const response = await api.get("/api/v1/admin/feature-flags");
      setFlags(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Failed to load feature flags");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadFlags();
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setSaveError(null);
    try {
      await api.post("/api/v1/admin/feature-flags", {
        key,
        merchant_id: merchantId.trim() || null,
        enabled,
        description: description.trim() || null,
      });
      setKey("");
      setMerchantId("");
      setEnabled(true);
      setDescription("");
      await loadFlags();
    } catch (err: any) {
      setSaveError(err.response?.data?.detail ?? "Failed to create flag");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <p className="text-secondary text-sm">Loading…</p>;
  if (error) return <p className="text-error text-sm">{error}</p>;

  return (
    <div className="max-w-3xl">
      <p className="text-xs uppercase tracking-wide text-secondary mb-2">Feature Flags</p>
      <p className="text-secondary text-sm mb-8">Global or per-merchant rollout toggles.</p>

      <form onSubmit={handleSubmit} className="border border-border p-5 mb-8 flex flex-col gap-4">
        <div>
          <label className="text-xs uppercase tracking-wide text-secondary block mb-1">Key</label>
          <input
            type="text"
            required
            value={key}
            onChange={(e) => setKey(e.target.value)}
            className="w-full border border-border px-3 py-2 text-sm font-mono focus:outline-none focus:border-primary"
          />
        </div>
        <div>
          <label className="text-xs uppercase tracking-wide text-secondary block mb-1">
            Merchant ID (leave blank for global)
          </label>
          <input
            type="text"
            value={merchantId}
            onChange={(e) => setMerchantId(e.target.value)}
            className="w-full border border-border px-3 py-2 text-sm font-mono focus:outline-none focus:border-primary"
          />
        </div>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={enabled} onChange={(e) => setEnabled(e.target.checked)} />
          Enabled
        </label>
        <div>
          <label className="text-xs uppercase tracking-wide text-secondary block mb-1">Description</label>
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full border border-border px-3 py-2 text-sm focus:outline-none focus:border-primary"
          />
        </div>
        {saveError && <p className="text-error text-sm">{saveError}</p>}
        <button
          type="submit"
          disabled={saving}
          className="bg-primary text-white px-4 py-2 text-sm font-medium disabled:opacity-50 self-start"
        >
          {saving ? "Creating…" : "Create flag"}
        </button>
      </form>

      {flags.length === 0 ? (
        <p className="text-secondary text-sm">No feature flags yet.</p>
      ) : (
        <div>
          {flags.map((flag, index) => (
            <div key={flag.id}>
              <div className="flex items-center justify-between py-3">
                <div>
                  <span className="font-mono text-sm">{flag.key}</span>
                  <span className="text-xs text-secondary ml-3">
                    {flag.merchant_id ? shortId(flag.merchant_id) : "global"}
                  </span>
                </div>
                <span
                  className="font-mono text-[11px] uppercase tracking-wider px-2 py-0.5 border"
                  style={{
                    color: flag.enabled ? "#1E7A46" : "#919191",
                    borderColor: flag.enabled ? "#1E7A46" : "#919191",
                  }}
                >
                  {flag.enabled ? "enabled" : "disabled"}
                </span>
              </div>
              {index < flags.length - 1 && <hr className="ledger-divider" />}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}