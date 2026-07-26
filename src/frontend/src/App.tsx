import { useEffect } from 'react';

import { Navbar } from './components/Navbar';
import { Hero } from './components/Hero';
import { HowItWorks } from './components/HowItWorks';
import { LiveOrdersPage } from './components/LiveOrdersPage';
import { DemoStory } from './components/DemoStory';
import { LoginPage } from './components/LoginPage';
import { MyOrdersPage } from './components/MyOrdersPage';
import { SessionDemo } from './components/SessionDemo';
import { SessionPage } from './components/SessionPage';
import { Testimonials } from './components/Testimonials';
import { Footer } from './components/Footer';

export function App() {
  const sessionRoute = getSessionRoute(window.location.pathname, window.location.search);
  const accountRoute = getAccountRoute(window.location.pathname);
  const normalizedPath = window.location.pathname.replace(/\/+$/, '') || '/';
  const demoRoute = normalizedPath === '/demo';
  const playgroundRoute = normalizedPath === '/playground';

  // Intersection Observer for scroll-driven fade-up animations
  useEffect(() => {
    if (!shouldObserveFadeUps(Boolean(sessionRoute), Boolean(accountRoute), demoRoute, playgroundRoute)) {
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
  }, [sessionRoute, accountRoute, demoRoute, playgroundRoute]);

  if (demoRoute) {
    return <DemoStory />;
  }

  if (playgroundRoute) {
    return (
      <>
        <Navbar />
        <main className="playground-page">
          <SessionDemo />
        </main>
      </>
    );
  }

  if (sessionRoute) {
    return (
      <>
        <Navbar />
        <SessionPage sessionId={sessionRoute.sessionId} token={sessionRoute.token} />
      </>
    );
  }

  if (accountRoute === 'login') {
    return (
      <>
        <Navbar />
        <LoginPage />
      </>
    );
  }
  if (accountRoute === 'orders') {
    return (
      <>
        <Navbar />
        <MyOrdersPage />
      </>
    );
  }
  if (accountRoute === 'live-orders') {
    return (
      <>
        <Navbar />
        <LiveOrdersPage />
      </>
    );
  }

  return (
    <>
      <Navbar />
      <main>
        <Hero />
        <HowItWorks />
        <Testimonials />
      </main>
      <Footer />
    </>
  );
}

export function shouldObserveFadeUps(
  hasSessionRoute: boolean,
  hasAccountRoute: boolean,
  hasDemoRoute: boolean,
  hasPlaygroundRoute: boolean,
): boolean {
  if (hasPlaygroundRoute) {
    return true;
  }
  return !hasSessionRoute && !hasAccountRoute && !hasDemoRoute;
}

export function getAccountRoute(pathname: string): 'login' | 'orders' | 'live-orders' | null {
  const normalized = pathname.replace(/\/+$/, '') || '/';
  if (normalized === '/login') return 'login';
  if (normalized === '/orders' || normalized === '/my-orders') return 'orders';
  if (normalized === '/orders/live') return 'live-orders';
  return null;
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
