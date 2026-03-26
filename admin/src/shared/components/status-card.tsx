type StatusCardProps = {
  title: string;
  value: string;
  tone: 'info' | 'success' | 'warning';
};

export function StatusCard({ title, value, tone }: StatusCardProps) {
  return (
    <article className={`status-card status-card--${tone}`}>
      <p className="status-card__title">{title}</p>
      <p className="status-card__value">{value}</p>
    </article>
  );
}

