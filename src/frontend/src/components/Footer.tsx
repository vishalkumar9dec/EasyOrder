export function Footer() {
  return (
    <footer className="site-footer" id="footer" aria-label="Site footer">
      <div className="footer-grid">
        <div>
          <p className="footer-brand">Easy<span>Order</span></p>
          <p className="footer-tagline">
            WhatsApp-first group food ordering. The host starts from WhatsApp, everyone collaborates on a shared cart, and checkout runs through Swiggy.
          </p>
        </div>

        <div className="footer-col">
          <h4>Product</h4>
          <a href="#how-it-works">How It Works</a>
          <a href="/demo">Watch Demo</a>
          <a href="/playground">Interactive Playground</a>
          <a href="#testimonials">Reviews</a>
        </div>

        <div className="footer-col">
          <h4>Contact</h4>
          <p>support@easyorder.app</p>
          <p>Bengaluru, India</p>
        </div>

        <div className="footer-col">
          <h4>Stay Updated</h4>
          <p>Get notified when EasyOrder launches publicly.</p>
          <form className="newsletter-form" onSubmit={(e) => e.preventDefault()}>
            <input
              className="newsletter-input"
              type="email"
              placeholder="your@email.com"
              aria-label="Email for newsletter"
              id="newsletter-email"
            />
            <button className="newsletter-btn" type="submit" id="newsletter-submit">
              Join
            </button>
          </form>
        </div>
      </div>

      <div className="footer-bottom">
        <p className="footer-copyright">
          © {new Date().getFullYear()} EasyOrder. Built for the Swiggy Builder Program.
        </p>
        <div className="footer-socials">
          <a href="#" aria-label="Twitter">𝕏</a>
          <a href="#" aria-label="GitHub">GH</a>
          <a href="#" aria-label="LinkedIn">in</a>
        </div>
      </div>
    </footer>
  );
}
