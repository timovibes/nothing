/*collects business details and creates the merchant via our already-JWT-authenticated POST
/api/v1/merchants endpoint (built back in Module 3), then sends the user straight to their new
Overview page.*/

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";

export function OnboardingPage() {
  const navigate = useNavigate();
  const [businessName, setBusinessName] = useState("");
  const [businessEmail, setBusinessEmail] = useState("");
  const [country, setCountry] = useState("KE");
  const [currency, setCurrency] = useState("KES");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await api.post("/api/v1/merchants", {
        business_name: businessName,
        business_email: businessEmail,
        country,
        default_currency: currency,
      });
      navigate("/");
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Something went wrong. Try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface px-4">
      <div className="w-full max-w-sm">
        <h1 className="font-display font-bold text-2xl mb-1">Set up your business</h1>
        <p className="text-secondary text-sm mb-8">
          You can start testing right away — no need to verify anything first.
        </p>

        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="block text-xs uppercase tracking-wide text-secondary mb-1">
              Business name
            </label>
            <input
              type="text"
              required
              value={businessName}
              onChange={(e) => setBusinessName(e.target.value)}
              className="w-full border border-primary px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div>
            <label className="block text-xs uppercase tracking-wide text-secondary mb-1">
              Business email
            </label>
            <input
              type="email"
              required
              value={businessEmail}
              onChange={(e) => setBusinessEmail(e.target.value)}
              className="w-full border border-primary px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs uppercase tracking-wide text-secondary mb-1">
                Country
              </label>
              <input
                type="text"
                required
                maxLength={2}
                value={country}
                onChange={(e) => setCountry(e.target.value.toUpperCase())}
                className="w-full border border-primary px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <div>
              <label className="block text-xs uppercase tracking-wide text-secondary mb-1">
                Currency
              </label>
              <input
                type="text"
                required
                maxLength={3}
                value={currency}
                onChange={(e) => setCurrency(e.target.value.toUpperCase())}
                className="w-full border border-primary px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>
          {error && <p className="text-error text-sm">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary text-white py-2 text-sm font-medium disabled:opacity-50"
          >
            {loading ? "Creating…" : "Create business"}
          </button>
        </form>
      </div>
    </div>
  );
}