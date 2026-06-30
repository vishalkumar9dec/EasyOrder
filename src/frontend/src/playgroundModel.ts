export type Vertical = 'food' | 'instamart';
export type DietaryTag = 'VEG' | 'NON-VEG' | 'ANY';
export type Role = 'host' | 'guest';
export type CheckoutStatus = 'idle' | 'ready' | 'blocked' | 'partial';

export interface CartItem {
  id: string;
  name: string;
  vertical: Vertical;
  quantity: number;
  unitPrice: number;
  dietaryTag: DietaryTag;
  restaurantName?: string;
  brandName?: string;
  sourceLabel?: string;
  issue?: 'unavailable' | 'price-change';
  substitute?: string;
}

export interface CheckoutResult {
  status: CheckoutStatus;
  title: string;
  detail: string;
  foodCheckoutUrl?: string;
  instamartCheckoutUrl?: string;
}

export interface PlaygroundScenario {
  id: string;
  title: string;
  shortLabel: string;
  prompt: string;
  budgetLimit: number;
  headcount: number;
  dietaryPreference: DietaryTag;
  degradedVerticals: Vertical[];
  warnings: string[];
  cart: CartItem[];
  checkoutResult: CheckoutResult;
}

export const scenarios: PlaygroundScenario[] = [
  {
    id: 'normal-group-order',
    title: 'Normal group order',
    shortLabel: 'Normal',
    prompt: '@EasyOrder get biryani, paneer rolls and cold drinks for 6 under 3000',
    budgetLimit: 3000,
    headcount: 6,
    dietaryPreference: 'ANY',
    degradedVerticals: [],
    warnings: ['All mock services are healthy.'],
    cart: [
      {
        id: 'food-biryani',
        name: 'Chicken dum biryani family pack',
        vertical: 'food',
        quantity: 2,
        unitPrice: 620,
        dietaryTag: 'NON-VEG',
        restaurantName: 'Biryani House',
      },
      {
        id: 'food-paneer-roll',
        name: 'Paneer tikka rolls',
        vertical: 'food',
        quantity: 4,
        unitPrice: 180,
        dietaryTag: 'VEG',
        restaurantName: 'Roll House',
      },
      {
        id: 'im-cola',
        name: 'Cola 2L bottle',
        vertical: 'instamart',
        quantity: 2,
        unitPrice: 110,
        dietaryTag: 'VEG',
        brandName: 'Thums Up',
        sourceLabel: 'Instamart Mock Store',
      },
    ],
    checkoutResult: {
      status: 'ready',
      title: 'Ready for mock checkout',
      detail: 'Food and Instamart carts are available as separate mock checkout links.',
      foodCheckoutUrl: 'https://mock.swiggy.local/checkout/food',
      instamartCheckoutUrl: 'https://mock.swiggy.local/checkout/instamart',
    },
  },
  {
    id: 'over-budget-cart',
    title: 'Over-budget cart',
    shortLabel: 'Budget',
    prompt: '@EasyOrder get premium pizza, desserts and drinks for 8 under 1800',
    budgetLimit: 1800,
    headcount: 8,
    dietaryPreference: 'ANY',
    degradedVerticals: [],
    warnings: [],
    cart: [
      {
        id: 'food-pizza',
        name: 'Large farmhouse pizzas',
        vertical: 'food',
        quantity: 4,
        unitPrice: 560,
        dietaryTag: 'VEG',
        restaurantName: 'Pizza Yard',
      },
      {
        id: 'food-brownie',
        name: 'Chocolate brownie box',
        vertical: 'food',
        quantity: 2,
        unitPrice: 320,
        dietaryTag: 'VEG',
        restaurantName: 'Pizza Yard',
      },
      {
        id: 'im-juice',
        name: 'Mixed fruit juice pack',
        vertical: 'instamart',
        quantity: 3,
        unitPrice: 145,
        dietaryTag: 'VEG',
        brandName: 'Real',
        sourceLabel: 'Instamart Mock Store',
      },
    ],
    checkoutResult: {
      status: 'ready',
      title: 'Budget warning only',
      detail: 'The host can still validate checkout after trimming or approving the overage.',
      foodCheckoutUrl: 'https://mock.swiggy.local/checkout/food-budget',
      instamartCheckoutUrl: 'https://mock.swiggy.local/checkout/instamart-budget',
    },
  },
  {
    id: 'dietary-mismatch',
    title: 'Dietary mismatch',
    shortLabel: 'Dietary',
    prompt: '@EasyOrder get vegetarian snacks and drinks for 5 under 2200',
    budgetLimit: 2200,
    headcount: 5,
    dietaryPreference: 'VEG',
    degradedVerticals: [],
    warnings: [],
    cart: [
      {
        id: 'food-paneer',
        name: 'Paneer makhani bowl',
        vertical: 'food',
        quantity: 5,
        unitPrice: 210,
        dietaryTag: 'VEG',
        restaurantName: 'Paneer Palace',
      },
      {
        id: 'food-kebab',
        name: 'Chicken seekh kebab',
        vertical: 'food',
        quantity: 1,
        unitPrice: 340,
        dietaryTag: 'NON-VEG',
        restaurantName: 'Kebab Junction',
      },
      {
        id: 'im-lassi',
        name: 'Sweet lassi bottle',
        vertical: 'instamart',
        quantity: 5,
        unitPrice: 65,
        dietaryTag: 'VEG',
        brandName: 'Amul',
        sourceLabel: 'Instamart Mock Store',
      },
    ],
    checkoutResult: {
      status: 'blocked',
      title: 'Dietary review needed',
      detail: 'Replace the non-veg item before validating this vegetarian mock order.',
    },
  },
  {
    id: 'degraded-food',
    title: 'Degraded Food availability',
    shortLabel: 'Food down',
    prompt: '@EasyOrder get burgers and party supplies for 4 under 1600',
    budgetLimit: 1600,
    headcount: 4,
    dietaryPreference: 'ANY',
    degradedVerticals: ['food'],
    warnings: ['Food search timed out. Add food manually while Instamart stays available.'],
    cart: [
      {
        id: 'im-plates',
        name: 'Disposable plates pack',
        vertical: 'instamart',
        quantity: 1,
        unitPrice: 140,
        dietaryTag: 'ANY',
        brandName: 'PartyPro',
        sourceLabel: 'Instamart Mock Store',
      },
      {
        id: 'im-soda',
        name: 'Soda cans pack',
        vertical: 'instamart',
        quantity: 2,
        unitPrice: 240,
        dietaryTag: 'VEG',
        brandName: 'Bisleri Pop',
        sourceLabel: 'Instamart Mock Store',
      },
    ],
    checkoutResult: {
      status: 'partial',
      title: 'Partial mock checkout',
      detail: 'Instamart can proceed. Food needs manual additions after the degraded search.',
      instamartCheckoutUrl: 'https://mock.swiggy.local/checkout/instamart-only',
    },
  },
  {
    id: 'degraded-instamart',
    title: 'Degraded Instamart availability',
    shortLabel: 'IM down',
    prompt: '@EasyOrder get dosa, idli and paper plates for 6 under 2400',
    budgetLimit: 2400,
    headcount: 6,
    dietaryPreference: 'VEG',
    degradedVerticals: ['instamart'],
    warnings: ['Instamart search timed out. Food recommendations are still ready.'],
    cart: [
      {
        id: 'food-dosa',
        name: 'Masala dosa',
        vertical: 'food',
        quantity: 6,
        unitPrice: 140,
        dietaryTag: 'VEG',
        restaurantName: 'Dosa Corner',
      },
      {
        id: 'food-idli',
        name: 'Idli sambar combo',
        vertical: 'food',
        quantity: 3,
        unitPrice: 120,
        dietaryTag: 'VEG',
        restaurantName: 'Dosa Corner',
      },
    ],
    checkoutResult: {
      status: 'partial',
      title: 'Food checkout only',
      detail: 'Food checkout is ready. Instamart can be retried or added manually later.',
      foodCheckoutUrl: 'https://mock.swiggy.local/checkout/food-only',
    },
  },
  {
    id: 'stock-change',
    title: 'Stock change at validation',
    shortLabel: 'Stock',
    prompt: '@EasyOrder get noodles, momos and ice cream for 5 under 2000',
    budgetLimit: 2000,
    headcount: 5,
    dietaryPreference: 'ANY',
    degradedVerticals: [],
    warnings: [],
    cart: [
      {
        id: 'food-noodles',
        name: 'Hakka noodles tray',
        vertical: 'food',
        quantity: 2,
        unitPrice: 380,
        dietaryTag: 'VEG',
        restaurantName: 'Wok Street',
      },
      {
        id: 'food-momos',
        name: 'Chicken momos',
        vertical: 'food',
        quantity: 3,
        unitPrice: 160,
        dietaryTag: 'NON-VEG',
        restaurantName: 'Momo House',
      },
      {
        id: 'im-icecream',
        name: 'Vanilla ice cream tub',
        vertical: 'instamart',
        quantity: 2,
        unitPrice: 220,
        dietaryTag: 'VEG',
        brandName: 'Cream Bell',
        sourceLabel: 'Instamart Mock Store',
        issue: 'unavailable',
        substitute: 'Butterscotch ice cream tub',
      },
    ],
    checkoutResult: {
      status: 'blocked',
      title: 'Unavailable item',
      detail: 'Vanilla ice cream is out of stock. Suggested substitute: Butterscotch ice cream tub.',
    },
  },
  {
    id: 'price-change',
    title: 'Price change at validation',
    shortLabel: 'Price',
    prompt: '@EasyOrder get sushi platter and sparkling water for 4 under 2600',
    budgetLimit: 2600,
    headcount: 4,
    dietaryPreference: 'ANY',
    degradedVerticals: [],
    warnings: [],
    cart: [
      {
        id: 'food-sushi',
        name: 'Sushi party platter',
        vertical: 'food',
        quantity: 1,
        unitPrice: 1850,
        dietaryTag: 'NON-VEG',
        restaurantName: 'Sushi Station',
        issue: 'price-change',
      },
      {
        id: 'im-water',
        name: 'Sparkling water cans',
        vertical: 'instamart',
        quantity: 2,
        unitPrice: 180,
        dietaryTag: 'VEG',
        brandName: 'Kinley',
        sourceLabel: 'Instamart Mock Store',
      },
    ],
    checkoutResult: {
      status: 'blocked',
      title: 'Price changed',
      detail: 'Sushi party platter increased in price. Review the new total before checkout.',
    },
  },
];

