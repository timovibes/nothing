/*real merchant signup — calls /auth/register, then redirects straight to the verify-email
screen with the email pre-filled, matching the actual account state (is_email_verified: false)
right after registration.*/

import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { EyeIcon } from "../components/EyeIcon";

export function SignupPage() {
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSignup(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await api.post("/api/v1/auth/register", {
        email,
        password,
        full_name: fullName,
      });
      navigate(`/verify-email?email=${encodeURIComponent(email)}`);
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Something went wrong. Try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface px-4">
      <div className="w-full max-w-sm">
        <h1 className="font-display font-bold text-2xl mb-1">nothing</h1>
        <p className="text-secondary text-sm mb-8">Create your account</p>

        <form onSubmit={handleSignup} className="space-y-4">
          <div>
            <label className="block text-xs uppercase tracking-wide text-secondary mb-1">
              Full name
            </label>
            <input
              type="text"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full border border-primary px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div>
            <label className="block text-xs uppercase tracking-wide text-secondary mb-1">
              Email
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full border border-primary px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div>
            <label className="block text-xs uppercase tracking-wide text-secondary mb-1">
              Password
            </label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full border border-primary px-3 py-2 pr-10 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                aria-label={showPassword ? "Hide password" : "Show password"}
                className="absolute inset-y-0 right-0 flex items-center px-3 text-secondary"
              >
                <EyeIcon open={showPassword} />
              </button>
            </div>
          </div>
          {error && <p className="text-error text-sm">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary text-white py-2 text-sm font-medium disabled:opacity-50"
          >
            {loading ? "Creating account…" : "Create account"}
          </button>
        </form>

        <p className="text-sm text-secondary mt-6">
          Already have an account?{" "}
          <Link to="/login" className="text-primary underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}