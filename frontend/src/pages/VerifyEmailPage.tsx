/*the one-time email verification screen — reads the email from the URL (passed by Signup),
submits the 6-digit code, then sends the user to Login (since verification alone doesn't issue
a session).*/

import { useState } from "react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { api } from "../lib/api";

export function VerifyEmailPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const email = searchParams.get("email") ?? "";

  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleVerify(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await api.post("/api/v1/auth/verify-email", { email, code });
      navigate("/login");
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Incorrect code. Try again.");
    } finally {
      setLoading(false);
    }
  }

  async function handleResend() {
    setError(null);
    setInfo(null);
    try {
      await api.post("/api/v1/auth/resend-verification", { email });
      setInfo("A new code has been sent.");
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Could not resend code.");
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface px-4">
      <div className="w-full max-w-sm">
        <h1 className="font-display font-bold text-2xl mb-1">nothing</h1>
        <p className="text-secondary text-sm mb-8">
          Enter the 6-digit code we sent to <span className="text-primary">{email}</span>
        </p>

        <form onSubmit={handleVerify} className="space-y-4">
          <input
            type="text"
            required
            maxLength={6}
            value={code}
            onChange={(e) => setCode(e.target.value)}
            className="w-full border border-primary px-3 py-2 text-sm font-mono tracking-widest focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="000000"
          />
          {error && <p className="text-error text-sm">{error}</p>}
          {info && <p className="text-success text-sm">{info}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary text-white py-2 text-sm font-medium disabled:opacity-50"
          >
            {loading ? "Verifying…" : "Verify email"}
          </button>
        </form>

        <div className="flex justify-between mt-6 text-sm">
          <button onClick={handleResend} className="text-secondary underline">
            Resend code
          </button>
          <Link to="/login" className="text-secondary underline">
            Back to sign in
          </Link>
        </div>
      </div>
    </div>
  );
}