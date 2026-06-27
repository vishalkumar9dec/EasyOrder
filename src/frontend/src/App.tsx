import { useMemo, useState } from 'react';

import {
  addManualItem,
  calculateCartTotal,
  cloneCart,
  formatCurrency,
  formatVertical,
  getScenarioById,
  getWarnings,
  scenarios,
  updateItemQuantity,
  type CartItem,
  type CheckoutResult,
  type Role,
  type Vertical,
} from './playgroundModel';

const statusLabel = {
  idle: 'Not run',
  ready: 'Ready',
  blocked: 'Blocked',
  partial: 'Partial',
};

const statusTone = {
  ready: 'good',
  blocked: 'danger',
  partial: 'warn',
  idle: 'muted',
};

export function App() {
  const [scenarioId, setScenarioId] = useState(scenarios[0].id);
  const [role, setRole] = useState<Role>('host');
  const [checkoutRan, setCheckoutRan] = useState(false);
  const scenario = getScenarioById(scenarioId);
  const [cart, setCart] = useState<CartItem[]>(() => cloneCart(scenario.cart));

  const total = useMemo(() => calculateCartTotal(cart), [cart]);
  const warnings = useMemo(() => getWarnings(scenario, cart), [scenario, cart]);
  const isHost = role === 'host';
  const checkoutResult = checkoutRan ? scenario.checkoutResult : undefined;
  const budgetDelta = scenario.budgetLimit - total;
  const budgetPercent = Math.min(100, Math.round((total / scenario.budgetLimit) * 100));
  const cartCount = cart.reduce((sum, item) => sum + item.quantity, 0);

  function selectScenario(nextScenarioId: string) {
    const nextScenario = getScenarioById(nextScenarioId);
    setScenarioId(nextScenario.id);
    setCart(cloneCart(nextScenario.cart));
    setCheckoutRan(false);
  }

  function setQuantity(itemId: string, quantity: number) {
    setCart((currentCart) => updateItemQuantity(currentCart, itemId, quantity));
    setCheckoutRan(false);
  }

  function addItem(vertical: Vertical) {
    setCart((currentCart) => addManualItem(currentCart, vertical));
    setCheckoutRan(false);
  }

  return (
    <main className="club-shell">
      <section className="hero-board" aria-label="EasyOrder session board">
        <div className="hero-copy">
          <p className="kicker">WhatsApp to shared cart</p>
          <h1>EasyOrder Club</h1>
          <p className="hero-line">
            A live score room for group orders, budgets, warnings, and host checkout.
          </p>
        </div>

        <div className="prompt-board" aria-label="Active WhatsApp prompt">
          <span className="prompt-token">Mention detected</span>
          <p>{scenario.prompt}</p>
        </div>

        <div className="score-strip" aria-label="Session score">
          <ScoreCell label="Total" value={formatCurrency(total)} tone={total > scenario.budgetLimit ? 'danger' : 'good'} />
          <ScoreCell label="Budget" value={formatCurrency(scenario.budgetLimit)} />
          <ScoreCell label="Items" value={String(cartCount)} />
          <ScoreCell label="People" value={String(scenario.headcount)} />
        </div>
      </section>

      <section className="command-bar" aria-label="Playground controls">
        <div className="scenario-rail" aria-label="Use cases">
          {scenarios.map((option, index) => (
            <button
              className={option.id === scenario.id ? 'active' : ''}
              key={option.id}
              type="button"
              onClick={() => selectScenario(option.id)}
              aria-pressed={option.id === scenario.id}
            >
              <span>{String(index + 1).padStart(2, '0')}</span>
              {option.shortLabel}
            </button>
          ))}
        </div>

        <div className="role-switch" aria-label="Perspective">
          <button
            className={isHost ? 'active' : ''}
            type="button"
            onClick={() => setRole('host')}
            aria-pressed={isHost}
          >
            Host
          </button>
          <button
            className={!isHost ? 'active' : ''}
            type="button"
            onClick={() => setRole('guest')}
            aria-pressed={!isHost}
          >
            Guest
          </button>
        </div>
      </section>

      <section className="workspace" aria-label="Planning canvas">
        <aside className="session-panel" aria-label="Session status">
          <div>
            <p className="section-label">Now playing</p>
            <h2>{scenario.title}</h2>
          </div>

          <div className="budget-meter" aria-label={`Budget used ${budgetPercent} percent`}>
            <div>
              <span>Budget used</span>
              <strong>{budgetPercent}%</strong>
            </div>
            <div className="meter-track">
              <span style={{ width: `${budgetPercent}%` }} />
            </div>
            <p className={budgetDelta < 0 ? 'danger-text' : ''}>
              {budgetDelta < 0
                ? `${formatCurrency(Math.abs(budgetDelta))} over`
                : `${formatCurrency(budgetDelta)} left`}
            </p>
          </div>

          <div className="mini-ledger">
            <StatusLine label="Preference" value={scenario.dietaryPreference} />
            <StatusLine label="Role" value={isHost ? 'Host controls' : 'Guest editing'} />
            <StatusLine
              label="Verticals"
              value={scenario.degradedVerticals.length ? 'Degraded' : 'Healthy'}
              tone={scenario.degradedVerticals.length ? 'warn' : 'good'}
            />
          </div>
        </aside>

        <section className="cart-stage" aria-label="Consolidated cart">
          <div className="stage-header">
            <div>
              <p className="section-label">Order board</p>
              <h2>Ranked cart lines</h2>
            </div>
            <div className="add-actions">
              <button type="button" onClick={() => addItem('food')}>
                Add Food
              </button>
              <button type="button" onClick={() => addItem('instamart')}>
                Add Instamart
              </button>
            </div>
          </div>

          <div className="cart-list">
            {cart.map((item, index) => (
              <CartRow
                item={item}
                key={item.id}
                rank={index + 1}
                onQuantityChange={(quantity) => setQuantity(item.id, quantity)}
              />
            ))}
          </div>
        </section>

        <aside className="console-panel" aria-label="Warnings and checkout">
          <section>
            <p className="section-label">Signals</p>
            <div className="warning-list">
              {warnings.map((warning) => (
                <p key={warning}>{warning}</p>
              ))}
            </div>
            {scenario.degradedVerticals.length > 0 ? (
              <div className="degraded-list">
                {scenario.degradedVerticals.map((vertical) => (
                  <span key={vertical}>{formatVertical(vertical)} degraded</span>
                ))}
              </div>
            ) : null}
          </section>

          <section className="checkout-box">
            <p className="section-label">Host checkout</p>
            {isHost ? (
              <>
                <button className="checkout-button" type="button" onClick={() => setCheckoutRan(true)}>
                  Validate checkout
                </button>
                <CheckoutState result={checkoutResult} />
              </>
            ) : (
              <p className="guest-note">Guests can tune the cart. Checkout stays with the host.</p>
            )}
          </section>
        </aside>
      </section>
    </main>
  );
}

