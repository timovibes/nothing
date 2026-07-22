/*
Maintenance windows — scheduled downtime records, also shown publicly on the status page.
*/

import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import { formatDate } from "../../lib/format";
import type { MaintenanceWindow } from "../../types";

export function AdminMaintenancePage() {
  const [windows, setWindows] = useState<MaintenanceWindow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [startsAt, setStartsAt] = useState("");
  const [endsAt, setEndsAt] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  async function loadWindows() {
    setLoading(true);
    try {
      const response = await api.get("/api/v1/admin/maintenance-windows");
      setWindows(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Failed to load maintenance windows");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadWindows();
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setSaveError(null);
    try {
      await api.post("/api/v1/admin/maintenance-windows", {
        title,
        description: description.trim() || null,
        starts_at: new Date(startsAt).toISOString(),
        ends_at: new Date(endsAt).toISOString(),
      });
      setTitle("");
      setDescription("");
      setStartsAt("");
      setEndsAt("");
      await loadWindows();
    } catch (err: any) {
      setSaveError(err.response?.data?.detail ?? "Failed to create maintenance window");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <p className="text-secondary text-sm">Loading…</p>;
  if (error) return <p className="text-error text-sm">{error}</p>;

  return (
    <div className="max-w-3xl">
      <p className="text-xs uppercase tracking-wide text-secondary mb-2">Maintenance Windows</p>
      <p className="text-secondary text-sm mb-8">
        Scheduled downtime, also shown on the public status page.
      </p>

      <form onSubmit={handleSubmit} className="border border-border p-5 mb-8 flex flex-col gap-4">
        <div>
          <label className="text-xs uppercase tracking-wide text-secondary block mb-1">Title</label>
          <input
            type="text"
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full border border-border px-3 py-2 text-sm focus:outline-none focus:border-primary"
          />
        </div>
        <div className="flex gap-3">
          <div className="flex-1">
            <label className="text-xs uppercase tracking-wide text-secondary block mb-1">Starts at</label>
            <input
              type="datetime-local"
              required
              value={startsAt}
              onChange={(e) => setStartsAt(e.target.value)}
              className="w-full border border-border px-3 py-2 text-sm font-mono focus:outline-none focus:border-primary"
            />
          </div>
          <div className="flex-1">
            <label className="text-xs uppercase tracking-wide text-secondary block mb-1">Ends at</label>
            <input
              type="datetime-local"
              required
              value={endsAt}
              onChange={(e) => setEndsAt(e.target.value)}
              className="w-full border border-border px-3 py-2 text-sm font-mono focus:outline-none focus:border-primary"
            />
          </div>
        </div>
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
          {saving ? "Creating…" : "Schedule window"}
        </button>
      </form>

      {windows.length === 0 ? (
        <p className="text-secondary text-sm">No maintenance windows scheduled.</p>
      ) : (
        <div>
          {windows.map((w, index) => (
            <div key={w.id}>
              <div className="py-3">
                <p className="text-sm font-medium">{w.title}</p>
                <p className="text-xs text-secondary font-mono mt-0.5">
                  {formatDate(w.starts_at)} → {formatDate(w.ends_at)}
                </p>
                {w.description && <p className="text-sm text-secondary mt-1">{w.description}</p>}
              </div>
              {index < windows.length - 1 && <hr className="ledger-divider" />}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}