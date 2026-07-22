/*
Customers page — replaces the StubPage. Lists every customer for this merchant and lets the
merchant create new customer records directly (JWT-authenticated), same data CustomerService
already handles for guest-checkout customers created via sk_test.
*/

import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { formatDate } from "../lib/format";

interface Customer {
  id: string;
  email: string | null;
  full_name: string | null;
  phone: string | null;
  created_at: string;
}

export function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showForm, setShowForm] = useState(false);
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  async function loadCustomers() {
    setLoading(true);
    try {
      const response = await api.get("/api/v1/dashboard/customers");
      setCustomers(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Failed to load customers");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadCustomers();
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setFormError(null);
    try {
      await api.post("/api/v1/dashboard/customers", {
        email: email.trim() || null,
        full_name: fullName.trim() || null,
        phone: phone.trim() || null,
      });
      setShowForm(false);
      setEmail("");
      setFullName("");
      setPhone("");
      await loadCustomers();
    } catch (err: any) {
      setFormError(err.response?.data?.detail ?? "Failed to create customer");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <p className="text-secondary text-sm">Loading…</p>;
  if (error) return <p className="text-error text-sm">{error}</p>;

  return (
    <div className="max-w-3xl">
      <div className="flex items-start justify-between mb-8">
        <div>
          <p className="text-xs uppercase tracking-wide text-secondary mb-2">Customers</p>
          <p className="text-secondary text-sm">Everyone who has paid you, guest or registered.</p>
        </div>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="bg-primary text-white px-4 py-2 text-sm font-medium shrink-0"
        >
          {showForm ? "Cancel" : "Add customer"}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="border border-border p-5 mb-8 flex flex-col gap-4">
          <div>
            <label className="text-xs uppercase tracking-wide text-secondary block mb-1">Full name</label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full border border-border px-3 py-2 text-sm focus:outline-none focus:border-primary"
            />
          </div>
          <div>
            <label className="text-xs uppercase tracking-wide text-secondary block mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full border border-border px-3 py-2 text-sm font-mono focus:outline-none focus:border-primary"
            />
          </div>
          <div>
            <label className="text-xs uppercase tracking-wide text-secondary block mb-1">Phone</label>
            <input
              type="text"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+254700000000"
              className="w-full border border-border px-3 py-2 text-sm font-mono focus:outline-none focus:border-primary"
            />
          </div>
          {formError && <p className="text-error text-sm">{formError}</p>}
          <button
            type="submit"
            disabled={submitting}
            className="bg-primary text-white px-4 py-2 text-sm font-medium disabled:opacity-50 self-start"
          >
            {submitting ? "Saving…" : "Create customer"}
          </button>
        </form>
      )}

      {customers.length === 0 ? (
        <p className="text-secondary text-sm">No customers yet.</p>
      ) : (
        <div>
          {customers.map((customer, index) => (
            <div key={customer.id}>
              <div className="flex items-center justify-between py-3">
                <div>
                  <p className="text-sm">
                    {customer.full_name ?? <span className="text-secondary">No name on file</span>}
                  </p>
                  <p className="font-mono text-xs text-secondary mt-0.5">
                    {customer.email ?? "no email"}
                    {customer.phone ? ` · ${customer.phone}` : ""}
                  </p>
                </div>
                <span className="text-xs text-secondary font-mono">{formatDate(customer.created_at)}</span>
              </div>
              {index < customers.length - 1 && <hr className="ledger-divider" />}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}