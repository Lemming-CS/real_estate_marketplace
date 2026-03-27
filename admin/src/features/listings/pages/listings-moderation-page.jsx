import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { useAuth } from '@/core/auth/auth-context';
import { QueryState } from '@/shared/components/query-state';
import { StatusBadge } from '@/shared/components/status-badge';
import { TableCard } from '@/shared/components/table-card';

export function ListingsModerationPage() {
  const auth = useAuth();
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState({ q: '', status: '', city: '', reported_only: false });

  const listingsQuery = useQuery({
    queryKey: ['admin-listings-moderation', filters],
    queryFn: () => auth.authenticatedRequest('/admin/listings/moderation', { query: filters }),
  });

  const reviewMutation = useMutation({
    mutationFn: ({ listingPublicId, action }) =>
      auth.authenticatedRequest(`/admin/listings/${listingPublicId}/review`, {
        method: 'POST',
        body: {
          action,
          moderation_note: window.prompt(`Moderation note for ${action}:`) ?? '',
        },
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-listings-moderation'] }),
  });

  const archiveMutation = useMutation({
    mutationFn: (listingPublicId) => auth.authenticatedRequest(`/listings/${listingPublicId}/archive`, { method: 'POST' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-listings-moderation'] }),
  });

  const rows = listingsQuery.data?.items ?? [];

  return (
    <section className="page-section">
      <header className="page-header">
        <p className="eyebrow">Listings Moderation</p>
        <h1>Inspect, hide, archive, and recover property listings</h1>
      </header>

      <TableCard
        title="Moderation queue"
        actions={
          <div className="toolbar">
            <input className="toolbar-input" placeholder="Search title or description" value={filters.q} onChange={(event) => setFilters((current) => ({ ...current, q: event.target.value }))} />
            <input className="toolbar-input" placeholder="City" value={filters.city} onChange={(event) => setFilters((current) => ({ ...current, city: event.target.value }))} />
            <select className="toolbar-select" value={filters.status} onChange={(event) => setFilters((current) => ({ ...current, status: event.target.value }))}>
              <option value="">All listings</option>
              <option value="published">Published</option>
              <option value="inactive">Hidden</option>
              <option value="rejected">Rejected</option>
              <option value="archived">Archived</option>
            </select>
            <label className="checkbox-field">
              <input
                type="checkbox"
                checked={filters.reported_only}
                onChange={(event) => setFilters((current) => ({ ...current, reported_only: event.target.checked }))}
              />
              <span>Reported only</span>
            </label>
          </div>
        }
      >
        <QueryState isLoading={listingsQuery.isLoading} error={listingsQuery.error} isEmpty={!rows.length}>
          <table className="data-table">
            <thead>
                <tr>
                  <th>Listing</th>
                  <th>Status</th>
                  <th>Location</th>
                  <th>Seller</th>
                  <th>Price</th>
                  <th />
                </tr>
            </thead>
            <tbody>
              {rows.map((listing) => (
                <tr key={listing.public_id}>
                  <td>
                    <strong>{listing.title}</strong>
                    <div className="muted-text">{listing.category.name}</div>
                  </td>
                  <td><StatusBadge value={listing.status} /></td>
                  <td>{[listing.district, listing.city].filter(Boolean).join(', ')}</td>
                  <td>{listing.seller.full_name}</td>
                  <td>{listing.price_amount} {listing.currency_code}</td>
                  <td className="table-actions">
                    <button className="secondary-button" type="button" onClick={() => reviewMutation.mutate({ listingPublicId: listing.public_id, action: 'publish' })}>
                      Publish
                    </button>
                    <button className="secondary-button" type="button" onClick={() => reviewMutation.mutate({ listingPublicId: listing.public_id, action: 'hide' })}>
                      Hide
                    </button>
                    <button className="danger-button" type="button" onClick={() => reviewMutation.mutate({ listingPublicId: listing.public_id, action: 'reject' })}>
                      Reject
                    </button>
                    <button className="ghost-button" type="button" onClick={() => archiveMutation.mutate(listing.public_id)}>
                      Archive
                    </button>
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
