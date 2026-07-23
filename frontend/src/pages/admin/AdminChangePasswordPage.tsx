// src/pages/admin/AdminChangePasswordPage.tsx
/*
Lets the logged-in admin change their own password, using the existing change-password
endpoint. Requires the current password for verification, standard practice even for an
admin account.
*/
import { useState } from "react";
import { api } from "../../lib/api";

export function AdminChangePasswordPage() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(false);

    if (newPassword !== confirmPassword) {
      setError("New passwords don't match.");
      return;
    }

    setSubmitting(true);
    try {
      await api.post("/api/v1/auth/change-password", {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setSuccess(true);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Failed to change password");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-md">
      <p className="text-xs uppercase tracking-wide text-secondary mb-2">Change Password</p>
      <p className="text-secondary text-sm mb-8">Update your admin account password.</p>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div>
          <label className="text-xs uppercase tracking-wide text-secondary block mb-1">
            Current password
          </label>
          <input
            type="password"
            required
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            className="w-full border border-border px-3 py-2 text-sm focus:outline-none focus:border-primary"
          />
        </div>
        <div>
          <label className="text-xs uppercase tracking-wide text-secondary block mb-1">
            New password
          </label>
          <input
            type="password"
            required
            minLength={8}
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            className="w-full border border-border px-3 py-2 text-sm focus:outline-none focus:border-primary"
          />
        </div>
        <div>
          <label className="text-xs uppercase tracking-wide text-secondary block mb-1">
            Confirm new password
          </label>
          <input
            type="password"
            required
            minLength={8}
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            className="w-full border border-border px-3 py-2 text-sm focus:outline-none focus:border-primary"
          />
        </div>
        {error && <p className="text-error text-sm">{error}</p>}
        {success && <p className="text-sm" style={{ color: "#1E7A46" }}>Password changed successfully.</p>}
        <button
          type="submit"
          disabled={submitting}
          className="bg-primary text-white px-4 py-2 text-sm font-medium disabled:opacity-50 self-start"
        >
          {submitting ? "Saving…" : "Change password"}
        </button>
      </form>
    </div>
  );
}