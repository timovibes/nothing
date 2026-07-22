/*
Admin KYC review queue — lists merchants by kyc_status (defaulting to under_review, the
actionable queue) and lets an admin approve or reject directly, using the existing
POST /admin/merchants/{id}/verify endpoint.
*/

import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import { formatDate } from "../../lib/format";
import type { MerchantProfile } from "../../types";

const FILTERS = [
  { label: "Under review", value: "under_review" },
  { label: "Pending", value: "pending" },
  { label: "Approved", value: "approved" },
  { label: "Rejected", value: "rejected" },
  { label: "All", value: "" },
];

export function AdminMerchantsPage() {
  const [filter, setFilter] = useState("under_review");
  const [merchants, setMerchants] = useState<MerchantProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actingOnId, setActingOnId] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState<Record<string, string>>({});

  async function loadMerchants() {
    setLoading(true);
    try {
      const response = await api.get("/api/v1/admin/merchants", {
        params: filter ? { kyc_status: filter } : {},
      });
      setMerchants(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Failed to load merchants");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadMerchants();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter]);

  async function handleDecision(merchantId: string, approved: boolean) {
    setActingOnId(merchantId);
    try {
      await api.post(`/api/v1/admin/merchants/${merchantId}/verify`, {
        approved,
        reason: approved ? null : rejectReason[merchantId] || "Did not meet verification requirements",
      });
      await loadMerchants();
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Failed to record decision");
    } finally {
      setActingOnId(null);
    }
  }

  return (
    <div className="max-w-3xl">
      <p className="text-xs uppercase tracking-wide text-secondary mb-2">Merchant KYC</p>
      <p className="text-secondary text-sm mb-6">
        Review and approve or reject merchant verification submissions.
      </p>

      <div className="flex gap-2 mb-8">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            className={`text-xs uppercase tracking-wide px-3 py-1.5 border ${
              filter === f.value ? "border-primary text-primary" : "border-border text-secondary"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {loading ? (
        <p className="text-secondary text-sm">Loading…</p>
      ) : error ? (
        <p className="text-error text-sm">{error}</p>
      ) : merchants.length === 0 ? (
        <p className="text-secondary text-sm">No merchants in this state.</p>
      ) : (
        <div>
          {merchants.map((merchant, index) => (
            <div key={merchant.id}>
              <div className="py-4">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <p className="text-sm font-medium">{merchant.business_name}</p>
                    <p className="font-mono text-xs text-secondary">{merchant.business_email}</p>
                  </div>
                  <span className="text-xs text-secondary font-mono">{formatDate(merchant.created_at)}</span>
                </div>

                <div className="grid grid-cols-2 gap-y-1 text-sm mb-3">
                  <span className="text-secondary">Bank</span>
                  <span>{merchant.settlement_bank_name ?? "—"}</span>
                  <span className="text-secondary">Account number</span>
                  <span className="font-mono text-xs">{merchant.settlement_account_number ?? "—"}</span>
                  <span className="text-secondary">Account name</span>
                  <span>{merchant.settlement_account_name ?? "—"}</span>
                </div>

                {merchant.kyc_status === "under_review" && (
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => handleDecision(merchant.id, true)}
                      disabled={actingOnId === merchant.id}
                      className="text-white px-3 py-1.5 text-xs uppercase tracking-wide disabled:opacity-50"
                      style={{ backgroundColor: "#1E7A46" }}
                    >
                      Approve
                    </button>
                    <input
                      type="text"
                      placeholder="Rejection reason (optional)"
                      value={rejectReason[merchant.id] ?? ""}
                      onChange={(e) => setRejectReason((prev) => ({ ...prev, [merchant.id]: e.target.value }))}
                      className="border border-border px-2 py-1.5 text-xs flex-1 focus:outline-none focus:border-primary"
                    />
                    <button
                      onClick={() => handleDecision(merchant.id, false)}
                      disabled={actingOnId === merchant.id}
                      className="text-white px-3 py-1.5 text-xs uppercase tracking-wide disabled:opacity-50"
                      style={{ backgroundColor: "#FF5449" }}
                    >
                      Reject
                    </button>
                  </div>
                )}
              </div>
              {index < merchants.length - 1 && <hr className="ledger-divider" />}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}