export function StatusBadge({ value }) {
  return <span className={`status-badge status-badge--${String(value).replace(/_/g, '-')}`}>{value}</span>;
}
