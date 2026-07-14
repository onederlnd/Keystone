import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const LINKS = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/listings", label: "Listings" },
  { to: "/contacts", label: "Contacts" },
  { to: "/pipeline", label: "Pipeline" },
  { to: "/documents", label: "Documents" },
  { to: "/analytics", label: "Analytics" },
];

export default function Layout() {
  const { user, signOut } = useAuth();

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">Keystone</div>
        <div className="brand-sub">Transaction Ledger</div>

        <nav>
          {LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) =>
                "nav-link" + (isActive ? " active" : "")
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div>{user?.full_name || user?.email}</div>
          <div className="eyebrow">{user?.role}</div>
          <button onClick={signOut}>Sign out</button>
        </div>
      </aside>

      <div className="main">
        <Outlet />
      </div>
    </div>
  );
}
