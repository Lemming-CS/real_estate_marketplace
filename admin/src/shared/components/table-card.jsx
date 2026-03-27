export function TableCard({ title, actions, children }) {
  return (
    <section className="table-card">
      <header className="table-card__header">
        <h3>{title}</h3>
        <div className="table-card__actions">{actions}</div>
      </header>
      <div className="table-card__body">{children}</div>
    </section>
  );
}
