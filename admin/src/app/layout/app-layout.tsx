import { Link, Outlet } from 'react-router-dom';

export function AppLayout() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">Marketplace Admin</p>
          <h1>Operations Console</h1>
        </div>

        <nav className="nav-links">
          <Link to="/">Dashboard</Link>
        </nav>
      </aside>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}

