import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { ChevronIcon } from "../components/ChevronIcon";
import type { ApiKey, ApiKeyCreated } from "../types";

export function ApiKeysPage() {
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [revealedKeys, setRevealedKeys] = useState<ApiKeyCreated[] | null>(null);
  const [visibleKeyIds, setVisibleKeyIds] = useState<Set<string>>(new Set());
  const [copiedKeyIds, setCopiedKeyIds] = useState<Set<string>>(new Set());
  const [regenerating, setRegenerating] = useState(false);
  const [visiblePairs, setVisiblePairs] = useState(3);

  const KEYS_PER_PAIR = 2;
  const visibleCount = visiblePairs * KEYS_PER_PAIR;

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
    <div className="max-w-2xl flex flex-col gap-6">
      <div>
        <p className="text-xs uppercase tracking-wide text-secondary mb-2">API Keys</p>
        <p className="text-secondary text-sm">
          Use these to authenticate requests from your own backend to our payments API.
        </p>
      </div>

      {revealedKeys && (
        <div className="rounded-neu-lg shadow-neu-raised bg-surface p-4">
          <p className="font-mono text-[11px] uppercase tracking-wider text-error mb-3">
            Save these now — the secret key will not be shown again
          </p>
          {revealedKeys.map((key) => {
            const visible = visibleKeyIds.has(key.id);
            return (
              <div key={key.id} className="flex items-center justify-between py-2 rounded-neu-sm px-2 -mx-2">
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
                    className="text-xs uppercase tracking-wide px-2 py-1 rounded-neu-sm shadow-neu-raised-sm hover:shadow-neu-hover active:shadow-neu-inset-sm transition-shadow"
                  >
                    {visible ? "Hide" : "Show"}
                  </button>
                  <button
                    onClick={() => copyToClipboard(key.id, key.raw_key)}
                    className="text-xs uppercase tracking-wide px-2 py-1 w-16 text-center rounded-neu-sm shadow-neu-raised-sm hover:shadow-neu-hover active:shadow-neu-inset-sm transition-shadow"
                    style={copiedKeyIds.has(key.id) ? { color: "#1E7A46" } : undefined}
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

      {error && <p className="text-error text-sm">{error}</p>}

      <div className="rounded-neu-lg shadow-neu-raised-sm bg-surface p-6">
        {keys.length === 0 ? (
          <p className="text-secondary text-sm">No API keys yet.</p>
        ) : (
          keys.slice(0, visibleCount).map((key, index, slicedKeys) => (
            <div key={key.id}>
              <div className="flex items-center justify-between py-3">
                <div className="flex items-center gap-4">
                  <span className="font-mono text-sm">
                    {key.display_prefix}…
                  </span>
                  <span className="font-mono text-[11px] uppercase tracking-wider px-3 py-1 rounded-neu-full shadow-neu-raised-sm text-secondary">
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
              {index < slicedKeys.length - 1 && <hr className="ledger-divider" />}
            </div>
          ))
        )}

        {(keys.length > visibleCount || visiblePairs > 3) && (
          <div className="flex items-center gap-4 mt-4">
            {keys.length > visibleCount && (
              <button
                onClick={() => setVisiblePairs((n) => n + 3)}
                className="flex items-center gap-1 text-xs uppercase tracking-wide text-secondary px-2 py-1 rounded-neu-sm hover:shadow-neu-raised-sm transition-shadow"
              >
                Show more <ChevronIcon direction="down" />
              </button>
            )}
            {visiblePairs > 3 && (
              <button
                onClick={() => setVisiblePairs(3)}
                className="flex items-center gap-1 text-xs uppercase tracking-wide text-secondary px-2 py-1 rounded-neu-sm hover:shadow-neu-raised-sm transition-shadow"
              >
                Show less <ChevronIcon direction="up" />
              </button>
            )}
          </div>
        )}
      </div>

      <div>
        <button
          onClick={handleRegenerate}
          disabled={regenerating}
          className="bg-primary text-white px-4 py-2 text-sm font-medium rounded-neu-md shadow-neu-raised-sm hover:shadow-neu-hover active:shadow-neu-inset-sm disabled:opacity-50 transition-shadow"
        >
          {regenerating ? "Regenerating…" : "Regenerate test keys"}
        </button>
        <p className="text-xs text-secondary mt-2">
          This revokes your current test keys immediately and issues a new pair.
        </p>
      </div>
    </div>
  );
}