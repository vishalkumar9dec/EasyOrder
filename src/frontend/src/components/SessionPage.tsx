import { useEffect, useMemo, useState } from 'react';

import {
  formatCurrency,
  formatVertical,
  getCartItemSourceText,
  type CartItem,
} from '../playgroundModel';
import {
  adaptSessionBootstrap,
  getRoleLabel,
  getSessionHealthLabel,
  type ApiSessionBootstrap,
  type SessionBootstrapViewModel,
} from '../sessionBootstrap';

type LoadState =
  | { status: 'loading' }
  | { status: 'ready'; session: SessionBootstrapViewModel }
  | { status: 'unauthorized' }
  | { status: 'not-found' }
  | { status: 'error'; message: string };

export function SessionPage({ sessionId, token }: { sessionId: string; token: string | null }) {
  const [state, setState] = useState<LoadState>({ status: 'loading' });

  useEffect(() => {
    let cancelled = false;

    async function loadSession() {
      if (!token) {
        setState({ status: 'unauthorized' });
        return;
      }

      setState({ status: 'loading' });
      try {
        const response = await fetch(`/api/session/${sessionId}?token=${encodeURIComponent(token)}`);
        if (cancelled) {
          return;
        }
        if (response.status === 401) {
          setState({ status: 'unauthorized' });
          return;
        }
        if (response.status === 404) {
          setState({ status: 'not-found' });
          return;
        }
        if (!response.ok) {
          setState({ status: 'error', message: 'Session could not be loaded.' });
          return;
        }

        const payload = (await response.json()) as ApiSessionBootstrap;
        setState({ status: 'ready', session: adaptSessionBootstrap(payload) });
      } catch {
        if (!cancelled) {
          setState({ status: 'error', message: 'Session could not be loaded.' });
        }
      }
    }

    void loadSession();

    return () => {
      cancelled = true;
    };
  }, [sessionId, token]);

  return (
    <main className="session-page">
      <div className="session-shell">
        <a className="session-brand" href="/">
          Easy<span>Order</span>
        </a>
        {state.status === 'loading' && <SessionState title="Loading session" detail="Fetching the latest planning canvas." />}
        {state.status === 'unauthorized' && (
          <SessionState title="Link not authorized" detail="Use the latest EasyOrder link from WhatsApp." tone="danger" />
        )}
        {state.status === 'not-found' && (
          <SessionState title="Session not found" detail="This planning canvas is no longer available." tone="warn" />
        )}
        {state.status === 'error' && (
          <SessionState title="Could not load session" detail={state.message} tone="danger" />
        )}
        {state.status === 'ready' && <SessionCanvas session={state.session} />}
      </div>
    </main>
  );
}

function SessionState({
  title,
  detail,
  tone = 'muted',
}: {
  title: string;
  detail: string;
  tone?: 'muted' | 'warn' | 'danger';
}) {
  return (
    <section className={`session-state ${tone}`}>
      <p className="section-eyebrow">Planning Canvas</p>
      <h1>{title}</h1>
      <p>{detail}</p>
    </section>
  );
}

