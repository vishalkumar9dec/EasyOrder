import { useMemo, useState } from 'react';

import {
  addManualItem,
  calculateCartTotal,
  cloneCart,
  formatCurrency,
  formatVertical,
  getCartItemSourceText,
  getCheckoutResult,
  getScenarioById,
  getWarnings,
  scenarios,
  updateItemQuantity,
  type CartItem,
  type CheckoutResult,
  type DietaryTag,
  type Role,
  type Vertical,
} from '../playgroundModel';

import biryaniImg from '../assets/dish-biryani.png';
import paneerImg from '../assets/dish-paneer-rolls.png';
import pizzaImg from '../assets/dish-pizza.png';
import momosImg from '../assets/dish-momos.png';
import dosaImg from '../assets/dish-dosa.png';

const dishImages: Record<string, string> = {
  'food-biryani': biryaniImg,
  'food-paneer-roll': paneerImg,
  'food-pizza': pizzaImg,
  'food-brownie': pizzaImg,
  'food-paneer': paneerImg,
  'food-kebab': biryaniImg,
  'food-dosa': dosaImg,
  'food-idli': dosaImg,
  'food-noodles': momosImg,
  'food-momos': momosImg,
  'food-sushi': momosImg,
  'im-cola': paneerImg,
  'im-juice': paneerImg,
  'im-lassi': paneerImg,
  'im-plates': pizzaImg,
  'im-soda': pizzaImg,
  'im-icecream': dosaImg,
  'im-water': dosaImg,
};

const statusLabel: Record<string, string> = {
  idle: 'Not run',
  ready: 'Ready',
  blocked: 'Blocked',
  partial: 'Partial',
};

const statusTone: Record<string, string> = {
  ready: 'good',
  blocked: 'danger',
  partial: 'warn',
  idle: 'muted',
};

