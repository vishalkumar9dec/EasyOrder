import { useEffect, useState } from 'react';

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <>
      <nav className={`navbar ${scrolled ? 'scrolled' : ''}`} id="navbar" aria-label="Main navigation">
        <a className="navbar-brand" href="#top">
          Easy<span>Order</span>
        </a>

        <div className="navbar-links">
          <a href="/#how-it-works">How It Works</a>
          <a href="/#demo">Demo</a>
          <a href="/#testimonials">Reviews</a>
          <a href="/#footer">Contact</a>
          <a href="/orders" id="nav-my-orders">My Orders</a>
          <a href="/orders/live" id="nav-live-orders">Live Orders</a>
        </div>

        <a className="navbar-cta" href="/#demo" id="nav-try-demo">
          Try Demo
        </a>

        <button
          className="navbar-hamburger"
          onClick={() => setMenuOpen(true)}
          aria-label="Open menu"
          id="nav-hamburger"
        >
          <span />
          <span />
          <span />
        </button>
      </nav>

      <div
        className={`mobile-overlay ${menuOpen ? 'open' : ''}`}
        onClick={() => setMenuOpen(false)}
      />

      <div className={`mobile-menu ${menuOpen ? 'open' : ''}`} aria-label="Mobile navigation">
        <a href="/#how-it-works" onClick={() => setMenuOpen(false)}>How It Works</a>
        <a href="/#demo" onClick={() => setMenuOpen(false)}>Demo</a>
        <a href="/#testimonials" onClick={() => setMenuOpen(false)}>Reviews</a>
        <a href="/#footer" onClick={() => setMenuOpen(false)}>Contact</a>
        <a href="/orders" onClick={() => setMenuOpen(false)}>My Orders</a>
        <a href="/orders/live" onClick={() => setMenuOpen(false)}>Live Orders</a>
      </div>
    </>
  );
}
