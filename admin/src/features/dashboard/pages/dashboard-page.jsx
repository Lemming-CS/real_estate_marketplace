import { useQuery } from '@tanstack/react-query';

import { useAuth } from '@/core/auth/auth-context';
import { MetricCard } from '@/shared/components/metric-card';
import { QueryState } from '@/shared/components/query-state';

const chartRows = [
  { label: 'Active users', key: 'active_users' },
  { label: 'Blocked users', key: 'blocked_users' },
  { label: 'Pending manual review', key: 'pending_listings' },
  { label: 'Published listings', key: 'approved_listings' },
  { label: 'Rejected listings', key: 'rejected_listings' },
  { label: 'Active promotions', key: 'active_promotions' },
];

export function DashboardPage() {
  const auth = useAuth();
  const metricsQuery = useQuery({
    queryKey: ['admin-dashboard'],
    queryFn: () => auth.authenticatedRequest('/admin/dashboard'),
  });

  const metrics = metricsQuery.data;
  const maxChartValue = metrics ? Math.max(...chartRows.map((row) => Number(metrics[row.key])), 1) : 1;

  return (
    <section className="page-section">
      <header className="page-header">
        <p className="eyebrow">Operational Snapshot</p>
        <h1>Marketplace health and risk posture</h1>
        <p className="page-copy">
          The dashboard aggregates property supply, moderation pressure, messaging volume, revenue, and current promotion activity.
        </p>
      </header>

      <QueryState isLoading={metricsQuery.isLoading} error={metricsQuery.error}>
        {metrics ? (
          <>
            <div className="metric-grid">
              <MetricCard title="Total Users" value={metrics.total_users} note={`${metrics.active_users} active`} />
              <MetricCard title="Blocked Users" value={metrics.blocked_users} note="Suspended accounts" />
              <MetricCard title="Total Listings" value={metrics.total_listings} note={`${metrics.pending_listings} pending manual review`} />
              <MetricCard title="Reports" value={metrics.total_reports} note="Open and historical" />
              <MetricCard title="Payments" value={metrics.total_payments} note="Promotion transactions" />
              <MetricCard
                title="Promotion Revenue"
                value={`$${metrics.total_revenue_from_promotions}`}
                note={`${metrics.active_promotions} active promotions`}
              />
            </div>

            <section className="chart-card">
              <header className="table-card__header">
                <h3>Operational mix</h3>
              </header>
              <div className="chart-list">
                {chartRows.map((row) => (
                  <div key={row.key} className="chart-row">
                    <span>{row.label}</span>
                    <div className="chart-row__bar">
                      <div
                        className="chart-row__fill"
                        style={{ width: `${(Number(metrics[row.key]) / maxChartValue) * 100}%` }}
                      />
                    </div>
                    <strong>{metrics[row.key]}</strong>
                  </div>
                ))}
              </div>
            </section>
          </>
        ) : null}
      </QueryState>
    </section>
  );
}
