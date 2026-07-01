import { useEffect } from 'react';

import { Navbar } from './components/Navbar';
import { Hero } from './components/Hero';
import { HowItWorks } from './components/HowItWorks';
import { SessionDemo } from './components/SessionDemo';
import { SessionPage } from './components/SessionPage';
import { Testimonials } from './components/Testimonials';
import { Footer } from './components/Footer';

export function App() {
  const sessionRoute = getSessionRoute(window.location.pathname, window.location.search);

  // Intersection Observer for scroll-driven fade-up animations
  useEffect(() => {
    if (sessionRoute) {
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
          }
        });
      },
      { threshold: 0.1 },
    );

    document.querySelectorAll('.fade-up').forEach((el) => observer.observe(el));

    return () => observer.disconnect();
  }, [sessionRoute]);

  if (sessionRoute) {
    return <SessionPage sessionId={sessionRoute.sessionId} token={sessionRoute.token} />;
  }

  return (
    <>
      <Navbar />
      <main>
        <Hero />
        <HowItWorks />
        <SessionDemo />
        <Testimonials />
      </main>
      <Footer />
    </>
  );
}

export function getSessionRoute(
  pathname: string,
  search: string,
): { sessionId: string; token: string | null } | null {
  const match = pathname.match(/^\/session\/([^/?#]+)$/);
  if (!match) {
    return null;
  }
  return {
    sessionId: decodeURIComponent(match[1]),
    token: new URLSearchParams(search).get('token'),
  };
}
