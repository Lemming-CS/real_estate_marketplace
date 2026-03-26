import { apiClientConfig } from '@/core/api/client';
import { StatusCard } from '@/shared/components/status-card';

const cards = [
  {
    title: 'Backend API',
    value: apiClientConfig.baseUrl,
    tone: 'info',
  },
  {
    title: 'Admin Shell',
    value: 'Ready for auth, moderation, and operations modules',
    tone: 'success',
  },
  {
    title: 'Current Scope',
    value: 'Scaffold only. Business features will land in later stages.',
    tone: 'warning',
  },
];

export function DashboardPage() {
  return (
    <section>
      <header className="page-header">
        <p className="eyebrow">Starter State</p>
        <h2>{apiClientConfig.appName}</h2>
        <p className="page-copy">
          This admin starter is wired for routing, shared providers, and env-based API
          configuration. It intentionally stops short of business feature implementation.
        </p>
      </header>

      <div className="card-grid">
        {cards.map((card) => (
          <StatusCard key={card.title} title={card.title} value={card.value} tone={card.tone} />
        ))}
      </div>
    </section>
  );
}
