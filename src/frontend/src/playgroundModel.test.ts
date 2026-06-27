import { describe, expect, it } from 'vitest';

import {
  addManualItem,
  calculateCartTotal,
  getScenarioById,
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
