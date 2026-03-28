import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { useAuth } from '@/core/auth/auth-context';
import { QueryState } from '@/shared/components/query-state';
import { StatusBadge } from '@/shared/components/status-badge';
import { TableCard } from '@/shared/components/table-card';

const initialForm = {
  code: '',
  name: '',
  description: '',
  duration_days: 7,
  price_amount: '9.99',
  currency_code: 'USD',
  boost_level: 5,
};

export function PromotionPackagesPage() {
  const auth = useAuth();
  const queryClient = useQueryClient();
  const [selectedPackage, setSelectedPackage] = useState(null);
  const [formState, setFormState] = useState(initialForm);

  const packagesQuery = useQuery({
    queryKey: ['admin-promotion-packages'],
    queryFn: () => auth.authenticatedRequest('/admin/promotion-packages'),
  });

  const saveMutation = useMutation({
    mutationFn: () => {
      const path = selectedPackage ? `/admin/promotion-packages/${selectedPackage.public_id}` : '/admin/promotion-packages';
      return auth.authenticatedRequest(path, {
        method: selectedPackage ? 'PATCH' : 'POST',
        body: formState,
      });
    },
    onSuccess: () => {
      setSelectedPackage(null);
      setFormState(initialForm);
      queryClient.invalidateQueries({ queryKey: ['admin-promotion-packages'] });
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: (packagePublicId) =>
      auth.authenticatedRequest(`/admin/promotion-packages/${packagePublicId}`, { method: 'DELETE' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-promotion-packages'] }),
  });

  const activateMutation = useMutation({
    mutationFn: (packagePublicId) =>
      auth.authenticatedRequest(`/admin/promotion-packages/${packagePublicId}/activate`, { method: 'POST' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-promotion-packages'] }),
  });

  const packages = useMemo(() => packagesQuery.data ?? [], [packagesQuery.data]);

  function loadPackage(item) {
    setSelectedPackage(item);
    setFormState({
      code: item.code,
      name: item.name,
      description: item.description ?? '',
      duration_days: item.duration_days,
      price_amount: item.price_amount,
      currency_code: item.currency_code,
      boost_level: item.boost_level,
      is_active: item.is_active,
    });
  }

  return (
    <section className="page-section">
      <header className="page-header">
        <p className="eyebrow">Promotion Packages</p>
        <h1>Manage pricing, duration, and boost tiers</h1>
      </header>

      <div className="split-grid split-grid--wide">
        <TableCard title="Package editor">
          <form
            className="form-grid"
            onSubmit={(event) => {
              event.preventDefault();
              saveMutation.mutate();
            }}
          >
            <label className="field">
              <span>Code</span>
              <input value={formState.code} disabled={Boolean(selectedPackage)} onChange={(event) => setFormState((current) => ({ ...current, code: event.target.value }))} required />
            </label>
            <label className="field">
              <span>Name</span>
              <input value={formState.name} onChange={(event) => setFormState((current) => ({ ...current, name: event.target.value }))} required />
            </label>
            <label className="field field--full">
              <span>Description</span>
              <textarea value={formState.description} onChange={(event) => setFormState((current) => ({ ...current, description: event.target.value }))} rows={3} />
            </label>
            <label className="field">
              <span>Duration days</span>
              <input type="number" min="1" value={formState.duration_days} onChange={(event) => setFormState((current) => ({ ...current, duration_days: Number(event.target.value) }))} />
            </label>
            <label className="field">
              <span>Price</span>
              <input value={formState.price_amount} onChange={(event) => setFormState((current) => ({ ...current, price_amount: event.target.value }))} />
            </label>
            <label className="field">
              <span>Currency</span>
              <input value={formState.currency_code} onChange={(event) => setFormState((current) => ({ ...current, currency_code: event.target.value.toUpperCase() }))} />
            </label>
            <label className="field">
              <span>Boost level</span>
              <input type="number" min="1" value={formState.boost_level} onChange={(event) => setFormState((current) => ({ ...current, boost_level: Number(event.target.value) }))} />
            </label>
            <div className="toolbar">
              <button className="primary-button" type="submit">{selectedPackage ? 'Update package' : 'Create package'}</button>
              {selectedPackage ? (
                <button className="ghost-button" type="button" onClick={() => { setSelectedPackage(null); setFormState(initialForm); }}>
                  Clear
                </button>
              ) : null}
            </div>
          </form>
        </TableCard>

        <TableCard title="Existing packages">
          <QueryState isLoading={packagesQuery.isLoading} error={packagesQuery.error} isEmpty={!packages.length}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Package</th>
                  <th>Status</th>
                  <th>Duration</th>
                  <th>Price</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {packages.map((item) => (
                  <tr key={item.public_id}>
                    <td>
                      <strong>{item.name}</strong>
                      <div className="muted-text">{item.code}</div>
                    </td>
                    <td><StatusBadge value={item.status ?? (item.is_active ? 'active' : 'inactive')} /></td>
                    <td>{item.duration_days} days</td>
                    <td>{item.price_amount} {item.currency_code}</td>
                    <td className="table-actions">
                      <button className="secondary-button" type="button" onClick={() => loadPackage(item)}>Edit</button>
                      {item.is_active ? (
                        <button className="danger-button" type="button" onClick={() => deactivateMutation.mutate(item.public_id)}>
                          Deactivate
                        </button>
                      ) : (
                        <button className="secondary-button" type="button" onClick={() => activateMutation.mutate(item.public_id)}>
                          Activate
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </QueryState>
        </TableCard>
      </div>
    </section>
  );
}
