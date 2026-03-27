import { NavLink, Outlet } from 'react-router-dom';

import { useAuth } from '@/core/auth/auth-context';

const navigation = [
  { to: '/', label: 'Dashboard' },
  { to: '/users', label: 'Users' },
  { to: '/listings', label: 'Listings' },
  { to: '/reports', label: 'Reports' },
  { to: '/payments', label: 'Payments' },
  { to: '/promotions', label: 'Promotions' },
  { to: '/promotion-packages', label: 'Packages' },
  { to: '/categories', label: 'Categories' },
  { to: '/audit-logs', label: 'Audit Logs' },
  { to: '/conversations', label: 'Message Review' },
];

export function AppLayout() {
  const auth = useAuth();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-header">
          <p className="eyebrow">Marketplace Admin</p>
          <h1>Operations Console</h1>
          <p className="sidebar-copy">
            Report-driven moderation, payments, abuse review, and operational
            controls for the real-estate marketplace.
          </p>
          <nav className="nav-links">
            {navigation.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `nav-link ${isActive ? 'nav-link--active' : ''}`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>

        <div className="sidebar-footer">
          <p className="sidebar-user">{auth.currentUser?.full_name}</p>
          <p className="sidebar-meta">{auth.currentUser?.email}</p>
          <button
            className="ghost-button"
            type="button"
            onClick={() => auth.logout()}
          >
            Sign Out
          </button>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <p className="eyebrow">Admin Control Plane</p>
            <h2>Secure operational interface</h2>
          </div>
        </header>
        <Outlet />
      </main>
    </div>
  );
}
