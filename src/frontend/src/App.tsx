const setupChecks = [
  'FastAPI backend shell',
  'React web app shell',
  'PostgreSQL local service',
  'Mock-first environment',
];

export function App() {
  return (
    <main className="app-shell">
      <section className="hero">
        <p className="eyebrow">EasyOrder local foundation</p>
        <h1>WhatsApp-first group ordering, ready for the next slice.</h1>
        <p className="summary">
          This placeholder app confirms the frontend toolchain is alive before the local
          use-case playground lands in issue #2.
        </p>
      </section>

      <section className="checklist" aria-label="Foundation checklist">
        {setupChecks.map((check) => (
          <div className="check" key={check}>
            <span aria-hidden="true">✓</span>
            <p>{check}</p>
          </div>
        ))}
      </section>
    </main>
  );
}
