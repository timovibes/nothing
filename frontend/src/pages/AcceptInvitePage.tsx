/*
Public page where an invited staff member sets their password to activate their account.
No JWT, no ProtectedRoute — reached via the link emailed by TeamService.invite_staff.
*/

import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../lib/api";

export function AcceptInvitePage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") ?? "";

  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await api.post("/api/v1/auth/accept-invite", { token, password });
      setSuccess(true);
      setTimeout(() => navigate("/login"), 2000);
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "This invite link is invalid or has expired");
    } finally {
      setSubmitting(false);
    }
  }

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface px-6">
        <p className="text-error text-sm">This invite link is missing a token.</p>
      </div>
    );
  }

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface px-6">
        <p className="text-sm" style={{ color: "#1E7A46" }}>
          Account activated. Redirecting to login…
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center px-6">
      <form onSubmit={handleSubmit} className="w-full max-w-sm flex flex-col gap-4">
        <p className="font-display font-bold text-lg mb-2">nothing</p>
        <p className="text-sm text-secondary mb-4">Set a password to activate your account.</p>
        <div>
          <label className="text-xs uppercase tracking-wide text-secondary block mb-1">Password</label>
          <input
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full border border-border px-3 py-2 text-sm focus:outline-none focus:border-primary"
          />
        </div>
        {error && <p className="text-error text-sm">{error}</p>}
        <button
          type="submit"
          disabled={submitting}
          className="bg-primary text-white px-4 py-3 text-sm font-medium disabled:opacity-50"
        >
          {submitting ? "Activating…" : "Activate account"}
        </button>
      </form>
    </div>
  );
}