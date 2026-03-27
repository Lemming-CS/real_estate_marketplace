import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { useAuth } from '@/core/auth/auth-context';
import { QueryState } from '@/shared/components/query-state';
import { StatusBadge } from '@/shared/components/status-badge';
import { TableCard } from '@/shared/components/table-card';

const blankForm = {
  slug: '',
  internal_name: '',
  is_active: true,
  sort_order: 0,
  translations: {
    en: { name: '', description: '' },
    ru: { name: '', description: '' },
  },
  attributesJson: '[]',
};

function buildCategoryPayload(formState) {
  return {
    slug: formState.slug,
    internal_name: formState.internal_name,
    is_active: formState.is_active,
    sort_order: Number(formState.sort_order),
    translations: ['en', 'ru'].map((locale) => ({
      locale,
      name: formState.translations[locale].name,
      description: formState.translations[locale].description || null,
    })),
    attributes: JSON.parse(formState.attributesJson || '[]'),
  };
}

export function CategoriesPage() {
  const auth = useAuth();
  const queryClient = useQueryClient();
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [formState, setFormState] = useState(blankForm);

  const categoriesQuery = useQuery({
    queryKey: ['admin-categories'],
    queryFn: () => auth.authenticatedRequest('/admin/categories'),
  });

  const saveMutation = useMutation({
    mutationFn: () => {
      const path = selectedCategory ? `/admin/categories/${selectedCategory.public_id}` : '/admin/categories';
      return auth.authenticatedRequest(path, {
        method: selectedCategory ? 'PATCH' : 'POST',
        body: buildCategoryPayload(formState),
      });
    },
    onSuccess: () => {
      setSelectedCategory(null);
      setFormState(blankForm);
      queryClient.invalidateQueries({ queryKey: ['admin-categories'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (categoryPublicId) => auth.authenticatedRequest(`/admin/categories/${categoryPublicId}`, { method: 'DELETE' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-categories'] }),
  });

  const categories = useMemo(() => categoriesQuery.data ?? [], [categoriesQuery.data]);

  function loadCategory(category) {
    const translationMap = Object.fromEntries(category.translations.map((translation) => [translation.locale, translation]));
    setSelectedCategory(category);
    setFormState({
      slug: category.slug,
      internal_name: category.internal_name,
      is_active: category.is_active,
      sort_order: category.sort_order,
      translations: {
        en: {
          name: translationMap.en?.name ?? '',
          description: translationMap.en?.description ?? '',
        },
        ru: {
          name: translationMap.ru?.name ?? '',
          description: translationMap.ru?.description ?? '',
        },
      },
      attributesJson: JSON.stringify(category.attributes, null, 2),
    });
  }

  return (
    <section className="page-section">
      <header className="page-header">
        <p className="eyebrow">Categories</p>
        <h1>Manage taxonomy and localized content</h1>
      </header>

      <div className="split-grid split-grid--wide">
        <TableCard title="Category editor">
          <form className="form-grid" onSubmit={(event) => { event.preventDefault(); saveMutation.mutate(); }}>
            <label className="field">
              <span>Slug</span>
              <input value={formState.slug} onChange={(event) => setFormState((current) => ({ ...current, slug: event.target.value }))} required />
            </label>
            <label className="field">
              <span>Internal name</span>
              <input value={formState.internal_name} onChange={(event) => setFormState((current) => ({ ...current, internal_name: event.target.value }))} required />
            </label>
            <label className="field">
              <span>Sort order</span>
              <input type="number" value={formState.sort_order} onChange={(event) => setFormState((current) => ({ ...current, sort_order: Number(event.target.value) }))} />
            </label>
            <label className="field field--checkbox">
              <input type="checkbox" checked={formState.is_active} onChange={(event) => setFormState((current) => ({ ...current, is_active: event.target.checked }))} />
              <span>Active category</span>
            </label>
            <label className="field">
              <span>English name</span>
              <input value={formState.translations.en.name} onChange={(event) => setFormState((current) => ({ ...current, translations: { ...current.translations, en: { ...current.translations.en, name: event.target.value } } }))} required />
            </label>
            <label className="field">
              <span>Russian name</span>
              <input value={formState.translations.ru.name} onChange={(event) => setFormState((current) => ({ ...current, translations: { ...current.translations, ru: { ...current.translations.ru, name: event.target.value } } }))} required />
            </label>
            <label className="field field--full">
              <span>Attributes JSON</span>
              <textarea rows={8} value={formState.attributesJson} onChange={(event) => setFormState((current) => ({ ...current, attributesJson: event.target.value }))} />
            </label>
            <div className="toolbar">
              <button className="primary-button" type="submit">{selectedCategory ? 'Update category' : 'Create category'}</button>
              {selectedCategory ? <button className="ghost-button" type="button" onClick={() => { setSelectedCategory(null); setFormState(blankForm); }}>Clear</button> : null}
            </div>
          </form>
        </TableCard>

        <TableCard title="Existing categories">
          <QueryState isLoading={categoriesQuery.isLoading} error={categoriesQuery.error} isEmpty={!categories.length}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Category</th>
                  <th>Status</th>
                  <th>Attributes</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {categories.map((category) => (
                  <tr key={category.public_id}>
                    <td>
                      <strong>{category.internal_name}</strong>
                      <div className="muted-text">{category.slug}</div>
                    </td>
                    <td><StatusBadge value={category.is_active ? 'active' : 'inactive'} /></td>
                    <td>{category.attributes.length}</td>
                    <td className="table-actions">
                      <button className="secondary-button" type="button" onClick={() => loadCategory(category)}>Edit</button>
                      <button className="danger-button" type="button" onClick={() => deleteMutation.mutate(category.public_id)}>Delete</button>
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
