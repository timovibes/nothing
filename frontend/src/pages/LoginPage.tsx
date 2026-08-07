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
import { EyeIcon } from "../components/EyeIcon";

export function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
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
      <div className="w-full max-w-sm rounded-neu-lg shadow-neu-raised bg-surface p-8">
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
              className="w-full bg-surface px-3 py-2 text-sm rounded-neu-sm shadow-neu-inset-sm border-none focus:outline-none focus:shadow-neu-inset"
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
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-surface px-3 py-2 pr-10 text-sm rounded-neu-sm shadow-neu-inset-sm border-none focus:outline-none focus:shadow-neu-inset"
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                aria-label={showPassword ? "Hide password" : "Show password"}
                className="absolute inset-y-0 right-0 flex items-center px-3 text-secondary rounded-neu-sm hover:shadow-neu-raised-sm transition-shadow"
              >
                <EyeIcon open={showPassword} />
              </button>
            </div>
          </div>
          {error && <p className="text-error text-sm">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary text-white py-2 text-sm font-medium rounded-neu-md shadow-neu-raised-sm hover:shadow-neu-hover active:shadow-neu-inset-sm disabled:opacity-50 transition-shadow"
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