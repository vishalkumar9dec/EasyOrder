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
    <main className="app-shell">
      <section className="control-band" aria-label="Mock scenario controls">
        <div className="brand">
          <span className="mark" aria-hidden="true">
            EO
          </span>
          <div>
            <p className="eyebrow">EasyOrder playground</p>
            <h1>Local group order canvas</h1>
          </div>
        </div>

        <label className="select-field">
          <span>Use case</span>
          <select value={scenario.id} onChange={(event) => selectScenario(event.target.value)}>
            {scenarios.map((option) => (
              <option key={option.id} value={option.id}>
                {option.title}
              </option>
            ))}
          </select>
        </label>

        <div className="role-toggle" aria-label="Perspective">
          <button
            className={isHost ? 'selected' : ''}
            type="button"
            onClick={() => setRole('host')}
            aria-pressed={isHost}
          >
            Host
          </button>
          <button
            className={!isHost ? 'selected' : ''}
            type="button"
            onClick={() => setRole('guest')}
            aria-pressed={!isHost}
          >
            Guest
          </button>
        </div>
      </section>

      <section className="prompt-strip" aria-label="Mock prompt">
        <span>@</span>
        <p>{scenario.prompt}</p>
      </section>

      <section className="dashboard" aria-label="Planning canvas">
        <aside className="summary-panel" aria-label="Session summary">
          <div>
            <p className="section-label">Budget</p>
            <strong>{formatCurrency(scenario.budgetLimit)}</strong>
            <span>{scenario.headcount} people</span>
          </div>
          <div>
            <p className="section-label">Cart total</p>
            <strong className={total > scenario.budgetLimit ? 'danger' : ''}>
              {formatCurrency(total)}
            </strong>
            <span>{total > scenario.budgetLimit ? 'Over budget' : 'Within budget'}</span>
          </div>
          <div>
            <p className="section-label">Preference</p>
            <strong>{scenario.dietaryPreference}</strong>
            <span>{role === 'host' ? 'Checkout controls visible' : 'Checkout hidden'}</span>
          </div>
        </aside>

        <section className="cart-panel" aria-label="Consolidated cart">
          <div className="panel-header">
            <div>
              <p className="section-label">Consolidated cart</p>
              <h2>{scenario.title}</h2>
            </div>
            <div className="add-actions">
              <button type="button" onClick={() => addItem('food')}>
                + Food
              </button>
              <button type="button" onClick={() => addItem('instamart')}>
                + Instamart
              </button>
            </div>
          </div>

          <div className="cart-list">
            {cart.map((item) => (
              <article className={`cart-row ${item.issue ? 'has-issue' : ''}`} key={item.id}>
                <div>
                  <p className="item-name">{item.name}</p>
                  <div className="item-meta">
                    <span>{formatVertical(item.vertical)}</span>
                    <span>{item.dietaryTag}</span>
                    <span>{formatCurrency(item.unitPrice)}</span>
                  </div>
                  {item.substitute ? <p className="substitute">Substitute: {item.substitute}</p> : null}
                </div>

                <div className="quantity-control">
                  <button
                    type="button"
                    aria-label={`Decrease ${item.name}`}
                    onClick={() => setQuantity(item.id, item.quantity - 1)}
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
                    onChange={(event) => setQuantity(item.id, Number(event.target.value))}
                  />
                  <button
                    type="button"
                    aria-label={`Increase ${item.name}`}
                    onClick={() => setQuantity(item.id, item.quantity + 1)}
                  >
                    +
                  </button>
                </div>
              </article>
            ))}
          </div>
        </section>

        <aside className="status-panel" aria-label="Warnings and checkout">
          <section>
            <p className="section-label">Warnings</p>
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
            <p className="section-label">Mock checkout</p>
            {isHost ? (
              <>
                <button className="checkout-button" type="button" onClick={() => setCheckoutRan(true)}>
                  Validate checkout
                </button>
                <CheckoutState result={checkoutResult} />
              </>
            ) : (
              <p className="guest-note">Guests can edit the cart but cannot validate checkout.</p>
            )}
          </section>
        </aside>
      </section>
    </main>
  );
}

function CheckoutState({ result }: { result: CheckoutResult | undefined }) {
  if (!result) {
    return <p className="checkout-state">Status: {statusLabel.idle}</p>;
  }

  return (
    <div className={`checkout-result ${result.status}`}>
      <span>{statusLabel[result.status]}</span>
      <strong>{result.title}</strong>
      <p>{result.detail}</p>
      {result.foodCheckoutUrl ? <a href={result.foodCheckoutUrl}>Food mock checkout</a> : null}
      {result.instamartCheckoutUrl ? (
        <a href={result.instamartCheckoutUrl}>Instamart mock checkout</a>
      ) : null}
    </div>
  );
}