function SessionCanvas({ session }: { session: SessionBootstrapViewModel }) {
  const cartCount = session.cart.reduce((sum, item) => sum + item.quantity, 0);
  const budgetDelta = session.budgetLimit - session.total;
  const budgetPercent = Math.min(100, Math.round((session.total / session.budgetLimit) * 100));
  const isHost = session.role === 'host';
  const warnings = useMemo(() => session.warnings, [session.warnings]);

  return (
    <section className="session-canvas" aria-label="EasyOrder session planning canvas">
      <div className="session-hero-panel">
        <div>
          <p className="section-eyebrow">Live Session</p>
          <h1>Planning canvas</h1>
          <p className="session-subtitle">
            Review the cart, source context, and session status before checkout.
          </p>
        </div>
        <div className="session-role-pill">{getRoleLabel(session.role)}</div>
      </div>

      <div className="score-strip session-score-strip">
        <ScoreCard label="Total" value={formatCurrency(session.total)} tone={session.total > session.budgetLimit ? 'danger' : 'good'} />
        <ScoreCard label="Budget" value={formatCurrency(session.budgetLimit)} tone="muted" />
        <ScoreCard label="Items" value={String(cartCount)} tone="muted" />
        <ScoreCard label="People" value={String(session.headcount)} tone="muted" />
      </div>

      <div className="session-layout session-route-layout">
        <aside className="session-side-panel">
          <div className="budget-section">
            <div className="budget-header">
              <span className="budget-label">Budget used</span>
              <span className="budget-percent">{budgetPercent}%</span>
            </div>
            <div className="meter-track">
              <div className="meter-fill" style={{ width: `${budgetPercent}%` }} />
            </div>
            <p className={`budget-remaining ${budgetDelta < 0 ? 'over' : ''}`}>
              {budgetDelta < 0
                ? `${formatCurrency(Math.abs(budgetDelta))} over budget`
                : `${formatCurrency(budgetDelta)} remaining`}
            </p>
          </div>

          <div className="session-info">
            <InfoRow label="Preference" value={session.dietaryPreference} />
            <InfoRow label="Role" value={getRoleLabel(session.role)} />
            <InfoRow
              label="Verticals"
              value={getSessionHealthLabel(session.status)}
              tone={session.status === 'DEGRADED' ? 'warn' : 'good'}
            />
          </div>
        </aside>

        <div className="cart-area">
          <div className="cart-header">
            <h2 className="cart-title">Consolidated Cart</h2>
          </div>
          <div className="cart-list">
            {session.cart.map((item) => (
              <SessionCartItem key={item.id} item={item} />
            ))}
            {session.cart.length === 0 && <p className="session-empty">No recommended items yet.</p>}
          </div>
        </div>

        <aside className="session-side-panel">
          <div className="warnings-panel">
            <p className="warnings-title">Signals</p>
            {warnings.length === 0 && <div className="warning-item">No blocking warnings.</div>}
            {warnings.map((warning) => (
              <div key={warning} className="warning-item">{warning}</div>
            ))}
            {session.degradedVerticals.length > 0 && (
              <div className="degraded-badges">
                {session.degradedVerticals.map((vertical) => (
                  <span key={vertical} className="degraded-badge">
                    {formatVertical(vertical)} degraded
                  </span>
                ))}
              </div>
            )}
          </div>

          <div className="checkout-section">
            <p className="checkout-title">Checkout</p>
            {isHost ? (
              <div className={`checkout-result ${session.checkoutEligible ? 'good' : 'warn'}`}>
                <span className="checkout-status">{session.checkoutEligible ? 'Ready' : 'Not ready'}</span>
                <p className="checkout-result-title">
                  {session.checkoutEligible ? 'Host checkout eligible' : 'Checkout unavailable'}
                </p>
                <p className="checkout-result-detail">
                  Source-attributed cart is loaded. Final stock and price validation comes later.
                </p>
              </div>
            ) : (
              <p className="guest-note">
                Guests can review the cart. Only the host can validate and checkout.
              </p>
            )}
          </div>
        </aside>
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

function InfoRow({ label, value, tone }: { label: string; value: string; tone?: string }) {
  return (
    <div className="info-row">
      <span className="info-label">{label}</span>
      <span className={`info-value ${tone ?? ''}`}>{value}</span>
    </div>
  );
}

function SessionCartItem({ item }: { item: CartItem }) {
  return (
    <article className="cart-item session-cart-item" id={`cart-${item.id}`}>
      <div className="session-item-image" aria-hidden="true">
        {item.vertical === 'food' ? 'Food' : 'IM'}
      </div>
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
        </div>
        <div className="cart-item-bottom">
          <span className="cart-item-price">{formatCurrency(item.quantity * item.unitPrice)}</span>
          <span className="session-qty">Qty {item.quantity}</span>
        </div>
      </div>
    </article>
  );
}
