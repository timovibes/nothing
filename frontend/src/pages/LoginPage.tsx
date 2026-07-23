// src/pages/LoginPage.tsx — full replace
/*
the dashboard login screen — plain email + password. After a successful login, decodes the
JWT to check role: admin accounts go straight to the Admin Portal, everyone else lands on
the normal merchant dashboard.
*/
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { decodeJwtPayload } from "../lib/jwt";

export function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const response = await api.post("/api/v1/auth/login", { email, password });
      localStorage.setItem("access_token", response.data.access_token);
      localStorage.setItem("refresh_token", response.data.refresh_token);

      const payload = decodeJwtPayload(response.data.access_token);
      if (payload?.role === "admin") {
        navigate("/admin/merchants");
      } else {
        navigate("/");
      }
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
        <p className="text-secondary text-sm mb-8">Sign in to your dashboard</p>
        <form onSubmit={handleLogin} className="space-y-4">
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
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full border border-primary px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          {error && <p className="text-error text-sm">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary text-white py-2 text-sm font-medium disabled:opacity-50"
          >
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>
        <p className="text-sm text-secondary mt-6">
          Don't have an account?{" "}
          <Link to="/signup" className="text-primary underline">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}