import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';

import { useAuth } from '@/core/auth/auth-context';
import { QueryState } from '@/shared/components/query-state';
import { StatusBadge } from '@/shared/components/status-badge';
import { TableCard } from '@/shared/components/table-card';

export function PromotionsPage() {
  const auth = useAuth();
  const [status, setStatus] = useState('');

  const promotionsQuery = useQuery({
    queryKey: ['admin-promotions', status],
    queryFn: () => auth.authenticatedRequest('/admin/promotions', { query: { status } }),
  });

  const rows = promotionsQuery.data?.items ?? [];

  return (
    <section className="page-section">
      <header className="page-header">
        <p className="eyebrow">Promotions Visibility</p>
        <h1>See active, expired, and pending boosts</h1>
      </header>

      <TableCard
        title="Promotions"
        actions={
          <select className="toolbar-select" value={status} onChange={(event) => setStatus(event.target.value)}>
            <option value="">All statuses</option>
            <option value="pending_payment">Pending payment</option>
            <option value="active">Active</option>
            <option value="expired">Expired</option>
            <option value="cancelled">Cancelled</option>
          </select>
        }
      >
        <QueryState isLoading={promotionsQuery.isLoading} error={promotionsQuery.error} isEmpty={!rows.length}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Listing</th>
                <th>Status</th>
                <th>Seller</th>
                <th>Target</th>
                <th>Budget</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((promotion) => (
                <tr key={promotion.public_id}>
                  <td>
                    <strong>{promotion.listing_title}</strong>
                    <div className="muted-text">{promotion.package_name}</div>
                  </td>
                  <td><StatusBadge value={promotion.status} /></td>
                  <td>{promotion.seller_username}</td>
                  <td>{promotion.target_city ?? 'All cities'} / {promotion.target_category_name ?? 'All categories'}</td>
                  <td>{promotion.price_amount} {promotion.currency_code}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </QueryState>
      </TableCard>
    </section>
  );
}
