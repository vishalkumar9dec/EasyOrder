export function HowItWorks() {
  return (
    <section className="how-it-works" id="how-it-works" aria-label="How it works">
      <div className="section-container">
        <p className="section-eyebrow fade-up">How It Works</p>
        <h2 className="section-title fade-up">Three steps to a shared feast</h2>

        <div className="steps-grid">
          <div className="step-connector" aria-hidden="true" />

          <div className="step-card fade-up" id="step-1">
            <div className="step-number" aria-hidden="true">1</div>
            <div className="step-icon" aria-hidden="true">💬</div>
            <h3>Tag @EasyOrder</h3>
            <p>
              Drop a message like "@EasyOrder get biryani for 6 under ₹3000" in your WhatsApp group. The AI parses your budget, headcount, and food preferences instantly.
            </p>
          </div>

          <div className="step-card fade-up" id="step-2">
            <div className="step-number" aria-hidden="true">2</div>
            <div className="step-icon" aria-hidden="true">🎨</div>
            <h3>Collaborate on Canvas</h3>
            <p>
              Everyone gets a shared link to the Planning Canvas. Add items from Swiggy Food and Instamart, adjust quantities, and watch the cart update in real-time.
            </p>
          </div>

          <div className="step-card fade-up" id="step-3">
            <div className="step-number" aria-hidden="true">3</div>
            <div className="step-icon" aria-hidden="true">🚀</div>
            <h3>Host Checks Out</h3>
            <p>
              The host validates stock and prices, logs in via Swiggy OAuth, and completes sequential checkout — Food first, then Instamart. Two deliveries, one shared decision.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