export function cloneCart(cart: CartItem[]): CartItem[] {
  return cart.map((item) => ({ ...item }));
}

export function calculateCartTotal(cart: CartItem[]): number {
  return cart.reduce((total, item) => total + item.quantity * item.unitPrice, 0);
}

export function updateItemQuantity(cart: CartItem[], itemId: string, quantity: number): CartItem[] {
  const nextQuantity = Math.max(0, Math.min(99, Math.floor(quantity)));
  return cart
    .map((item) => (item.id === itemId ? { ...item, quantity: nextQuantity } : item))
    .filter((item) => item.quantity > 0);
}

export function addManualItem(cart: CartItem[], vertical: Vertical): CartItem[] {
  const manualCount = cart.filter((item) => item.id.startsWith('manual-')).length + 1;
  return [
    ...cart,
    {
      id: `manual-${vertical}-${manualCount}`,
      name: vertical === 'food' ? 'Manual food item' : 'Manual Instamart item',
      vertical,
      quantity: 1,
      unitPrice: vertical === 'food' ? 220 : 120,
      dietaryTag: 'ANY',
      restaurantName: vertical === 'food' ? 'Manual restaurant' : undefined,
      brandName: vertical === 'instamart' ? 'Manual brand' : undefined,
      sourceLabel: vertical === 'instamart' ? 'Manual Instamart source' : undefined,
    },
  ];
}

