import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';

import { useAuth } from '@/core/auth/auth-context';
import { QueryState } from '@/shared/components/query-state';
import { StatusBadge } from '@/shared/components/status-badge';
import { TableCard } from '@/shared/components/table-card';

export function UsersPage() {
  const auth = useAuth();
  const [filters, setFilters] = useState({ q: '', status: '' });
  const query = useQuery({
    queryKey: ['admin-users', filters],
    queryFn: () => auth.authenticatedRequest('/admin/users', { query: filters }),
  });

  const rows = useMemo(() => query.data?.items ?? [], [query.data]);

  return (
    <section className="page-section">
      <header className="page-header">
        <p className="eyebrow">User Management</p>
        <h1>Search, inspect, and control accounts</h1>
      </header>

      <TableCard
        title="Accounts"
        actions={
          <div className="toolbar">
            <input
              className="toolbar-input"
              placeholder="Search email, username, or full name"
              value={filters.q}
              onChange={(event) => setFilters((current) => ({ ...current, q: event.target.value }))}
            />
            <select
              className="toolbar-select"
              value={filters.status}
              onChange={(event) => setFilters((current) => ({ ...current, status: event.target.value }))}
            >
              <option value="">All statuses</option>
              <option value="active">Active</option>
              <option value="suspended">Suspended</option>
              <option value="pending_verification">Pending verification</option>
            </select>
          </div>
        }
      >
        <QueryState isLoading={query.isLoading} error={query.error} isEmpty={!rows.length}>
          <table className="data-table">
            <thead>
              <tr>
                <th>User</th>
                <th>Status</th>
                <th>Roles</th>
                <th>Last Login</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {rows.map((user) => (
                <tr key={user.public_id}>
                  <td>
                    <strong>{user.full_name}</strong>
                    <div className="muted-text">{user.email}</div>
                  </td>
                  <td><StatusBadge value={user.status} /></td>
                  <td>{user.roles.join(', ')}</td>
                  <td>{user.last_login_at ? new Date(user.last_login_at).toLocaleString() : 'Never'}</td>
                  <td>
                    <Link className="inline-link" to={`/users/${user.public_id}`}>
                      Open
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </QueryState>
      </TableCard>
    </section>
  );
}