export function SessionDemo() {
  const [scenarioId, setScenarioId] = useState(scenarios[0].id);
  const [role, setRole] = useState<Role>('host');
  const [dietaryPreference, setDietaryPreference] = useState<DietaryTag>(scenarios[0].dietaryPreference);
  const [checkoutRan, setCheckoutRan] = useState(false);
  const scenario = getScenarioById(scenarioId);
  const [cart, setCart] = useState<CartItem[]>(() => cloneCart(scenario.cart));

  const total = useMemo(() => calculateCartTotal(cart), [cart]);
  const warnings = useMemo(
    () => getWarnings(scenario, cart, dietaryPreference),
    [scenario, cart, dietaryPreference],
  );
  const isHost = role === 'host';
  const checkoutResult = checkoutRan ? getCheckoutResult(scenario, cart, dietaryPreference) : undefined;
  const budgetDelta = scenario.budgetLimit - total;
  const budgetPercent = Math.min(100, Math.round((total / scenario.budgetLimit) * 100));
  const cartCount = cart.reduce((sum, item) => sum + item.quantity, 0);

  function selectScenario(nextId: string) {
    const next = getScenarioById(nextId);
    setScenarioId(next.id);
    setCart(cloneCart(next.cart));
    setDietaryPreference(next.dietaryPreference);
    setCheckoutRan(false);
  }

  function setQuantity(itemId: string, quantity: number) {
    setCart((c) => updateItemQuantity(c, itemId, quantity));
    setCheckoutRan(false);
  }

  function selectDietaryPreference(nextPreference: DietaryTag) {
    setDietaryPreference(nextPreference);
    setCheckoutRan(false);
  }

  function addItem(vertical: Vertical) {
    setCart((c) => addManualItem(c, vertical));
    setCheckoutRan(false);
  }

  return (
    <section className="session-demo" id="demo" aria-label="Interactive demo">
      <div className="section-container">
        <div className="demo-header fade-up">
          <p className="section-eyebrow">Interactive Demo</p>
          <h2 className="section-title">See EasyOrder in action</h2>
          <p className="demo-subtitle">
            Switch between 7 real-world scenarios — budget limits, dietary mismatches, degraded services, stock changes — and watch the canvas adapt.
          </p>
        </div>

        {/* Scenario tabs */}
        <div className="scenario-tabs fade-up" aria-label="Use case scenarios">
          {scenarios.map((s) => (
            <button
              key={s.id}
              className={`scenario-tab ${s.id === scenarioId ? 'active' : ''}`}
              onClick={() => selectScenario(s.id)}
              aria-pressed={s.id === scenarioId}
              id={`scenario-${s.id}`}
            >
              {s.shortLabel}
            </button>
          ))}
        </div>

        {/* Role toggle */}
        <div className="role-toggle fade-up" aria-label="Perspective switcher">
          <button
            className={`role-btn ${isHost ? 'active' : ''}`}
            onClick={() => setRole('host')}
            aria-pressed={isHost}
            id="role-host"
          >
            👑 Host
          </button>
          <button
            className={`role-btn ${!isHost ? 'active' : ''}`}
            onClick={() => setRole('guest')}
            aria-pressed={!isHost}
            id="role-guest"
          >
            👤 Guest
          </button>
        </div>

        {/* Prompt board */}
        <div className="prompt-card fade-up" aria-label="WhatsApp prompt">
          <p className="prompt-label">@EasyOrder mention detected</p>
          <p className="prompt-text">{scenario.prompt}</p>
        </div>

        {/* Score strip */}
        <div className="score-strip fade-up" style={{ marginTop: 16 }}>
          <ScoreCard label="Total" value={formatCurrency(total)} tone={total > scenario.budgetLimit ? 'danger' : 'good'} />
          <ScoreCard label="Budget" value={formatCurrency(scenario.budgetLimit)} tone="muted" />
          <ScoreCard label="Items" value={String(cartCount)} tone="muted" />
          <ScoreCard label="People" value={String(scenario.headcount)} tone="muted" />
        </div>

        {/* Main session layout */}
        <div className="session-layout" style={{ marginTop: 16 }}>
          {/* Left sidebar */}
          <div>
            {/* Budget meter */}
            <div className="budget-section fade-up">
              <div className="budget-header">
                <span className="budget-label">Budget used</span>
                <span className="budget-percent">{budgetPercent}%</span>
              </div>
              <div className="meter-track">
                <div
                  className="meter-fill"
                  style={{ width: `${budgetPercent}%` }}
                  role="progressbar"
                  aria-valuenow={budgetPercent}
                  aria-valuemin={0}
                  aria-valuemax={100}
                />
              </div>
              <p className={`budget-remaining ${budgetDelta < 0 ? 'over' : ''}`}>
                {budgetDelta < 0
                  ? `${formatCurrency(Math.abs(budgetDelta))} over budget`
                  : `${formatCurrency(budgetDelta)} remaining`}
              </p>
            </div>

            {/* Session info */}
            <div className="session-info fade-up" style={{ marginTop: 12 }}>
              <div className="info-row">
                <span className="info-label">Preference</span>
                <span className="info-value">{dietaryPreference}</span>
              </div>
              <div className="info-row">
                <span className="info-label">Role</span>
                <span className="info-value">{isHost ? '👑 Host' : '👤 Guest'}</span>
              </div>
              <div className="info-row">
                <span className="info-label">Verticals</span>
                <span className={`info-value ${scenario.degradedVerticals.length ? 'warn' : 'good'}`}>
                  {scenario.degradedVerticals.length ? 'Degraded' : 'Healthy'}
                </span>
              </div>
            </div>

            <div className="preference-control fade-up" aria-label="Food preference" style={{ marginTop: 12 }}>
              <p className="preference-title">Food preference</p>
              <div className="preference-buttons">
                <button
                  className={`preference-btn ${dietaryPreference === 'ANY' ? 'active' : ''}`}
                  onClick={() => selectDietaryPreference('ANY')}
                  aria-pressed={dietaryPreference === 'ANY'}
                  id="preference-any"
                >
                  Any
                </button>
                <button
                  className={`preference-btn ${dietaryPreference === 'VEG' ? 'active' : ''}`}
                  onClick={() => selectDietaryPreference('VEG')}
                  aria-pressed={dietaryPreference === 'VEG'}
                  id="preference-veg"
                >
                  Veg
                </button>
                <button
                  className={`preference-btn ${dietaryPreference === 'NON-VEG' ? 'active' : ''}`}
                  onClick={() => selectDietaryPreference('NON-VEG')}
                  aria-pressed={dietaryPreference === 'NON-VEG'}
                  id="preference-non-veg"
                >
                  Non-veg
                </button>
              </div>
            </div>
          </div>

          {/* Cart area */}
          <div className="cart-area fade-up">
            <div className="cart-header">
              <h3 className="cart-title">Consolidated Cart</h3>
              <div className="cart-actions">
                <button className="btn-add btn-add-food" onClick={() => addItem('food')} id="add-food">
                  + Food
                </button>
                <button className="btn-add btn-add-im" onClick={() => addItem('instamart')} id="add-instamart">
                  + Instamart
                </button>
              </div>
            </div>

            <div className="cart-list">
              {cart.map((item) => (
                <CartItemCard
                  key={item.id}
                  item={item}
                  onQuantityChange={(q) => setQuantity(item.id, q)}
                />
              ))}
              {cart.length === 0 && (
                <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '32px 0' }}>
                  Cart is empty. Add items above.
                </p>
              )}
            </div>
          </div>

          {/* Right sidebar: warnings + checkout */}
          <div>
            {/* Warnings */}
            <div className="warnings-panel fade-up">
              <p className="warnings-title">⚠ Signals</p>
              {warnings.map((w) => (
                <div key={w} className="warning-item">{w}</div>
              ))}
              {scenario.degradedVerticals.length > 0 && (
                <div className="degraded-badges">
                  {scenario.degradedVerticals.map((v) => (
                    <span key={v} className="degraded-badge">
                      {formatVertical(v)} degraded
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Checkout */}
            <div className="checkout-section fade-up" style={{ marginTop: 12 }}>
              <p className="checkout-title">Checkout</p>
              {isHost ? (
                <>
                  <button
                    className="checkout-btn"
                    onClick={() => setCheckoutRan(true)}
                    id="validate-checkout"
                  >
                    Validate Checkout
                  </button>
                  <CheckoutState result={checkoutResult} />
                </>
              ) : (
                <p className="guest-note">
                  Guests can edit the cart. Only the host can validate and checkout.
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function ScoreCard({ label, value, tone }: { label: string; value: string; tone: string }) {
  return (
    <div className="score-card">
      <span className="score-label">{label}</span>
      <div className={`score-value ${tone}`}>{value}</div>
    </div>
  );
}

function CartItemCard({
  item,
  onQuantityChange,
}: {
  item: CartItem;
  onQuantityChange: (q: number) => void;
}) {
  const lineTotal = item.quantity * item.unitPrice;
  const img = dishImages[item.id] || biryaniImg;

  return (
    <article className={`cart-item ${item.issue ? 'has-issue' : ''}`} id={`cart-${item.id}`}>
      <img className="cart-item-image" src={img} alt={item.name} loading="lazy" />

      <div className="cart-item-info">
        <p className="cart-item-name">{item.name}</p>
        <p className="cart-item-source">{getCartItemSourceText(item)}</p>
        <div className="cart-item-tags">
          <span className={`tag ${item.vertical === 'food' ? 'tag-food' : 'tag-im'}`}>
            {formatVertical(item.vertical)}
          </span>
          <span className={`tag ${item.dietaryTag === 'NON-VEG' ? 'tag-nonveg' : 'tag-veg'}`}>
            {item.dietaryTag}
          </span>
          {item.issue && (
            <span className="tag" style={{ color: 'var(--danger)', borderColor: 'rgba(239,68,68,0.3)' }}>
              {item.issue === 'unavailable' ? '⛔ Unavailable' : '💰 Price changed'}
            </span>
          )}
        </div>
        {item.substitute && (
          <p className="cart-item-substitute">↳ Substitute: {item.substitute}</p>
        )}
        <div className="cart-item-bottom">
          <span className="cart-item-price">{formatCurrency(lineTotal)}</span>
          <div className="qty-control">
            <button
              className="qty-btn"
              onClick={() => onQuantityChange(item.quantity - 1)}
              aria-label={`Decrease ${item.name}`}
            >
              −
            </button>
            <input
              className="qty-input"
              type="number"
              inputMode="numeric"
              min="0"
              max="99"
              value={item.quantity}
              onChange={(e) => onQuantityChange(Number(e.target.value))}
              aria-label={`${item.name} quantity`}
            />
            <button
              className="qty-btn"
              onClick={() => onQuantityChange(item.quantity + 1)}
              aria-label={`Increase ${item.name}`}
            >
              +
            </button>
          </div>
        </div>
      </div>
    </article>
  );
}

function CheckoutState({ result }: { result: CheckoutResult | undefined }) {
  if (!result) {
    return <p style={{ color: 'var(--text-muted)', fontSize: 'var(--text-caption)', marginTop: 10 }}>Status: Not run</p>;
  }

  const tone = statusTone[result.status] || 'muted';

  return (
    <div className={`checkout-result ${tone}`}>
      <span className="checkout-status">{statusLabel[result.status]}</span>
      <p className="checkout-result-title">{result.title}</p>
      <p className="checkout-result-detail">{result.detail}</p>
      <div className="checkout-links">
        {result.foodCheckoutUrl && (
          <MockCheckoutLink href={result.foodCheckoutUrl} label="Food checkout" />
        )}
        {result.instamartCheckoutUrl && (
          <MockCheckoutLink href={result.instamartCheckoutUrl} label="Instamart checkout" />
        )}
      </div>
    </div>
  );
}

function MockCheckoutLink({ href, label }: { href: string; label: string }) {
  return (
    <a
      href={href}
      onClick={(event) => event.preventDefault()}
      aria-label={`${label} mock link`}
      title={href}
    >
      {label === 'Food checkout' ? '🍽' : '🛒'} {label} →
    </a>
  );
}
