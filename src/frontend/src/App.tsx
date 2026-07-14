import { useEffect } from 'react';

import { Navbar } from './components/Navbar';
import { Hero } from './components/Hero';
import { HowItWorks } from './components/HowItWorks';
import { LoginPage } from './components/LoginPage';
import { MyOrdersPage } from './components/MyOrdersPage';
import { SessionDemo } from './components/SessionDemo';
import { SessionPage } from './components/SessionPage';
import { Testimonials } from './components/Testimonials';
import { Footer } from './components/Footer';

export function App() {
  const sessionRoute = getSessionRoute(window.location.pathname, window.location.search);
  const accountRoute = getAccountRoute(window.location.pathname);

  // Intersection Observer for scroll-driven fade-up animations
  useEffect(() => {
    if (sessionRoute || accountRoute) {
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
  }, [sessionRoute, accountRoute]);

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

export function getAccountRoute(pathname: string): 'login' | 'orders' | null {
  const normalized = pathname.replace(/\/+$/, '') || '/';
  if (normalized === '/login') return 'login';
  if (normalized === '/orders' || normalized === '/my-orders') return 'orders';
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
