/*
Layout shell for the Admin Portal — mirrors DashboardLayout's structure and design language
(same sidebar pattern, now soft neumorphic panels instead of ledger-tape borders) but with
admin-specific navigation and no "Test mode" stamp, since admin actions apply platform-wide,
not per-merchant test/live mode.
*/

import { NavLink, useNavigate } from "react-router-dom";

const ADMIN_NAV_ITEMS = [
  { label: "Merchant KYC", path: "/admin/merchants" },
  { label: "Fraud Review", path: "/admin/fraud" },
  { label: "System Settings", path: "/admin/settings" },
  { label: "Feature Flags", path: "/admin/feature-flags" },
  { label: "Maintenance", path: "/admin/maintenance" },
  { label: "Reports", path: "/admin/reports" },
  { label: "Change Password", path: "/admin/change-password" }
];

export function AdminLayout({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();
  function handleLogout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    navigate("/login");
  }
  return (
    <div className="min-h-screen bg-surface font-body flex gap-6 p-6">
      <aside className="w-56 shrink-0 rounded-neu-lg shadow-neu-raised bg-surface flex flex-col justify-between">
        <div>
          <div className="px-6 py-5">
            <span className="font-display font-bold text-lg">nothing</span>
            <p className="font-mono text-[10px] uppercase tracking-wider text-secondary mt-0.5">
              Admin
            </p>
          </div>
          <nav className="px-3 pb-4 flex flex-col gap-1">
            {ADMIN_NAV_ITEMS.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `block px-4 py-2 text-sm rounded-neu-sm transition-shadow ${
                    isActive
                      ? "text-primary font-medium shadow-neu-inset-sm"
                      : "text-secondary hover:text-primary hover:shadow-neu-raised-sm"
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
        <div className="px-3 py-4">
          <button
            onClick={handleLogout}
            className="w-full text-left text-xs uppercase tracking-wide text-secondary hover:text-error px-4 py-2 rounded-neu-sm hover:shadow-neu-raised-sm transition-shadow"
          >
            Sign out
          </button>
        </div>
      </aside>
      <div className="flex-1 flex flex-col">
        <main className="flex-1 rounded-neu-lg shadow-neu-raised bg-surface px-8 py-10">{children}</main>
      </div>
    </div>
  );
}