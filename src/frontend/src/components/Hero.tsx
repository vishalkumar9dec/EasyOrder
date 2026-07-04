import heroImage from '../assets/hero-feast.png';

export function Hero() {
  return (
    <section className="hero" id="top" aria-label="Hero">
      <div className="hero-bg">
        <img src={heroImage} alt="Indian feast spread on dark table" />
        <div className="hero-overlay" />
      </div>

      <div className="hero-content fade-up">
        <div className="hero-badge">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
          WhatsApp-first ordering
        </div>

        <h1>
          Craft Your Feast, <em>Together</em>
        </h1>

        <p className="hero-subtitle">
          Plan group meals from WhatsApp, share a collaborative cart in real-time, and checkout through Swiggy with the host in control.
        </p>

        <div className="hero-actions">
          <a className="btn-primary" href="#demo" id="hero-cta">
            Try the Demo
          </a>
          <a className="btn-secondary" href="#how-it-works" id="hero-learn">
            How It Works
          </a>
        </div>
      </div>

      <div className="hero-scroll-hint" aria-hidden="true">
        <span>Scroll</span>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M7 13l5 5 5-5M7 6l5 5 5-5" />
        </svg>
      </div>
    </section>
  );
}