function ScoreCell({
  label,
  value,
  tone = 'muted',
}: {
  label: string;
  value: string;
  tone?: 'good' | 'danger' | 'muted';
}) {
  return (
    <div className={`score-cell ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function StatusLine({
  label,
  value,
  tone = 'muted',
}: {
  label: string;
  value: string;
  tone?: 'good' | 'warn' | 'muted';
}) {
  return (
    <p className={`status-line ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </p>
  );
}

function CartRow({
  item,
  rank,
  onQuantityChange,
}: {
  item: CartItem;
  rank: number;
  onQuantityChange: (quantity: number) => void;
}) {
  const lineTotal = item.quantity * item.unitPrice;

  return (
    <article className={`cart-row ${item.issue ? 'has-issue' : ''}`}>
      <div className="rank" aria-hidden="true">
        {String(rank).padStart(2, '0')}
      </div>

      <div className="item-copy">
        <p className="item-name">{item.name}</p>
        <div className="item-meta">
          <span>{formatVertical(item.vertical)}</span>
          <span>{item.dietaryTag}</span>
          <span>{formatCurrency(item.unitPrice)}</span>
        </div>
        {item.substitute ? <p className="substitute">Substitute: {item.substitute}</p> : null}
      </div>

      <div className="line-total">
        <span>Line</span>
        <strong>{formatCurrency(lineTotal)}</strong>
      </div>

      <div className="quantity-control">
        <button
          type="button"
          aria-label={`Decrease ${item.name}`}
          onClick={() => onQuantityChange(item.quantity - 1)}
        >
          -
        </button>
        <input
          aria-label={`${item.name} quantity`}
          inputMode="numeric"
          min="0"
          max="99"
          type="number"
          value={item.quantity}
          onChange={(event) => onQuantityChange(Number(event.target.value))}
        />
        <button
          type="button"
          aria-label={`Increase ${item.name}`}
          onClick={() => onQuantityChange(item.quantity + 1)}
        >
          +
        </button>
      </div>
    </article>
  );
}

function CheckoutState({ result }: { result: CheckoutResult | undefined }) {
  if (!result) {
    return <p className="checkout-state">Status: {statusLabel.idle}</p>;
  }

  return (
    <div className={`checkout-result ${statusTone[result.status]}`}>
      <span>{statusLabel[result.status]}</span>
      <strong>{result.title}</strong>
      <p>{result.detail}</p>
      <div className="checkout-links">
        {result.foodCheckoutUrl ? <a href={result.foodCheckoutUrl}>Food mock checkout</a> : null}
        {result.instamartCheckoutUrl ? (
          <a href={result.instamartCheckoutUrl}>Instamart mock checkout</a>
        ) : null}
      </div>
    </div>
  );
}
