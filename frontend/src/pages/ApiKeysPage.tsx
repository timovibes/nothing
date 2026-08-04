import { useEffect, useState } from "react";
import { api } from "../lib/api";
import type { ApiKey, ApiKeyCreated } from "../types";

export function ApiKeysPage() {
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [revealedKeys, setRevealedKeys] = useState<ApiKeyCreated[] | null>(null);
  const [visibleKeyIds, setVisibleKeyIds] = useState<Set<string>>(new Set());
  const [copiedKeyIds, setCopiedKeyIds] = useState<Set<string>>(new Set());
  const [regenerating, setRegenerating] = useState(false);

  async function loadKeys() {
    setLoading(true);
    try {
      const response = await api.get("/api/v1/merchants/me/api-keys");
      setKeys(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Failed to load API keys");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadKeys();
  }, []);

  async function handleRegenerate() {
    setRegenerating(true);
    setError(null);
    try {
      const response = await api.post("/api/v1/merchants/me/test-keys/regenerate");
      setRevealedKeys(response.data);
      setVisibleKeyIds(new Set());
      await loadKeys();
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Failed to regenerate keys");
    } finally {
      setRegenerating(false);
    }
  }

  function copyToClipboard(id: string, text: string) {
    navigator.clipboard.writeText(text);
    setCopiedKeyIds((prev) => new Set(prev).add(id));
    setTimeout(() => {
      setCopiedKeyIds((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }, 1500);
  }

  function toggleKeyVisibility(id: string) {
    setVisibleKeyIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  function maskKey(rawKey: string) {
    const prefixLen = rawKey.indexOf("_", rawKey.indexOf("_") + 1) + 1; // e.g. "sk_test_"
    const prefix = rawKey.slice(0, prefixLen);
    return `${prefix}${"•".repeat(Math.max(rawKey.length - prefixLen, 8))}`;
  }

  if (loading) {
    return <p className="text-secondary text-sm">Loading…</p>;
  }

  return (
    <div className="max-w-2xl">
      <p className="text-xs uppercase tracking-wide text-secondary mb-2">API Keys</p>
      <p className="text-secondary text-sm mb-8">
        Use these to authenticate requests from your own backend to our payments API.
      </p>

      {revealedKeys && (
        <div className="border border-primary p-4 mb-8">
          <p className="font-mono text-[11px] uppercase tracking-wider text-error mb-3">
            Save these now — the secret key will not be shown again
          </p>
          {revealedKeys.map((key) => {
            const visible = visibleKeyIds.has(key.id);
            return (
              <div key={key.id} className="flex items-center justify-between py-2 border-t border-border first:border-t-0">
                <div>
                  <p className="text-xs text-secondary uppercase">{key.key_type}</p>
                  <p className="font-mono text-sm break-all">
                    {visible ? key.raw_key : maskKey(key.raw_key)}
                  </p>
                </div>
                <div className="flex items-center gap-2 shrink-0 ml-4">
                  <button
                    onClick={() => toggleKeyVisibility(key.id)}
                    aria-label={visible ? "Hide key" : "Show key"}
                    className="text-xs uppercase tracking-wide border border-primary px-2 py-1"
                  >
                    {visible ? "Hide" : "Show"}
                  </button>
                  <button
                    onClick={() => copyToClipboard(key.id, key.raw_key)}
                    className="text-xs uppercase tracking-wide border border-primary px-2 py-1 w-16 text-center"
                    style={copiedKeyIds.has(key.id) ? { color: "#1E7A46", borderColor: "#1E7A46" } : undefined}
                  >
                    {copiedKeyIds.has(key.id) ? "Copied" : "Copy"}
                  </button>
                </div>
              </div>
            );
          })}
          <button
            onClick={() => setRevealedKeys(null)}
            className="text-xs text-secondary underline mt-3"
          >
            Dismiss
          </button>
        </div>
      )}

      {error && <p className="text-error text-sm mb-4">{error}</p>}

      <div>
        {keys.length === 0 ? (
          <p className="text-secondary text-sm">No API keys yet.</p>
        ) : (
          keys.map((key, index) => (
            <div key={key.id}>
              <div className="flex items-center justify-between py-3">
                <div className="flex items-center gap-4">
                  <span className="font-mono text-sm">
                    {key.display_prefix}…
                  </span>
                  <span className="font-mono text-[11px] uppercase tracking-wider border border-secondary text-secondary px-2 py-0.5">
                    {key.key_type}
                  </span>
                  {!key.is_active && (
                    <span className="font-mono text-[11px] uppercase tracking-wider text-error">
                      Revoked
                    </span>
                  )}
                </div>
                <span className="text-xs text-secondary font-mono">
                  {new Date(key.created_at).toLocaleDateString("en-KE", { month: "short", day: "numeric" })}
                </span>
              </div>
              {index < keys.length - 1 && <hr className="ledger-divider" />}
            </div>
          ))
        )}
      </div>

      <hr className="ledger-divider my-8" />

      <button
        onClick={handleRegenerate}
        disabled={regenerating}
        className="bg-primary text-white px-4 py-2 text-sm font-medium disabled:opacity-50"
      >
        {regenerating ? "Regenerating…" : "Regenerate test keys"}
      </button>
      <p className="text-xs text-secondary mt-2">
        This revokes your current test keys immediately and issues a new pair.
      </p>
    </div>
  );
}