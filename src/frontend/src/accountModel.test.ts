import { describe, expect, it } from 'vitest';

import { adaptOrder, adaptOrders, isValidPhoneInput } from './accountModel';

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
