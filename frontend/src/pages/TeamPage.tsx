/*
Team page — replaces the StubPage. Lets a merchant_owner invite staff by email (they receive
a link to set their own password and activate the account), view current staff, and remove
them. Only visible/functional for owners — staff themselves get a 403 from the backend if
they try these actions, enforced in TeamService, not just hidden in the UI.
*/

import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { formatDate } from "../lib/format";
import { getCurrentRole } from "../lib/jwt";
import type { StaffMember } from "../types";

export function TeamPage() {
  const isOwner = getCurrentRole() === "merchant_owner";
  const [staff, setStaff] = useState<StaffMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showForm, setShowForm] = useState(false);
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [inviting, setInviting] = useState(false);
  const [inviteError, setInviteError] = useState<string | null>(null);
  const [inviteSent, setInviteSent] = useState(false);

  const [removingId, setRemovingId] = useState<string | null>(null);

  async function loadStaff() {
    setLoading(true);
    try {
      const response = await api.get("/api/v1/merchants/me/staff");
      setStaff(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Failed to load team");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (isOwner) loadStaff();
    else setLoading(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleInvite(e: React.FormEvent) {
    e.preventDefault();
    setInviting(true);
    setInviteError(null);
    setInviteSent(false);
    try {
      await api.post("/api/v1/merchants/me/staff/invite", { email, full_name: fullName });
      setInviteSent(true);
      setEmail("");
      setFullName("");
      await loadStaff();
    } catch (err: any) {
      setInviteError(err.response?.data?.detail ?? "Failed to send invite");
    } finally {
      setInviting(false);
    }
  }

  async function handleRemove(staffId: string) {
    setRemovingId(staffId);
    try {
      await api.delete(`/api/v1/merchants/me/staff/${staffId}`);
      await loadStaff();
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Failed to remove staff member");
    } finally {
      setRemovingId(null);
    }
  }

  if (!isOwner) {
    return (
      <div className="max-w-2xl">
        <p className="text-xs uppercase tracking-wide text-secondary mb-2">Team</p>
        <p className="text-secondary text-sm">Only the account owner can manage team members.</p>
      </div>
    );
  }

  if (loading) return <p className="text-secondary text-sm">Loading…</p>;
  if (error) return <p className="text-error text-sm">{error}</p>;

  return (
    <div className="max-w-2xl">
      <div className="flex items-start justify-between mb-8">
        <div>
          <p className="text-xs uppercase tracking-wide text-secondary mb-2">Team</p>
          <p className="text-secondary text-sm">Invite staff to help manage your account.</p>
        </div>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="bg-primary text-white px-4 py-2 text-sm font-medium shrink-0"
        >
          {showForm ? "Cancel" : "Invite staff"}
        </button>
      </div>

      {inviteSent && (
        <p className="text-sm mb-4" style={{ color: "#1E7A46" }}>
          Invite sent. They'll receive an email with a link to set their password.
        </p>
      )}

      {showForm && (
        <form onSubmit={handleInvite} className="border border-border p-5 mb-8 flex flex-col gap-4">
          <div>
            <label className="text-xs uppercase tracking-wide text-secondary block mb-1">Full name</label>
            <input
              type="text"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full border border-border px-3 py-2 text-sm focus:outline-none focus:border-primary"
            />
          </div>
          <div>
            <label className="text-xs uppercase tracking-wide text-secondary block mb-1">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full border border-border px-3 py-2 text-sm font-mono focus:outline-none focus:border-primary"
            />
          </div>
          {inviteError && <p className="text-error text-sm">{inviteError}</p>}
          <button
            type="submit"
            disabled={inviting}
            className="bg-primary text-white px-4 py-2 text-sm font-medium disabled:opacity-50 self-start"
          >
            {inviting ? "Sending…" : "Send invite"}
          </button>
        </form>
      )}

      {staff.length === 0 ? (
        <p className="text-secondary text-sm">No staff members yet.</p>
      ) : (
        <div>
          {staff.map((member, index) => (
            <div key={member.id}>
              <div className="flex items-center justify-between py-3">
                <div>
                  <p className="text-sm">{member.full_name}</p>
                  <p className="font-mono text-xs text-secondary mt-0.5">{member.email}</p>
                </div>
                <div className="flex items-center gap-4">
                  <span
                    className="font-mono text-[11px] uppercase tracking-wider px-2 py-0.5 border"
                    style={{
                      color: member.is_active ? "#1E7A46" : "#919191",
                      borderColor: member.is_active ? "#1E7A46" : "#919191",
                    }}
                  >
                    {member.is_active ? "active" : "pending"}
                  </span>
                  <span className="text-xs text-secondary font-mono">{formatDate(member.created_at)}</span>
                  <button
                    onClick={() => handleRemove(member.id)}
                    disabled={removingId === member.id}
                    className="text-xs uppercase tracking-wide text-error disabled:opacity-50"
                  >
                    Remove
                  </button>
                </div>
              </div>
              {index < staff.length - 1 && <hr className="ledger-divider" />}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}