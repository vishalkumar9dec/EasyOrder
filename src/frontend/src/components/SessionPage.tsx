import { useCallback, useEffect, useMemo, useState } from 'react';

import {
  formatCurrency,
  formatVertical,
  getCartItemSourceText,
  type CartItem,
} from '../playgroundModel';
import {
  adaptSessionBootstrap,
  getBudgetStatus,
  getItemWarnings,
  getRoleLabel,
  getSessionHealthLabel,
  getWarningTitle,
  type ApiSessionWarning,
  type ApiSessionBootstrap,
  type SessionBootstrapViewModel,
} from '../sessionBootstrap';
import { createCartItem, deleteCartItem, updateCartItem } from '../sessionCartApi';
import { useSupabaseCartRealtime } from '../useSupabaseCartRealtime';

type LoadState =
  | { status: 'loading' }
  | { status: 'ready'; session: SessionBootstrapViewModel }
  | { status: 'unauthorized' }
  | { status: 'not-found' }
  | { status: 'error'; message: string };

export function SessionPage({ sessionId, token }: { sessionId: string; token: string | null }) {
  const [state, setState] = useState<LoadState>({ status: 'loading' });
  const handleSessionChange = useCallback((session: SessionBootstrapViewModel) => {
    setState({ status: 'ready', session });
  }, []);

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
        {state.status === 'ready' && (
          <SessionCanvas
            session={state.session}
            token={token}
            onSessionChange={handleSessionChange}
          />
        )}
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

function SessionCanvas({
  session,
  token,
  onSessionChange,
}: {
  session: SessionBootstrapViewModel;
  token: string | null;
  onSessionChange: (session: SessionBootstrapViewModel) => void;
}) {
  const cartCount = session.cart.reduce((sum, item) => sum + item.quantity, 0);
  const budget = getBudgetStatus(session);
  const isHost = session.role === 'host';
  const warnings = useMemo(() => session.warnings, [session.warnings]);
  const [mutationError, setMutationError] = useState<string | null>(null);
  const [isMutating, setIsMutating] = useState(false);
  const { connectionState } = useSupabaseCartRealtime({
    sessionId: session.sessionId,
    token,
    onSnapshot: onSessionChange,
  });

  async function applyMutation(action: () => Promise<SessionBootstrapViewModel>) {
    if (!token) {
      setMutationError('Session token is missing.');
      return;
    }
    setIsMutating(true);
    setMutationError(null);
    try {
      onSessionChange(await action());
    } catch {
      setMutationError('Cart update failed. Refresh the session and try again.');
    } finally {
      setIsMutating(false);
    }
  }

  function addFoodItem() {
    if (!token) {
      return;
    }
    void applyMutation(() =>
      createCartItem(session.sessionId, token, {
        name: 'Manual paneer rolls',
        quantity: 1,
        price: 180,
        dietary_tag: 'VEG',
        vertical: 'food',
        restaurant_id: 'rest-manual-restaurant',
        restaurant_name: 'Manual restaurant',
      }),
    );
  }

  function addInstamartItem() {
    if (!token) {
      return;
    }
    void applyMutation(() =>
      createCartItem(session.sessionId, token, {
        name: 'Manual cola bottle',
        quantity: 1,
        price: 110,
        dietary_tag: 'VEG',
        vertical: 'instamart',
        brand_name: 'Manual brand',
        source_label: 'Manual Instamart source',
      }),
    );
  }

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
      <div className={`realtime-strip ${connectionState}`}>
        <span>Realtime {connectionState}</span>
        <span>Cart edits sync through the session API.</span>
      </div>

      <div className="score-strip session-score-strip">
        <ScoreCard label="Total" value={formatCurrency(session.total)} tone={session.total > session.budgetLimit ? 'danger' : 'good'} />
        <ScoreCard label="Budget" value={formatCurrency(session.budgetLimit)} tone="muted" />
        <ScoreCard label="Items" value={String(cartCount)} tone="muted" />
        <ScoreCard label="People" value={String(session.headcount)} tone="muted" />
      </div>

      <SessionAlertStrip session={session} />

      <div className="session-layout session-route-layout">
        <aside className="session-side-panel">
          <div className={`budget-section ${budget.hasWarning ? 'attention' : ''}`}>
            <div className="budget-header">
              <span className="budget-label">Budget used</span>
              <span className="budget-percent">{budget.percent}%</span>
            </div>
            <div className="meter-track">
              <div className="meter-fill" style={{ width: `${budget.percent}%` }} />
            </div>
            <p className={`budget-remaining ${budget.isOverBudget ? 'over' : ''}`}>
              {budget.isOverBudget
                ? `${formatCurrency(Math.abs(budget.delta))} over budget`
                : `${formatCurrency(budget.delta)} remaining`}
            </p>
            {budget.hasWarning && (
              <p className="budget-note">
                Budget warning only. Cart editing remains open for guests and host.
              </p>
            )}
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
            <div className="session-cart-actions">
              <button type="button" onClick={addFoodItem} disabled={isMutating}>+ Food</button>
              <button type="button" onClick={addInstamartItem} disabled={isMutating}>+ Instamart</button>
            </div>
          </div>
          {mutationError && <p className="session-error">{mutationError}</p>}
          <div className="cart-list">
            {session.cart.map((item) => (
              <SessionCartItem
                key={`${item.id}-${item.apiId ?? 'local'}`}
                item={item}
                session={session}
                isMutating={isMutating}
                onQuantityChange={(quantity) => {
                  if (item.apiId === undefined || !token) {
                    return;
                  }
                  void applyMutation(() => updateCartItem(session.sessionId, token, item.apiId as number, { quantity }));
                }}
                onDelete={() => {
                  if (item.apiId === undefined || !token) {
                    return;
                  }
                  void applyMutation(() => deleteCartItem(session.sessionId, token, item.apiId as number));
                }}
              />
            ))}
            {session.cart.length === 0 && <p className="session-empty">No recommended items yet.</p>}
          </div>
        </div>

        <aside className="session-side-panel">
          <div className="warnings-panel">
            <p className="warnings-title">Signals</p>
            {warnings.length === 0 && !budget.hasWarning && session.degradedVerticals.length === 0 && (
              <div className="warning-item calm">No blocking warnings.</div>
            )}
            {budget.hasWarning && !warnings.some((warning) => warning.code === 'BUDGET_EXCEEDED') && (
              <WarningCard
                warning={{
                  code: 'BUDGET_EXCEEDED',
                  message: `${formatCurrency(Math.abs(budget.delta))} over budget.`,
                }}
              />
            )}
            {warnings.map((warning) => (
              <WarningCard key={`${warning.code}-${warning.item_id ?? warning.message}`} warning={warning} />
            ))}
            {session.degradedVerticals.length > 0 && (
              <div className="degraded-badges" aria-label="Degraded verticals">
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

function SessionAlertStrip({ session }: { session: SessionBootstrapViewModel }) {
  const budget = getBudgetStatus(session);
  const dietaryWarnings = session.cart.filter((item) => getItemWarnings(item, session).length > 0);
  const alerts = [
    budget.hasWarning ? `${formatCurrency(Math.abs(budget.delta))} budget review` : null,
    dietaryWarnings.length > 0 ? `${dietaryWarnings.length} dietary flag${dietaryWarnings.length > 1 ? 's' : ''}` : null,
    session.degradedVerticals.length > 0
      ? `${session.degradedVerticals.map(formatVertical).join(', ')} degraded`
      : null,
  ].filter(Boolean);

  if (alerts.length === 0) {
    return null;
  }

  return (
    <div className="session-alert-strip" aria-label="Session warnings">
      {alerts.map((alert) => (
        <span key={alert}>{alert}</span>
      ))}
    </div>
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

function SessionCartItem({
  item,
  session,
  isMutating,
  onQuantityChange,
  onDelete,
}: {
  item: CartItem;
  session: SessionBootstrapViewModel;
  isMutating: boolean;
  onQuantityChange: (quantity: number) => void;
  onDelete: () => void;
}) {
  const itemWarnings = getItemWarnings(item, session);
  return (
    <article className={`cart-item session-cart-item ${itemWarnings.length > 0 ? 'attention' : ''}`} id={`cart-${item.id}`}>
      <div className="session-item-image" aria-hidden="true">
        {item.vertical === 'food' ? 'Food' : 'IM'}
      </div>
      <div className="cart-item-info">
        <p className="cart-item-name">{item.name}</p>
        <p className="cart-item-source">{getCartItemSourceText(item)}</p>
        {itemWarnings.length > 0 && (
          <div className="item-warning-list">
            {itemWarnings.map((warning) => (
              <span key={`${item.id}-${warning.code}`}>{getWarningTitle(warning)}</span>
            ))}
          </div>
        )}
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
          <div className="session-qty-controls" aria-label={`${item.name} quantity controls`}>
            <button
              type="button"
              onClick={() => onQuantityChange(item.quantity - 1)}
              disabled={isMutating || item.apiId === undefined}
            >
              -
            </button>
            <span className="session-qty">Qty {item.quantity}</span>
            <button
              type="button"
              onClick={() => onQuantityChange(item.quantity + 1)}
              disabled={isMutating || item.apiId === undefined || item.quantity >= 99}
            >
              +
            </button>
            <button
              type="button"
              className="session-delete-button"
              onClick={onDelete}
              disabled={isMutating || item.apiId === undefined}
            >
              Remove
            </button>
          </div>
        </div>
      </div>
    </article>
  );
}

function WarningCard({ warning }: { warning: ApiSessionWarning }) {
  return (
    <div className={`warning-item ${warning.code.toLowerCase()}`}>
      <span className="warning-heading">{getWarningTitle(warning)}</span>
      <span>{warning.message}</span>
      {warning.vertical && <span className="warning-meta">{formatVertical(warning.vertical)}</span>}
    </div>
  );
}
