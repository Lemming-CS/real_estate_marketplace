import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import React from 'react';
import { useAuth } from '@/core/auth/auth-context';
import { QueryState } from '@/shared/components/query-state';
import { StatusBadge } from '@/shared/components/status-badge';
import { TableCard } from '@/shared/components/table-card';

export function ReportsPage() {
  const auth = useAuth();
  const queryClient = useQueryClient();
  const [status, setStatus] = useState('');

  const reportsQuery = useQuery({
    queryKey: ['admin-reports', status],
    queryFn: () =>
      auth.authenticatedRequest('/admin/reports', { query: { status } }),
  });

  const actionMutation = useMutation({
    mutationFn: ({ reportPublicId, action, listing_action, user_action }) =>
      auth.authenticatedRequest(`/admin/reports/${reportPublicId}/resolve`, {
        method: 'POST',
        body: {
          action,
          resolution_note:
            window.prompt(`Resolution note for ${action}:`) ?? '',
          listing_action,
          user_action,
        },
      }),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ['admin-reports'] }),
  });

  const rows = reportsQuery.data?.items ?? [];

  return (
    <section className="page-section">
      <header className="page-header">
        <p className="eyebrow">Reports</p>
        <h1>Abuse and policy signal queue</h1>
      </header>

      <TableCard
        title="Reports queue"
        actions={
          <select
            className="toolbar-select"
            value={status}
            onChange={(event) => setStatus(event.target.value)}
          >
            <option value="">All statuses</option>
            <option value="open">Open</option>
            <option value="in_review">In review</option>
            <option value="resolved">Resolved</option>
            <option value="rejected">Dismissed</option>
          </select>
        }
      >
        <QueryState
          isLoading={reportsQuery.isLoading}
          error={reportsQuery.error}
          isEmpty={!rows.length}
        >
          <table className="data-table">
            <thead>
              <tr>
                <th>Reason</th>
                <th>Status</th>
                <th>Context</th>
                <th>Reporter</th>
                <th>Target</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {rows.map((report) => (
                <React.Fragment key={report.public_id}>
                  <tr>
                    <td>
                      <strong>{report.reason_code}</strong>
                      <div className="muted-text">
                        {report.description ?? 'No description'}
                      </div>
                    </td>
                    <td>
                      <StatusBadge value={report.status} />
                    </td>
                    <td>
                      <div className="muted-text">
                        Listing: {report.listing_status ?? 'n/a'}
                      </div>
                      <div className="muted-text">
                        User: {report.reported_user_status ?? 'n/a'}
                      </div>
                    </td>
                    <td>{report.reporter_username}</td>
                    <td>
                      {report.listing_title ??
                        report.reported_username ??
                        'Unknown target'}
                      <div className="muted-text">
                        {report.listing_public_id ? (
                          <Link
                            className="inline-link"
                            to={`/conversations?listing_public_id=${report.listing_public_id}`}
                          >
                            Review listing conversations
                          </Link>
                        ) : null}
                        {report.reported_user_public_id ? (
                          <>
                            {report.listing_public_id ? ' • ' : null}
                            <Link
                              className="inline-link"
                              to={`/conversations?user_public_id=${report.reported_user_public_id}`}
                            >
                              Review user conversations
                            </Link>
                          </>
                        ) : null}
                      </div>
                    </td>
                  </tr>

                  <tr className="actions-row">
                    <td colSpan={6}>
                      <div className="table-actions">
                        {report.conversation_public_id ? (
                          <Link
                            className="secondary-button"
                            to={`/conversations?listing_public_id=${report.listing_public_id ?? ''}&user_public_id=${report.reported_user_public_id ?? ''}`}
                          >
                            Open Message Review
                          </Link>
                        ) : null}
                        <button
                        className="secondary-button"
                          onClick={() =>
                            actionMutation.mutate({
                              reportPublicId: report.public_id,
                              action: 'in_review',
                            })
                          }
                        >
                          In Review
                        </button>
                        <button
                        className="secondary-button"
                          onClick={() =>
                            actionMutation.mutate({
                              reportPublicId: report.public_id,
                              action: 'resolve',
                              listing_action: 'hide',
                            })
                          }
                        >
                          Hide Listing
                        </button>
                        <button
                        className="secondary-button"
                          onClick={() =>
                            actionMutation.mutate({
                              reportPublicId: report.public_id,
                              action: 'resolve',
                              listing_action: 'archive',
                            })
                          }
                        >
                          Archive Listing
                        </button>
                        <button
                        className="secondary-button"
                          onClick={() =>
                            actionMutation.mutate({
                              reportPublicId: report.public_id,
                              action: 'resolve',
                              user_action: 'suspend',
                            })
                          }
                        >
                          Suspend Seller
                        </button>
                        <button
                        className="secondary-button"
                          onClick={() =>
                            actionMutation.mutate({
                              reportPublicId: report.public_id,
                              action: 'resolve',
                            })
                          }
                        >
                          Resolve
                        </button>
                        <button
                          className="danger-button"
                          onClick={() =>
                            actionMutation.mutate({
                              reportPublicId: report.public_id,
                              action: 'dismiss',
                            })
                          }
                        >
                          Dismiss
                        </button>
                      </div>
                    </td>
                  </tr>
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </QueryState>
      </TableCard>
    </section>
  );
}
