import { NavLink, useNavigate } from "react-router-dom";

const NAV_ITEMS = [
  { label: "Overview", path: "/" },
  { label: "Payments", path: "/payments" },
  { label: "Refunds", path: "/refunds" },
  { label: "Payouts", path: "/payouts" },
  { label: "Customers", path: "/customers" },
  { label: "Webhooks", path: "/webhooks" },
  { label: "API Keys", path: "/api-keys" },
  { label: "Team", path: "/team" },
  { label: "Settings", path: "/settings" },
];

export function DashboardLayout({ children }: { children: React.ReactNode }) {
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
          </div>
          <nav className="px-3 pb-4 flex flex-col gap-1">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === "/"}
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

      <div className="flex-1 flex flex-col gap-6">
        <header className="flex items-center justify-end px-2 py-1 min-h-[1px]">
          {/* <span className="font-mono text-[11px] uppercase tracking-wider border border-secondary text-secondary px-2 py-0.5">
            Test mode
          </span> */}
        </header>
        <main className="flex-1 rounded-neu-lg shadow-neu-raised bg-surface px-8 py-10">{children}</main>
      </div>
    </div>
  );
}