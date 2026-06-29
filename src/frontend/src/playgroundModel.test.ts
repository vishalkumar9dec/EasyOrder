import { describe, expect, it } from 'vitest';

import {
  addManualItem,
  calculateCartTotal,
  getScenarioById,
  getCheckoutResult,
  getWarnings,
  scenarios,
  updateItemQuantity,
} from './playgroundModel';

describe('playground scenarios', () => {
  it('covers every issue #2 mock use case', () => {
    expect(scenarios.map((scenario) => scenario.id)).toEqual([
      'normal-group-order',
      'over-budget-cart',
      'dietary-mismatch',
      'degraded-food',
      'degraded-instamart',
      'stock-change',
      'price-change',
    ]);
  });

  it('keeps scenario prompts deterministic and local', () => {
    for (const scenario of scenarios) {
      expect(scenario.prompt).toContain('@EasyOrder');
      expect(scenario.cart.length).toBeGreaterThan(0);
    }
  });

  it('calculates cart totals from editable quantities', () => {
    const scenario = getScenarioById('normal-group-order');

    expect(calculateCartTotal(scenario.cart)).toBe(2180);
  });

  it('adds budget and dietary warnings from current cart state', () => {
    const scenario = getScenarioById('dietary-mismatch');
    const warnings = getWarnings(scenario, scenario.cart);

    expect(warnings).toContain('Vegetarian preference has non-veg items in the cart.');
  });

  it('updates dietary warnings when food preference changes', () => {
    const scenario = getScenarioById('dietary-mismatch');

    expect(getWarnings(scenario, scenario.cart, 'VEG')).toContain(
      'Vegetarian preference has non-veg items in the cart.',
    );
    expect(getWarnings(scenario, scenario.cart, 'NON-VEG')).not.toContain(
      'Vegetarian preference has non-veg items in the cart.',
    );
  });

  it('unblocks dietary checkout when selected preference allows the cart', () => {
    const scenario = getScenarioById('dietary-mismatch');

    expect(getCheckoutResult(scenario, scenario.cart, 'VEG').status).toBe('blocked');
    expect(getCheckoutResult(scenario, scenario.cart, 'NON-VEG')).toMatchObject({
      status: 'ready',
      title: 'Ready for mock checkout',
    });
  });

  it('removes budget warnings when edited cart returns under budget', () => {
    const scenario = getScenarioById('over-budget-cart');
    const reducedCart = updateItemQuantity(scenario.cart, 'food-pizza', 1);
    const warnings = getWarnings(scenario, reducedCart);

    expect(warnings.some((warning) => warning.includes('over budget'))).toBe(false);
  });

  it('removes unavailable-item warnings and unblocks checkout after the item is removed', () => {
    const scenario = getScenarioById('stock-change');
    const updatedCart = updateItemQuantity(scenario.cart, 'im-icecream', 0);

    expect(getWarnings(scenario, scenario.cart)).toContain(
      'A checkout validation item is unavailable and has a substitute.',
    );
    expect(getWarnings(scenario, updatedCart)).not.toContain(
      'A checkout validation item is unavailable and has a substitute.',
    );
    expect(getCheckoutResult(scenario, scenario.cart).status).toBe('blocked');
    expect(getCheckoutResult(scenario, updatedCart)).toMatchObject({
      status: 'ready',
      title: 'Ready for mock checkout',
    });
  });

  it('removes price-change warnings and unblocks checkout after the item is removed', () => {
    const scenario = getScenarioById('price-change');
    const updatedCart = updateItemQuantity(scenario.cart, 'food-sushi', 0);

    expect(getWarnings(scenario, scenario.cart)).toContain(
      'A checkout validation item changed price before payment.',
    );
    expect(getWarnings(scenario, updatedCart)).not.toContain(
      'A checkout validation item changed price before payment.',
    );
    expect(getCheckoutResult(scenario, scenario.cart).status).toBe('blocked');
    expect(getCheckoutResult(scenario, updatedCart)).toMatchObject({
      status: 'ready',
      title: 'Ready for mock checkout',
    });
  });

  it('updates quantities and removes zero-quantity items', () => {
    const scenario = getScenarioById('normal-group-order');
    const updatedCart = updateItemQuantity(scenario.cart, 'food-biryani', 0);

    expect(updatedCart.some((item) => item.id === 'food-biryani')).toBe(false);
  });

  it('adds manual items for degraded vertical review', () => {
    const scenario = getScenarioById('degraded-food');
    const updatedCart = addManualItem(scenario.cart, 'food');

    expect(updatedCart.at(-1)).toMatchObject({
      name: 'Manual food item',
      vertical: 'food',
    });
  });
});
