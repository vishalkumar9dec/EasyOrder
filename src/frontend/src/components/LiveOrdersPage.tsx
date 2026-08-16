import { useEffect, useState } from 'react';

import {
  ApiLiveOrders,
  LiveOrderView,
  SpendView,
  adaptLiveOrders,
  adaptSpend,
  fetchLiveOrders,
  fetchMe,
  fetchSpend,
  logout,
} from '../accountModel';
import { LoginPage } from './LoginPage';
import { SpendSummary } from './SpendSummary';

type Tab = 'scheduled' | 'ongoing' | 'historical';

type Buckets = Record<Tab, LiveOrderView[]>;

type State =
  | { kind: 'loading' }
  | { kind: 'unauthenticated' }
  | { kind: 'error'; message: string }
  | { kind: 'ready'; waId: string; buckets: Buckets; spend: SpendView | null };

const TABS: { key: Tab; label: string }[] = [
  { key: 'scheduled', label: 'Scheduled' },
  { key: 'ongoing', label: 'Ongoing' },
  { key: 'historical', label: 'Historical' },
];

function adaptBuckets(body: ApiLiveOrders): Buckets {
  return {
    scheduled: adaptLiveOrders(body.scheduled),
    ongoing: adaptLiveOrders(body.ongoing),
    historical: adaptLiveOrders(body.historical),
  };
}

export function LiveOrdersPage() {
  const [state, setState] = useState<State>({ kind: 'loading' });
  const [activeTab, setActiveTab] = useState<Tab>('scheduled');

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
        // Spend is supplementary: if it fails, still show the orders.
        const [body, spend] = await Promise.all([
          fetchLiveOrders(),
          fetchSpend().catch(() => null),
        ]);
        if (cancelled) return;
        setState({
          kind: 'ready',
          waId,
          buckets: adaptBuckets(body),
          spend: spend ? adaptSpend(spend) : null,
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

  const orders = state.kind === 'ready' ? state.buckets[activeTab] : [];

  return (
    <section className="account-page" aria-label="Orders">
      <div className="account-card account-card--wide">
        <div className="account-header">
          <h1 className="account-title">Orders</h1>
          {state.kind === 'ready' && (
            <button
              className="account-link-button"
              type="button"
              id="live-orders-logout"
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
              Logged in as +{state.waId}. Orders you placed from a named restaurant over WhatsApp.
            </p>

            {state.spend && <SpendSummary spend={state.spend} />}

            <div className="live-orders-tabs" role="tablist" aria-label="Order status">
              {TABS.map((tab) => (
                <button
                  key={tab.key}
                  type="button"
                  role="tab"
                  aria-selected={activeTab === tab.key}
                  className={`live-orders-tab ${activeTab === tab.key ? 'active' : ''}`}
                  onClick={() => setActiveTab(tab.key)}
                >
                  {tab.label} ({state.buckets[tab.key].length})
                </button>
              ))}
            </div>

            {orders.length === 0 ? (
              <p className="orders-empty">
                No {activeTab} orders yet. Message the EasyOrder WhatsApp number — for example:
                <em> order paneer tikka from MotiMahal</em> — and it will appear here.
              </p>
            ) : (
              <ol className="orders-list">
                {orders.map((order) => (
                  <li key={order.orderId} className="order-card">
                    <div className="order-card-main">
                      <span className={`order-status ${order.statusClass}`}>
                        {order.statusLabel}
                      </span>
                      <p className="order-meta">
                        {order.restaurantName} · {order.itemsLabel} · {order.totalLabel}
                      </p>
                      {order.timingLabel && <p className="order-meta">{order.timingLabel}</p>}
                    </div>
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