export function getScenarioById(id: string): PlaygroundScenario {
  return scenarios.find((scenario) => scenario.id === id) ?? scenarios[0];
}

export function hasDietaryMismatch(dietaryPreference: DietaryTag, cart: CartItem[]): boolean {
  return dietaryPreference === 'VEG' && cart.some((item) => item.dietaryTag === 'NON-VEG');
}

export function getCartIssueItems(cart: CartItem[], issue: NonNullable<CartItem['issue']>): CartItem[] {
  return cart.filter((item) => item.issue === issue);
}

export function getWarnings(
  scenario: PlaygroundScenario,
  cart: CartItem[],
  dietaryPreference: DietaryTag = scenario.dietaryPreference,
): string[] {
  const total = calculateCartTotal(cart);
  const warnings = new Set(scenario.warnings);

  if (total > scenario.budgetLimit) {
    warnings.add(`Cart is ${formatCurrency(total - scenario.budgetLimit)} over budget.`);
  }

  if (hasDietaryMismatch(dietaryPreference, cart)) {
    warnings.add('Vegetarian preference has non-veg items in the cart.');
  }

  if (getCartIssueItems(cart, 'unavailable').length > 0) {
    warnings.add('A checkout validation item is unavailable and has a substitute.');
  }

  if (getCartIssueItems(cart, 'price-change').length > 0) {
    warnings.add('A checkout validation item changed price before payment.');
  }

  for (const vertical of scenario.degradedVerticals) {
    warnings.add(`${formatVertical(vertical)} is degraded in this mock scenario.`);
  }

  return Array.from(warnings);
}

