/*
Layout shell for the Admin Portal — mirrors DashboardLayout's structure and design language
(same sidebar pattern, ledger-tape/stamp visuals) but with admin-specific navigation and no
"Test mode" stamp, since admin actions apply platform-wide, not per-merchant test/live mode.
*/

import { NavLink, useNavigate } from "react-router-dom";

const ADMIN_NAV_ITEMS = [
  { label: "Merchant KYC", path: "/admin/merchants" },
  { label: "Fraud Review", path: "/admin/fraud" },
  { label: "System Settings", path: "/admin/settings" },
  { label: "Feature Flags", path: "/admin/feature-flags" },
  { label: "Maintenance", path: "/admin/maintenance" },
  { label: "Reports", path: "/admin/reports" },
];

export function AdminLayout({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();
  function handleLogout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    navigate("/login");
  }
  return (
    <div className="min-h-screen bg-surface font-body flex">
      <aside className="w-56 border-r border-border flex flex-col justify-between shrink-0">
        <div>
          <div className="px-6 py-5 border-b border-border">
            <span className="font-display font-bold text-lg">nothing</span>
            <p className="font-mono text-[10px] uppercase tracking-wider text-secondary mt-0.5">
              Admin
            </p>
          </div>
          <nav className="py-4">
            {ADMIN_NAV_ITEMS.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `block px-6 py-2 text-sm ${
                    isActive
                      ? "text-primary font-medium border-l-2 border-primary bg-black/[0.03]"
                      : "text-secondary border-l-2 border-transparent hover:text-primary"
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
        <div className="px-6 py-4 border-t border-border">
          <button
            onClick={handleLogout}
            className="text-xs uppercase tracking-wide text-secondary hover:text-error"
          >
            Sign out
          </button>
        </div>
      </aside>
      <div className="flex-1 flex flex-col">
        <main className="flex-1 px-8 py-10">{children}</main>
      </div>
    </div>
  );
}