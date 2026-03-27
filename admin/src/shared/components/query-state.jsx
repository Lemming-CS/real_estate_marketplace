export function QueryState({ isLoading, error, isEmpty, emptyMessage = 'No records found.', children }) {
  if (isLoading) {
    return <div className="query-state">Loading…</div>;
  }

  if (error) {
    return <div className="query-state query-state--error">{error.message}</div>;
  }

  if (isEmpty) {
    return <div className="query-state">{emptyMessage}</div>;
  }

  return children;
}
