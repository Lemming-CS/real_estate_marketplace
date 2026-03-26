export function StatusCard({ title, value, tone }) {
  return (
    <article className={`status-card status-card--${tone}`}>
      <p className="status-card__title">{title}</p>
      <p className="status-card__value">{value}</p>
    </article>
  );
}