export function getCheckoutResult(
  scenario: PlaygroundScenario,
  cart: CartItem[],
  dietaryPreference: DietaryTag = scenario.dietaryPreference,
): CheckoutResult {
  if (scenario.id === 'dietary-mismatch' && !hasDietaryMismatch(dietaryPreference, cart)) {
    return {
      status: 'ready',
      title: 'Ready for mock checkout',
      detail: 'Dietary preference is compatible with the current cart.',
      foodCheckoutUrl: 'https://mock.swiggy.local/checkout/food-dietary',
      instamartCheckoutUrl: 'https://mock.swiggy.local/checkout/instamart-dietary',
    };
  }

  const unavailableItems = getCartIssueItems(cart, 'unavailable');
  if (scenario.id === 'stock-change') {
    if (unavailableItems.length === 0) {
      return {
        status: 'ready',
        title: 'Ready for mock checkout',
        detail: 'Unavailable items were removed from the current cart.',
        foodCheckoutUrl: 'https://mock.swiggy.local/checkout/food-stock',
        instamartCheckoutUrl: 'https://mock.swiggy.local/checkout/instamart-stock',
      };
    }

    const [item] = unavailableItems;
    return {
      status: 'blocked',
      title: 'Unavailable item',
      detail: `${item.name} is out of stock.${
        item.substitute ? ` Suggested substitute: ${item.substitute}.` : ''
      }`,
    };
  }

  const priceChangedItems = getCartIssueItems(cart, 'price-change');
  if (scenario.id === 'price-change') {
    if (priceChangedItems.length === 0) {
      return {
        status: 'ready',
        title: 'Ready for mock checkout',
        detail: 'Price-change items were removed from the current cart.',
        foodCheckoutUrl: 'https://mock.swiggy.local/checkout/food-price',
        instamartCheckoutUrl: 'https://mock.swiggy.local/checkout/instamart-price',
      };
    }

    const [item] = priceChangedItems;
    return {
      status: 'blocked',
      title: 'Price changed',
      detail: `${item.name} changed price before payment. Review the new total before checkout.`,
    };
  }

  return scenario.checkoutResult;
}

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatVertical(vertical: Vertical): string {
  return vertical === 'food' ? 'Food' : 'Instamart';
}

export function getCartItemSourceText(item: CartItem): string {
  if (item.vertical === 'food') {
    return item.restaurantName ?? 'Restaurant pending';
  }
  if (item.brandName && item.sourceLabel) {
    return `${item.brandName} · ${item.sourceLabel}`;
  }
  return item.sourceLabel ?? item.brandName ?? 'Instamart source pending';
}
