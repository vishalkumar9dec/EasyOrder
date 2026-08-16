import { describe, expect, it } from 'vitest';

import {
  adaptOrder,
  adaptOrders,
  adaptProfile,
  adaptSpend,
  isValidPhoneInput,
} from './accountModel';

const order = {
  session_id: 'session_abc123',
  created_at: '2026-07-11T14:30:00+00:00',
  status: 'ACTIVE',
  item_count: 6,
  total: '2700.00',
  review_url: 'http://localhost:5173/api/r/abc12345',
};

describe('adaptOrder', () => {
  it('maps API fields to display labels', () => {
    const view = adaptOrder(order);

    expect(view.sessionId).toBe('session_abc123');
    expect(view.statusLabel).toBe('Being planned');
    expect(view.statusClass).toBe('order-status--active');
    expect(view.itemsLabel).toBe('6 items');
    expect(view.totalLabel).toBe('₹2,700.00');
    expect(view.reviewUrl).toContain('/api/r/');
    expect(view.startedLabel).not.toBe('');
  });

  it('singularizes one item and passes unknown statuses through', () => {
    const view = adaptOrder({ ...order, item_count: 1, status: 'SOMETHING_NEW' });

    expect(view.itemsLabel).toBe('1 item');
    expect(view.statusLabel).toBe('SOMETHING_NEW');
  });

  it('labels checkout and degraded states distinctly', () => {
    expect(adaptOrder({ ...order, status: 'CHECKOUT_READY' }).statusLabel).toBe(
      'Ready for checkout',
    );
    expect(adaptOrder({ ...order, status: 'ORDERED' }).statusLabel).toBe('Placed');
    expect(adaptOrder({ ...order, status: 'DEGRADED' }).statusClass).toBe(
      'order-status--degraded',
    );
  });

  it('tolerates malformed timestamps', () => {
    expect(adaptOrder({ ...order, created_at: 'not-a-date' }).startedLabel).toBe('');
  });
});

describe('adaptOrders', () => {
  it('maps lists preserving order', () => {
    const views = adaptOrders([order, { ...order, session_id: 'session_def456' }]);
    expect(views.map((v) => v.sessionId)).toEqual(['session_abc123', 'session_def456']);
  });
});

describe('isValidPhoneInput', () => {
  it('accepts common formats', () => {
    for (const phone of ['+91 99887 76655', '9988776655', '+911234567890', '91-99887-76655']) {
      expect(isValidPhoneInput(phone)).toBe(true);
    }
  });

  it('rejects junk', () => {
    for (const phone of ['', 'hello', '12ab34', '+1']) {
      expect(isValidPhoneInput(phone)).toBe(false);
    }
  });
});

describe('adaptSpend', () => {
  const spend = {
    wa_id: '919988776655',
    currency: 'INR',
    total: '1228.50',
    order_count: 3,
    group_orders: { total: '678.00', count: 1 },
    restaurant_orders: { total: '550.50', count: 2 },
  };

  it('formats the headline total and per-surface breakdown', () => {
    const view = adaptSpend(spend);

    expect(view.totalLabel).toBe('₹1,228.50');
    expect(view.ordersLabel).toBe('across 3 orders');
    expect(view.groupOrdersLabel).toBe('₹678.00 · 1 order');
    expect(view.restaurantOrdersLabel).toBe('₹550.50 · 2 orders');
    expect(view.isEmpty).toBe(false);
  });

  it('marks a zero-spend account empty so the panel can be hidden', () => {
    const view = adaptSpend({
      ...spend,
      total: '0.00',
      order_count: 0,
      group_orders: { total: '0.00', count: 0 },
      restaurant_orders: { total: '0.00', count: 0 },
    });

    expect(view.isEmpty).toBe(true);
    expect(view.totalLabel).toBe('₹0.00');
  });

  it('does not render NaN if the API sends something unparseable', () => {
    expect(adaptSpend({ ...spend, total: 'oops' }).totalLabel).toBe('₹0.00');
  });
});

describe('adaptProfile', () => {
  const profile = {
    wa_id: '919988776655',
    observations: 5,
    is_confident: true,
    min_observations: 3,
    typical_budget: '800.00',
    budget_ceiling: '1240.00',
    usual_headcount: 6,
    dietary_tendency: 'VEG',
    favourites: [
      { restaurant_name: 'MotiMahal', order_count: 3, last_ordered_at: '2026-08-03T20:30:00Z' },
    ],
    busiest_weekday: 'Monday',
    busiest_hour: 20,
    last_ordered_at: '2026-08-03T20:30:00Z',
  };

  it('turns learned values into readable traits', () => {
    const view = adaptProfile(profile);

    expect(view.headline).toBe('Learned from your last 5 orders');
    expect(view.isConfident).toBe(true);
    expect(view.traits).toEqual([
      { label: 'Usual budget', value: '₹800.00' },
      { label: 'Usually feeding', value: '6 people' },
      { label: 'Goes back to', value: 'MotiMahal · 3x' },
      { label: 'Usually orders', value: 'VEG' },
      { label: 'Orders most on', value: 'Monday, around 8pm' },
    ]);
  });

  it('counts down instead of implying a preference is already in use', () => {
    const view = adaptProfile({ ...profile, observations: 2, is_confident: false });

    expect(view.headline).toBe('1 more order until EasyOrder starts using this');
    expect(view.isConfident).toBe(false);
  });

  it('omits traits with nothing learned yet', () => {
    const view = adaptProfile({
      ...profile,
      usual_headcount: null,
      dietary_tendency: null,
      favourites: [],
      busiest_weekday: null,
    });

    expect(view.traits.map((t) => t.label)).toEqual(['Usual budget']);
  });

  it('marks a user with no history empty so the card can be hidden', () => {
    expect(adaptProfile({ ...profile, observations: 0 }).isEmpty).toBe(true);
  });
});
