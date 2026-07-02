import { describe, expect, it } from 'vitest';

import { getSessionRoute } from './App';
import {
  adaptSessionBootstrap,
  buildCheckoutPreviewGroups,
  getBudgetStatus,
  getItemWarnings,
  getRoleLabel,
  getSessionHealthLabel,
  getWarningTitle,
  type ApiSessionBootstrap,
} from './sessionBootstrap';
import { adaptCheckoutConfirm, adaptCheckoutValidation, reconcileCartItems } from './sessionCartApi';

const payload: ApiSessionBootstrap = {
  session_id: 'session_123',
  role: 'host',
  status: 'DEGRADED',
  budget_limit: '3000.00',
  head_count: 4,
  dietary_preference: 'ANY',
  budget_warning: false,
  degraded_verticals: ['instamart'],
  warnings: [{ code: 'VERTICAL_TIMEOUT', message: 'Instamart search timed out.' }],
  checkout_eligible: true,
  cart_items: [
    {
      id: 1,
      item_id: 'food-biryani',
      name: 'Chicken dum biryani family pack',
      quantity: 4,
      price: '620.00',
      added_by: '919988776655',
      dietary_tag: 'NON-VEG',
      vertical: 'food',
      restaurant_id: 'rest-biryani-house',
      restaurant_name: 'Biryani House',
    },
    {
      id: 2,
      item_id: 'im-cola',
      name: 'Cola 2L bottle',
      quantity: 2,
      price: '110.00',
      added_by: '919988776655',
      dietary_tag: 'VEG',
      vertical: 'instamart',
      brand_name: 'Thums Up',
      source_label: 'Instamart Mock Store',
    },
  ],
};

