import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { useAuth } from '@/core/auth/auth-context';
import { QueryState } from '@/shared/components/query-state';
import { StatusBadge } from '@/shared/components/status-badge';
import { TableCard } from '@/shared/components/table-card';

export function PaymentsPage() {
  const auth = useAuth();
  const queryClient = useQueryClient();
  const [status, setStatus] = useState('');

  const paymentsQuery = useQuery({
    queryKey: ['admin-payments', status],
    queryFn: () => auth.authenticatedRequest('/admin/payments', { query: { status } }),
  });

  const simulateMutation = useMutation({
    mutationFn: ({ paymentPublicId, result }) =>
      auth.authenticatedRequest(`/payments/${paymentPublicId}/simulate`, {
        method: 'POST',
        body: { result },
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-payments'] }),
  });

  const rows = paymentsQuery.data?.items ?? [];

  return (
    <section className="page-section">
      <header className="page-header">
        <p className="eyebrow">Payments</p>
        <h1>Promotion transactions and simulated provider state</h1>
      </header>

      <TableCard
        title="Payments"
        actions={
          <select className="toolbar-select" value={status} onChange={(event) => setStatus(event.target.value)}>
            <option value="">All statuses</option>
            <option value="pending">Pending</option>
            <option value="successful">Successful</option>
            <option value="failed">Failed</option>
            <option value="cancelled">Cancelled</option>
            <option value="refunded_ready">Refund-ready</option>
          </select>
        }
      >
        <QueryState isLoading={paymentsQuery.isLoading} error={paymentsQuery.error} isEmpty={!rows.length}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Payment</th>
                <th>Status</th>
                <th>Listing</th>
                <th>Amount</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {rows.map((payment) => (
                <tr key={payment.public_id}>
                  <td>
                    <strong>{payment.public_id}</strong>
                    <div className="muted-text">{payment.provider_reference ?? 'No provider ref'}</div>
                  </td>
                  <td><StatusBadge value={payment.status} /></td>
                  <td>{payment.listing_title ?? 'N/A'}</td>
                  <td>{payment.amount} {payment.currency_code}</td>
                  <td className="table-actions">
                    {payment.status === 'pending' ? (
                      <>
                        <button className="secondary-button" type="button" onClick={() => simulateMutation.mutate({ paymentPublicId: payment.public_id, result: 'successful' })}>
                          Mark Success
                        </button>
                        <button className="ghost-button" type="button" onClick={() => simulateMutation.mutate({ paymentPublicId: payment.public_id, result: 'failed' })}>
                          Fail
                        </button>
                      </>
                    ) : null}
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
