/*
Admin fraud case review queue — every pending fraud_case (payment intents held for manual
review by FraudService's risk scoring) with an approve/reject decision that flows straight
through to PaymentService.continue_after_fraud_review via the existing decide endpoint.
*/

import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import { formatDate, shortId } from "../../lib/format";
import type { FraudCase } from "../../types";

export function AdminFraudPage() {
  const [cases, setCases] = useState<FraudCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actingOnId, setActingOnId] = useState<string | null>(null);

  async function loadCases() {
    setLoading(true);
    try {
      const response = await api.get("/api/v1/fraud/cases/pending");
      setCases(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Failed to load fraud cases");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadCases();
  }, []);

  async function handleDecision(caseId: string, approved: boolean) {
    setActingOnId(caseId);
    try {
      await api.post(`/api/v1/fraud/cases/${caseId}/decide`, { approved });
      await loadCases();
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Failed to record decision");
    } finally {
      setActingOnId(null);
    }
  }

  if (loading) return <p className="text-secondary text-sm">Loading…</p>;
  if (error) return <p className="text-error text-sm">{error}</p>;

  return (
    <div className="max-w-3xl">
      <p className="text-xs uppercase tracking-wide text-secondary mb-2">Fraud Review</p>
      <p className="text-secondary text-sm mb-8">
        Payments held for manual review before authorization is allowed to proceed.
      </p>

      {cases.length === 0 ? (
        <p className="text-secondary text-sm">No pending fraud cases.</p>
      ) : (
        <div>
          {cases.map((fraudCase, index) => (
            <div key={fraudCase.id}>
              <div className="flex items-center justify-between py-4">
                <div>
                  <div className="flex items-center gap-3 mb-1">
                    <span className="font-mono text-sm">{shortId(fraudCase.payment_intent_id)}</span>
                    <span
                      className="font-mono text-[11px] uppercase tracking-wider px-2 py-0.5 border"
                      style={{ color: "#FF5449", borderColor: "#FF5449" }}
                    >
                      Risk score {fraudCase.risk_score}
                    </span>
                  </div>
                  <p className="text-xs text-secondary font-mono">{formatDate(fraudCase.created_at)}</p>
                </div>
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => handleDecision(fraudCase.id, true)}
                    disabled={actingOnId === fraudCase.id}
                    className="text-white px-3 py-1.5 text-xs uppercase tracking-wide disabled:opacity-50"
                    style={{ backgroundColor: "#1E7A46" }}
                  >
                    Approve
                  </button>
                  <button
                    onClick={() => handleDecision(fraudCase.id, false)}
                    disabled={actingOnId === fraudCase.id}
                    className="text-white px-3 py-1.5 text-xs uppercase tracking-wide disabled:opacity-50"
                    style={{ backgroundColor: "#FF5449" }}
                  >
                    Reject
                  </button>
                </div>
              </div>
              {index < cases.length - 1 && <hr className="ledger-divider" />}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}