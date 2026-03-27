import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';

import { useAuth } from '@/core/auth/auth-context';
import { QueryState } from '@/shared/components/query-state';
import { TableCard } from '@/shared/components/table-card';

export function AuditLogsPage() {
  const auth = useAuth();
  const [filters, setFilters] = useState({ q: '', action: '', entity_type: '' });

  const logsQuery = useQuery({
    queryKey: ['admin-audit-logs', filters],
    queryFn: () => auth.authenticatedRequest('/admin/audit-logs', { query: filters }),
  });

  const rows = logsQuery.data?.items ?? [];

  return (
    <section className="page-section">
      <header className="page-header">
        <p className="eyebrow">Audit Trail</p>
        <h1>Trace privileged decisions and state changes</h1>
      </header>

      <TableCard
        title="Audit logs"
        actions={
          <div className="toolbar">
            <input className="toolbar-input" placeholder="Search action, entity, or description" value={filters.q} onChange={(event) => setFilters((current) => ({ ...current, q: event.target.value }))} />
            <input className="toolbar-input" placeholder="Action" value={filters.action} onChange={(event) => setFilters((current) => ({ ...current, action: event.target.value }))} />
            <input className="toolbar-input" placeholder="Entity type" value={filters.entity_type} onChange={(event) => setFilters((current) => ({ ...current, entity_type: event.target.value }))} />
          </div>
        }
      >
        <QueryState isLoading={logsQuery.isLoading} error={logsQuery.error} isEmpty={!rows.length}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Action</th>
                <th>Actor</th>
                <th>Entity</th>
                <th>When</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((log) => (
                <tr key={log.id}>
                  <td>
                    <strong>{log.action}</strong>
                    <div className="muted-text">{log.description ?? 'No description'}</div>
                    {log.after_json?.reason ? <div className="muted-text">Note: {log.after_json.reason}</div> : null}
                  </td>
                  <td>{log.actor_email ?? 'System'}</td>
                  <td>{log.entity_type} / {log.entity_id ?? 'n/a'}</td>
                  <td>{new Date(log.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </QueryState>
      </TableCard>
    </section>
  );
}
