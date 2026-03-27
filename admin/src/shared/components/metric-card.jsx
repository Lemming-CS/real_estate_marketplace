export function MetricCard({ title, value, note }) {
  return (
    <article className="metric-card">
      <p className="metric-card__title">{title}</p>
      <p className="metric-card__value">{value}</p>
      {note ? <p className="metric-card__note">{note}</p> : null}
    </article>
  );
}
