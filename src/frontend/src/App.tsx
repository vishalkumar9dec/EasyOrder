import { useEffect } from 'react';

import { Navbar } from './components/Navbar';
import { Hero } from './components/Hero';
import { HowItWorks } from './components/HowItWorks';
import { SessionDemo } from './components/SessionDemo';
import { Testimonials } from './components/Testimonials';
import { Footer } from './components/Footer';

export function App() {
  // Intersection Observer for scroll-driven fade-up animations
  useEffect(() => {
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
  }, []);

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
