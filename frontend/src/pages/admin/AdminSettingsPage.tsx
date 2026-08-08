/*
Global platform settings — key/value pairs (JSON value) with description, editable via
PUT /admin/settings (upserts by key).
*/

import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import { formatDate } from "../../lib/format";
import type { SystemSetting } from "../../types";

export function AdminSettingsPage() {
  const [settings, setSettings] = useState<SystemSetting[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [key, setKey] = useState("");
  const [valueJson, setValueJson] = useState("");
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  async function loadSettings() {
    setLoading(true);
    try {
      const response = await api.get("/api/v1/admin/settings");
      setSettings(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Failed to load settings");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadSettings();
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setSaveError(null);
    try {
      let parsedValue: Record<string, unknown>;
      try {
        parsedValue = JSON.parse(valueJson);
      } catch {
        setSaveError("Value must be valid JSON, e.g. {\"enabled\": true}");
        setSaving(false);
        return;
      }
      await api.put("/api/v1/admin/settings", {
        key,
        value: parsedValue,
        description: description.trim() || null,
      });
      setKey("");
      setValueJson("");
      setDescription("");
      await loadSettings();
    } catch (err: any) {
      setSaveError(err.response?.data?.detail ?? "Failed to save setting");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <p className="text-secondary text-sm">Loading…</p>;
  if (error) return <p className="text-error text-sm">{error}</p>;

  return (
    <div className="max-w-3xl flex flex-col gap-6">
      <div>
        <p className="text-xs uppercase tracking-wide text-secondary mb-2">System Settings</p>
        <p className="text-secondary text-sm">
          Global platform configuration — fee defaults, feature toggles, and similar.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="rounded-neu-lg shadow-neu-raised-sm bg-surface p-6 flex flex-col gap-4">
        <div>
          <label className="text-xs uppercase tracking-wide text-secondary block mb-1">Key</label>
          <input
            type="text"
            required
            value={key}
            onChange={(e) => setKey(e.target.value)}
            placeholder="e.g. default_settlement_delay_days"
            className="w-full bg-surface px-3 py-2 text-sm font-mono rounded-neu-sm shadow-neu-inset-sm border-none focus:outline-none focus:shadow-neu-inset"
          />
        </div>
        <div>
          <label className="text-xs uppercase tracking-wide text-secondary block mb-1">Value (JSON)</label>
          <input
            type="text"
            required
            value={valueJson}
            onChange={(e) => setValueJson(e.target.value)}
            placeholder='e.g. {"days": 2}'
            className="w-full bg-surface px-3 py-2 text-sm font-mono rounded-neu-sm shadow-neu-inset-sm border-none focus:outline-none focus:shadow-neu-inset"
          />
        </div>
        <div>
          <label className="text-xs uppercase tracking-wide text-secondary block mb-1">Description</label>
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full bg-surface px-3 py-2 text-sm rounded-neu-sm shadow-neu-inset-sm border-none focus:outline-none focus:shadow-neu-inset"
          />
        </div>
        {saveError && <p className="text-error text-sm">{saveError}</p>}
        <button
          type="submit"
          disabled={saving}
          className="bg-primary text-white px-4 py-2 text-sm font-medium rounded-neu-md shadow-neu-raised-sm hover:shadow-neu-hover active:shadow-neu-inset-sm disabled:opacity-50 self-start transition-shadow"
        >
          {saving ? "Saving…" : "Save setting"}
        </button>
      </form>

      {settings.length === 0 ? (
        <p className="text-secondary text-sm">No settings configured yet.</p>
      ) : (
        <div className="rounded-neu-lg shadow-neu-raised-sm bg-surface p-6">
          {settings.map((setting, index) => (
            <div key={setting.id}>
              <div className="py-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-mono text-sm">{setting.key}</span>
                  <span className="text-xs text-secondary font-mono">{formatDate(setting.updated_at)}</span>
                </div>
                <pre className="font-mono text-xs text-secondary rounded-neu-sm shadow-neu-inset-sm px-2 py-1 inline-block">
                  {JSON.stringify(setting.value)}
                </pre>
                {setting.description && <p className="text-xs text-secondary mt-1">{setting.description}</p>}
              </div>
              {index < settings.length - 1 && <hr className="ledger-divider" />}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}