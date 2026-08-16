import { useEffect, useState } from 'react';

import {
  OrderView,
  ProfileView,
  SpendView,
  adaptOrders,
  adaptProfile,
  adaptSpend,
  fetchMe,
  fetchOrders,
  fetchProfile,
  fetchSpend,
  logout,
} from '../accountModel';
import { LoginPage } from './LoginPage';
import { ProfileCard } from './ProfileCard';
import { SpendSummary } from './SpendSummary';

type State =
  | { kind: 'loading' }
  | { kind: 'unauthenticated' }
  | { kind: 'error'; message: string }
  | {
      kind: 'ready';
      waId: string;
      orders: OrderView[];
      spend: SpendView | null;
      profile: ProfileView | null;
    };

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
        // Spend and profile are supplementary: if either fails, still show the orders.
        const [orders, spend, profile] = await Promise.all([
          fetchOrders(),
          fetchSpend().catch(() => null),
          fetchProfile().catch(() => null),
        ]);
        if (cancelled) return;
        setState({
          kind: 'ready',
          waId,
          orders: adaptOrders(orders),
          spend: spend ? adaptSpend(spend) : null,
          profile: profile ? adaptProfile(profile) : null,
        });
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
          <h1 className="account-title">My orders</h1>
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
            {state.spend && <SpendSummary spend={state.spend} />}
            {state.profile && <ProfileCard profile={state.profile} />}
            {state.orders.length === 0 ? (
              <p className="orders-empty">
                No group orders yet. Message the EasyOrder WhatsApp number — for example:
                <em> get biryani for 4 under 2000</em> — and it will appear here.
                {/* Spend is account-wide, so it can be non-zero while this list is empty. */}
                {state.spend && !state.spend.isEmpty && (
                  <>
                    {' '}
                    Your single-restaurant orders are on <a href="/orders/live">Live orders</a>.
                  </>
                )}
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
