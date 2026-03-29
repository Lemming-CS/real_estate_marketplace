import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';

import { useAuth } from '@/core/auth/auth-context';
import { MetricCard } from '@/shared/components/metric-card';
import { QueryState } from '@/shared/components/query-state';
import { StatusBadge } from '@/shared/components/status-badge';
import { TableCard } from '@/shared/components/table-card';

export function UserDetailPage() {
  const { userPublicId } = useParams();
  const auth = useAuth();
  const queryClient = useQueryClient();

  const detailQuery = useQuery({
    queryKey: ['admin-user-detail', userPublicId],
    queryFn: () => auth.authenticatedRequest(`/admin/users/${userPublicId}`),
  });

  const statusMutation = useMutation({
    mutationFn: ({ action }) =>
      auth.authenticatedRequest(`/admin/users/${userPublicId}/status`, {
        method: 'POST',
        body: {
          action,
          reason: window.prompt(`Provide a note for ${action}.`) ?? '',
        },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-user-detail', userPublicId] });
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
    },
  });

  const user = detailQuery.data;

  return (
    <section className="page-section">
      <QueryState isLoading={detailQuery.isLoading} error={detailQuery.error}>
        {user ? (
          <>
            <header className="page-header page-header--split">
              <div>
                <p className="eyebrow">User Detail</p>
                <h1>{user.full_name}</h1>
                <p className="page-copy">@{user.username}</p>
                <p className="page-copy">{user.email}</p>
              </div>
              <div className="toolbar">
                <StatusBadge value={user.status} />
                <Link
                  className="secondary-button"
                  to={`/conversations?user_public_id=${user.public_id}`}
                >
                  Review Messages
                </Link>
                {user.status === 'suspended' ? (
                  <button className="secondary-button" type="button" onClick={() => statusMutation.mutate({ action: 'unsuspend' })}>
                    Unsuspend
                  </button>
                ) : (
                  <button className="danger-button" type="button" onClick={() => statusMutation.mutate({ action: 'suspend' })}>
                    Suspend
                  </button>
                )}
              </div>
            </header>

            <div className="metric-grid">
              <MetricCard title="Username" value={`@${user.username}`} />
              <MetricCard title="Roles" value={user.roles.join(', ')} />
              <MetricCard title="Listings" value={user.listing_count} note={`${user.active_listing_count} published`} />
              <MetricCard title="Locale" value={user.locale} />
              <MetricCard title="Email Verified" value={user.is_email_verified ? 'Yes' : 'No'} />
              <MetricCard
                title="Latest Moderation Note"
                value={user.latest_status_note ? 'Recorded' : 'None'}
                note={user.latest_status_note ?? 'No status note history yet'}
              />
            </div>

            <div className="split-grid">
              <TableCard title="Listings">
                <SimpleMiniTable
                  columns={['Title', 'Status', 'Price']}
                  rows={user.listings.map((item) => [item.title, item.status, `${item.price_amount} ${item.currency_code}`])}
                />
              </TableCard>
              <TableCard title="Promotions">
                <SimpleMiniTable
                  columns={['Package', 'Status', 'Listing']}
                  rows={user.promotions.map((item) => [item.package_name, item.status, item.listing_title])}
                />
              </TableCard>
              <TableCard title="Payments">
                <SimpleMiniTable
                  columns={['Amount', 'Status', 'Type']}
                  rows={user.payments.map((item) => [`${item.amount} ${item.currency_code}`, item.status, item.payment_type])}
                />
              </TableCard>
              <TableCard title="Reports">
                <SimpleMiniTable
                  columns={['Reason', 'Status', 'Listing']}
                  rows={user.reports.map((item) => [item.reason_code, item.status, item.listing_title ?? 'User-level'])}
                />
              </TableCard>
              <TableCard title="Status History">
                <SimpleMiniTable
                  columns={['Changed', 'From', 'To', 'Note']}
                  rows={user.status_history.map((item) => [
                    new Date(item.created_at).toLocaleString(),
                    item.previous_status ?? 'n/a',
                    item.new_status,
                    item.reason ?? 'No note',
                  ])}
                />
              </TableCard>
            </div>
          </>
        ) : null}
      </QueryState>
    </section>
  );
}

function SimpleMiniTable({ columns, rows }) {
  if (!rows.length) {
    return <div className="query-state">No related records.</div>;
  }

  return (
    <table className="data-table">
      <thead>
        <tr>
          {columns.map((column) => (
            <th key={column}>{column}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, index) => (
          <tr key={`${row[0]}-${index}`}>
            {row.map((cell, cellIndex) => (
              <td key={`${index}-${cellIndex}`}>{cell}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
