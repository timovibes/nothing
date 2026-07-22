/*
Settings page — replaces the StubPage. Resolves the previously-undecided Settings scope:
business profile (read-only), settlement bank details (editable), KYC submission and status,
and live API key issuance once approved. All backed by existing, already-working merchant
routes (PUT /me/settlement-details, POST /me/submit-kyc, POST /me/live-keys) — this page was
the only missing piece; every one of these has been curl-tested already.
*/

import { useEffect, useState } from "react";
import { api } from "../lib/api";
import type { MerchantProfile, LiveApiKeyCreated } from "../types";

const KYC_LABELS: Record<MerchantProfile["kyc_status"], string> = {
  pending: "Not submitted",
  under_review: "Under review",
  approved: "Approved",
  rejected: "Rejected",
};

const KYC_COLORS: Record<MerchantProfile["kyc_status"], string> = {
  pending: "#919191",
  under_review: "#919191",
  approved: "#1E7A46",
  rejected: "#FF5449",
};

export function SettingsPage() {
  const [merchant, setMerchant] = useState<MerchantProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [bankName, setBankName] = useState("");
  const [accountNumber, setAccountNumber] = useState("");
  const [accountName, setAccountName] = useState("");
  const [savingBankDetails, setSavingBankDetails] = useState(false);
  const [bankError, setBankError] = useState<string | null>(null);
  const [bankSaved, setBankSaved] = useState(false);

  const [submittingKyc, setSubmittingKyc] = useState(false);
  const [kycError, setKycError] = useState<string | null>(null);

  const [issuingLiveKeys, setIssuingLiveKeys] = useState(false);
  const [liveKeysError, setLiveKeysError] = useState<string | null>(null);
  const [revealedLiveKeys, setRevealedLiveKeys] = useState<LiveApiKeyCreated[] | null>(null);

  async function loadMerchant() {
    setLoading(true);
    try {
      const response = await api.get<MerchantProfile>("/api/v1/merchants/me");
      setMerchant(response.data);
      setBankName(response.data.settlement_bank_name ?? "");
      setAccountNumber(response.data.settlement_account_number ?? "");
      setAccountName(response.data.settlement_account_name ?? "");
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Failed to load merchant profile");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadMerchant();
  }, []);

  async function handleSaveBankDetails(e: React.FormEvent) {
    e.preventDefault();
    setSavingBankDetails(true);
    setBankError(null);
    setBankSaved(false);
    try {
      const response = await api.put<MerchantProfile>("/api/v1/merchants/me/settlement-details", {
        settlement_bank_name: bankName,
        settlement_account_number: accountNumber,
        settlement_account_name: accountName,
      });
      setMerchant(response.data);
      setBankSaved(true);
    } catch (err: any) {
      setBankError(err.response?.data?.detail ?? "Failed to save settlement details");
    } finally {
      setSavingBankDetails(false);
    }
  }

  async function handleSubmitKyc() {
    setSubmittingKyc(true);
    setKycError(null);
    try {
      const response = await api.post<MerchantProfile>("/api/v1/merchants/me/submit-kyc");
      setMerchant(response.data);
    } catch (err: any) {
      setKycError(err.response?.data?.detail ?? "Failed to submit for review");
    } finally {
      setSubmittingKyc(false);
    }
  }

  async function handleIssueLiveKeys() {
    setIssuingLiveKeys(true);
    setLiveKeysError(null);
    try {
      const response = await api.post<LiveApiKeyCreated[]>("/api/v1/merchants/me/live-keys");
      setRevealedLiveKeys(response.data);
    } catch (err: any) {
      setLiveKeysError(err.response?.data?.detail ?? "Failed to issue live keys");
    } finally {
      setIssuingLiveKeys(false);
    }
  }

  function copyToClipboard(text: string) {
    navigator.clipboard.writeText(text);
  }

  if (loading) return <p className="text-secondary text-sm">Loading…</p>;
  if (error) return <p className="text-error text-sm">{error}</p>;
  if (!merchant) return null;

  const hasBankDetails =
    !!merchant.settlement_bank_name &&
    !!merchant.settlement_account_number &&
    !!merchant.settlement_account_name;

  return (
    <div className="max-w-2xl">
      <p className="text-xs uppercase tracking-wide text-secondary mb-2">Settings</p>
      <p className="text-secondary text-sm mb-8">
        Your business profile, settlement details, and verification status.
      </p>

      {/* Business profile */}
      <section className="mb-8">
        <p className="text-xs uppercase tracking-wide text-secondary mb-3">Business profile</p>
        <div className="grid grid-cols-2 gap-y-2 text-sm">
          <span className="text-secondary">Business name</span>
          <span>{merchant.business_name}</span>
          <span className="text-secondary">Business email</span>
          <span className="font-mono text-xs">{merchant.business_email}</span>
          <span className="text-secondary">Country</span>
          <span className="font-mono">{merchant.country}</span>
          <span className="text-secondary">Default currency</span>
          <span className="font-mono">{merchant.default_currency}</span>
        </div>
      </section>

      <hr className="ledger-divider mb-8" />

      {/* KYC status */}
      <section className="mb-8">
        <p className="text-xs uppercase tracking-wide text-secondary mb-3">Verification status</p>
        <span
          className="inline-block font-mono text-[11px] uppercase tracking-wider px-2 py-0.5 mb-2"
          style={{ color: KYC_COLORS[merchant.kyc_status], border: `1px solid ${KYC_COLORS[merchant.kyc_status]}` }}
        >
          {KYC_LABELS[merchant.kyc_status]}
        </span>
        {merchant.kyc_status === "rejected" && merchant.kyc_rejection_reason && (
          <p className="text-error text-sm mt-2">{merchant.kyc_rejection_reason}</p>
        )}
        {merchant.kyc_status === "approved" && (
          <p className="text-sm text-secondary mt-2">
            Live mode is enabled. You can issue live API keys below.
          </p>
        )}
        {(merchant.kyc_status === "pending" || merchant.kyc_status === "rejected") && (
          <div className="mt-3">
            <button
              onClick={handleSubmitKyc}
              disabled={submittingKyc || !hasBankDetails}
              className="bg-primary text-white px-4 py-2 text-sm font-medium disabled:opacity-50"
            >
              {submittingKyc ? "Submitting…" : "Submit for review"}
            </button>
            {!hasBankDetails && (
              <p className="text-xs text-secondary mt-2">
                Add your settlement bank details below before submitting.
              </p>
            )}
            {kycError && <p className="text-error text-sm mt-2">{kycError}</p>}
          </div>
        )}
      </section>

      <hr className="ledger-divider mb-8" />

      {/* Settlement bank details */}
      <section className="mb-8">
        <p className="text-xs uppercase tracking-wide text-secondary mb-3">Settlement bank details</p>
        <p className="text-secondary text-sm mb-4">
          Where your available balance is paid out to, automatically, T+2 days after settlement.
        </p>
        <form onSubmit={handleSaveBankDetails} className="flex flex-col gap-4">
          <div>
            <label className="text-xs uppercase tracking-wide text-secondary block mb-1">Bank name</label>
            <input
              type="text"
              required
              value={bankName}
              onChange={(e) => setBankName(e.target.value)}
              className="w-full border border-border px-3 py-2 text-sm focus:outline-none focus:border-primary"
            />
          </div>
          <div>
            <label className="text-xs uppercase tracking-wide text-secondary block mb-1">Account number</label>
            <input
              type="text"
              required
              value={accountNumber}
              onChange={(e) => setAccountNumber(e.target.value)}
              className="w-full border border-border px-3 py-2 text-sm font-mono focus:outline-none focus:border-primary"
            />
          </div>
          <div>
            <label className="text-xs uppercase tracking-wide text-secondary block mb-1">Account name</label>
            <input
              type="text"
              required
              value={accountName}
              onChange={(e) => setAccountName(e.target.value)}
              className="w-full border border-border px-3 py-2 text-sm focus:outline-none focus:border-primary"
            />
          </div>
          {bankError && <p className="text-error text-sm">{bankError}</p>}
          {bankSaved && <p className="text-sm" style={{ color: "#1E7A46" }}>Saved.</p>}
          <button
            type="submit"
            disabled={savingBankDetails}
            className="bg-primary text-white px-4 py-2 text-sm font-medium disabled:opacity-50 self-start"
          >
            {savingBankDetails ? "Saving…" : "Save bank details"}
          </button>
        </form>
      </section>

      {/* Live API keys */}
      {merchant.is_live_mode_enabled && (
        <>
          <hr className="ledger-divider mb-8" />
          <section>
            <p className="text-xs uppercase tracking-wide text-secondary mb-3">Live API keys</p>
            <p className="text-secondary text-sm mb-4">
              Issue your live key pair. Manage them alongside your test keys on the API Keys page.
            </p>

            {revealedLiveKeys && (
              <div className="border border-primary p-4 mb-4">
                <p className="font-mono text-[11px] uppercase tracking-wider text-error mb-3">
                  Save these now — the secret key will not be shown again
                </p>
                {revealedLiveKeys.map((key) => (
                  <div key={key.id} className="flex items-center justify-between py-2 border-t border-border first:border-t-0">
                    <div>
                      <p className="text-xs text-secondary uppercase">{key.key_type}</p>
                      <p className="font-mono text-sm break-all">{key.raw_key}</p>
                    </div>
                    <button
                      onClick={() => copyToClipboard(key.raw_key)}
                      className="text-xs uppercase tracking-wide border border-primary px-2 py-1 shrink-0 ml-4"
                    >
                      Copy
                    </button>
                  </div>
                ))}
              </div>
            )}

            {liveKeysError && <p className="text-error text-sm mb-3">{liveKeysError}</p>}

            <button
              onClick={handleIssueLiveKeys}
              disabled={issuingLiveKeys}
              className="bg-primary text-white px-4 py-2 text-sm font-medium disabled:opacity-50"
            >
              {issuingLiveKeys ? "Issuing…" : "Issue live keys"}
            </button>
          </section>
        </>
      )}
    </div>
  );
}