describe('session bootstrap route and adapter', () => {
  it('detects session routes and token query params', () => {
    expect(getSessionRoute('/session/session_123', '?token=guest_token')).toEqual({
      sessionId: 'session_123',
      token: 'guest_token',
    });
    expect(getSessionRoute('/', '')).toBeNull();
  });

  it('adapts API state into the cart view model without token material', () => {
    const viewModel = adaptSessionBootstrap(payload);

    expect(viewModel.sessionId).toBe('session_123');
    expect(viewModel.role).toBe('host');
    expect(viewModel.total).toBe(2700);
    expect(viewModel.cart[0]).toMatchObject({
      id: 'food-biryani',
      apiId: 1,
      restaurantId: 'rest-biryani-house',
      restaurantName: 'Biryani House',
      dietaryTag: 'NON-VEG',
    });
    expect(viewModel.cart[1]).toMatchObject({
      id: 'im-cola',
      brandName: 'Thums Up',
      sourceLabel: 'Instamart Mock Store',
    });
    expect(JSON.stringify(viewModel)).not.toContain('host_token');
    expect(JSON.stringify(viewModel)).not.toContain('guest_token');
  });

  it('labels host/guest and degraded session states', () => {
    expect(getRoleLabel('guest')).toBe('Guest');
    expect(getRoleLabel('host')).toBe('Host');
    expect(getSessionHealthLabel('DEGRADED')).toBe('Degraded');
    expect(getSessionHealthLabel('ACTIVE')).toBe('Healthy');
    expect(getWarningTitle({ code: 'DIETARY_MISMATCH', message: 'x' })).toBe('Dietary review');
  });

  it('reconciles realtime cart snapshots without duplicates', () => {
    const current = payload.cart_items;
    const incoming = [
      { ...payload.cart_items[0], quantity: 3 },
      {
        id: 3,
        item_id: 'im-napkins',
        name: 'Paper napkins',
        quantity: 2,
        price: '45.00',
        added_by: 'guest',
        dietary_tag: 'ANY',
        vertical: 'instamart',
        source_label: 'Instamart Mock Store',
      },
    ] satisfies ApiSessionBootstrap['cart_items'];

    const reconciled = reconcileCartItems(current, incoming);

    expect(reconciled).toHaveLength(2);
    expect(reconciled[0]).toMatchObject({ id: 1, quantity: 3 });
    expect(reconciled[1]).toMatchObject({ id: 3, item_id: 'im-napkins' });
    expect(reconciled.some((item) => item.id === 2)).toBe(false);
  });

  it('derives budget and item-level warning state for session UI', () => {
    const warningPayload: ApiSessionBootstrap = {
      ...payload,
      budget_limit: '2000.00',
      dietary_preference: 'VEG',
      budget_warning: true,
      warnings: [
        { code: 'BUDGET_EXCEEDED', message: 'Cart total exceeds budget by INR 700.00.' },
        {
          code: 'DIETARY_MISMATCH',
          message: "Non-veg item 'Chicken dum biryani family pack' appears in a vegetarian session.",
          vertical: 'food',
          item_id: 'food-biryani',
        },
      ],
    };

    const viewModel = adaptSessionBootstrap(warningPayload);
    const budget = getBudgetStatus(viewModel);
    const itemWarnings = getItemWarnings(viewModel.cart[0], viewModel);

    expect(budget).toMatchObject({
      percent: 100,
      delta: -700,
      isOverBudget: true,
      hasWarning: true,
    });
    expect(itemWarnings).toHaveLength(1);
    expect(itemWarnings[0].code).toBe('DIETARY_MISMATCH');
  });

  it('builds host checkout preview groups by restaurant and Instamart source', () => {
    const viewModel = adaptSessionBootstrap({
      ...payload,
      cart_items: [
        ...payload.cart_items,
        {
          id: 3,
          item_id: 'food-paneer-roll',
          name: 'Paneer tikka rolls',
          quantity: 2,
          price: '180.00',
          added_by: 'guest',
          dietary_tag: 'VEG',
          vertical: 'food',
          restaurant_id: 'rest-roll-house',
          restaurant_name: 'Roll House',
        },
      ],
    });

    const groups = buildCheckoutPreviewGroups(viewModel.cart);

    expect(groups).toEqual([
      {
        groupId: 'food:rest-biryani-house',
        vertical: 'food',
        sourceLabel: 'Biryani House',
        itemCount: 4,
        subtotal: 2480,
      },
      {
        groupId: 'food:rest-roll-house',
        vertical: 'food',
        sourceLabel: 'Roll House',
        itemCount: 2,
        subtotal: 360,
      },
      {
        groupId: 'instamart:instamart',
        vertical: 'instamart',
        sourceLabel: 'Instamart Mock Store',
        itemCount: 2,
        subtotal: 220,
      },
    ]);
  });

  it('adapts checkout validation responses for the host panel', () => {
    const validation = adaptCheckoutValidation({
      status: 'checkout_ready',
      checkout_ready: true,
      groups: [
        {
          group_id: 'food:rest-biryani-house',
          vertical: 'food',
          source_id: 'rest-biryani-house',
          source_label: 'Biryani House',
          item_count: 4,
          subtotal: '2480.00',
          items: [payload.cart_items[0]],
        },
      ],
      issues: [],
    });

    expect(validation.checkoutReady).toBe(true);
    expect(validation.groups[0]).toMatchObject({
      groupId: 'food:rest-biryani-house',
      sourceLabel: 'Biryani House',
      subtotal: 2480,
    });
  });

  it('adapts checkout confirmation responses with created and failed steps', () => {
    const confirmation = adaptCheckoutConfirm({
      status: 'partial',
      checkout_complete: false,
      partial_success: true,
      steps: [
        {
          group_id: 'food:rest-biryani-house',
          vertical: 'food',
          source_label: 'Biryani House',
          status: 'created',
          checkout_url: 'https://mock.swiggy.local/checkout/food/rest-biryani-house/normal',
        },
        {
          group_id: 'instamart:instamart',
          vertical: 'instamart',
          source_label: 'Instamart Mock Store',
          status: 'failed',
          error_message: 'MockSwiggyCartCreationError: checkout cart creation failed',
        },
      ],
    });

    expect(confirmation).toMatchObject({
      status: 'partial',
      checkoutComplete: false,
      partialSuccess: true,
    });
    expect(confirmation.steps[0].checkoutUrl).toContain('rest-biryani-house');
    expect(confirmation.steps[1].errorMessage).toContain('cart creation failed');
  });
});
