import { useEffect, useState } from 'react';

import { OrderView, adaptOrders, fetchMe, fetchOrders, logout } from '../accountModel';
import { LoginPage } from './LoginPage';

type State =
  | { kind: 'loading' }
  | { kind: 'unauthenticated' }
  | { kind: 'error'; message: string }
  | { kind: 'ready'; waId: string; orders: OrderView[] };

export function MyOrdersPage() {
  const [state, setState] = useState<State>({ kind: 'loading' });

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const waId = await fetchMe();
        if (cancelled) return;
        if (waId === null) {
          setState({ kind: 'unauthenticated' });
          return;
        }
        const orders = await fetchOrders();
        if (cancelled) return;
        setState({ kind: 'ready', waId, orders: adaptOrders(orders) });
      } catch (err) {
        if (!cancelled) {
          setState({
            kind: 'error',
            message: err instanceof Error ? err.message : 'Could not load your orders',
          });
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (state.kind === 'unauthenticated') {
    return <LoginPage />;
  }

  return (
    <section className="account-page" aria-label="My orders">
      <div className="account-card account-card--wide">
        <div className="account-header">
          <a className="navbar-brand account-brand" href="/">
            Easy<span>Order</span>
          </a>
          {state.kind === 'ready' && (
            <button
              className="account-link-button"
              type="button"
              id="orders-logout"
              onClick={async () => {
                await logout();
                window.location.href = '/';
              }}
            >
              Log out
            </button>
          )}
        </div>
        <h1 className="account-title">My orders</h1>

        {state.kind === 'loading' && <p className="account-subtitle">Loading your orders…</p>}

        {state.kind === 'error' && (
          <p className="account-error" role="alert">
            {state.message}
          </p>
        )}

        {state.kind === 'ready' && (
          <>
            <p className="account-subtitle">
              Logged in as +{state.waId}. Same history you get on WhatsApp.
            </p>
            {state.orders.length === 0 ? (
              <p className="orders-empty">
                No orders yet. Message the EasyOrder WhatsApp number — for example:
                <em> get biryani for 4 under 2000</em> — and it will appear here.
              </p>
            ) : (
              <ol className="orders-list">
                {state.orders.map((order) => (
                  <li key={order.sessionId} className="order-card">
                    <div className="order-card-main">
                      <span className={`order-status ${order.statusClass}`}>
                        {order.statusLabel}
                      </span>
                      <p className="order-meta">
                        {order.startedLabel} · {order.itemsLabel} · {order.totalLabel}
                      </p>
                    </div>
                    <a className="order-open" href={order.reviewUrl}>
                      Open
                    </a>
                  </li>
                ))}
              </ol>
            )}
          </>
        )}
      </div>
    </section>
  );
}
