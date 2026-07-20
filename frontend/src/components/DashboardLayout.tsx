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
    <div className="min-h-screen bg-surface font-body flex">
      <aside className="w-56 border-r border-border flex flex-col justify-between shrink-0">
        <div>
          <div className="px-6 py-5 border-b border-border">
            <span className="font-display font-bold text-lg">nothing</span>
          </div>
          <nav className="py-4">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === "/"}
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
        <header className="flex items-center justify-end px-8 py-5 border-b border-border">
          <span className="font-mono text-[11px] uppercase tracking-wider border border-secondary text-secondary px-2 py-0.5">
            Test mode
          </span>
        </header>
        <main className="flex-1 px-8 py-10">{children}</main>
      </div>
    </div>
  );
}