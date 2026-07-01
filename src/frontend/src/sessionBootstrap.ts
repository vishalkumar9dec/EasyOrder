import { calculateCartTotal, type CartItem, type DietaryTag, type Vertical } from './playgroundModel';

export type SessionRole = 'host' | 'guest';
export type SessionStatus = 'INITIALIZING' | 'ACTIVE' | 'DEGRADED' | 'CHECKOUT_READY' | 'ORDERED';

export interface ApiSessionWarning {
  code: string;
  message: string;
  vertical?: Vertical | null;
  item_id?: string | null;
}

export interface ApiCartItem {
  id: number | null;
  item_id: string;
  name: string;
  quantity: number;
  price: string | number;
  added_by: string;
  dietary_tag: DietaryTag;
  vertical: Vertical;
  restaurant_id?: string | null;
  restaurant_name?: string | null;
  brand_name?: string | null;
  source_label?: string | null;
}

export interface ApiSessionBootstrap {
  session_id: string;
  role: SessionRole;
  status: SessionStatus;
  budget_limit: string | number;
  head_count: number;
  dietary_preference: DietaryTag;
  budget_warning: boolean;
  degraded_verticals: Vertical[];
  warnings: ApiSessionWarning[];
  cart_items: ApiCartItem[];
  checkout_eligible: boolean;
}

export interface SessionBootstrapViewModel {
  sessionId: string;
  role: SessionRole;
  status: SessionStatus;
  budgetLimit: number;
  headcount: number;
  dietaryPreference: DietaryTag;
  budgetWarning: boolean;
  degradedVerticals: Vertical[];
  warnings: string[];
  cart: CartItem[];
  checkoutEligible: boolean;
  total: number;
}

export function adaptSessionBootstrap(payload: ApiSessionBootstrap): SessionBootstrapViewModel {
  const cart = payload.cart_items.map(adaptCartItem);
  return {
    sessionId: payload.session_id,
    role: payload.role,
    status: payload.status,
    budgetLimit: Number(payload.budget_limit),
    headcount: payload.head_count,
    dietaryPreference: payload.dietary_preference,
    budgetWarning: payload.budget_warning,
    degradedVerticals: payload.degraded_verticals,
    warnings: payload.warnings.map((warning) => warning.message),
    cart,
    checkoutEligible: payload.checkout_eligible,
    total: calculateCartTotal(cart),
  };
}

export function adaptCartItem(item: ApiCartItem): CartItem {
  return {
    id: item.item_id || `cart-${item.id ?? item.name}`,
    apiId: item.id ?? undefined,
    name: item.name,
    vertical: item.vertical,
    quantity: item.quantity,
    unitPrice: Number(item.price),
    dietaryTag: item.dietary_tag,
    restaurantName: item.restaurant_name ?? undefined,
    brandName: item.brand_name ?? undefined,
    sourceLabel: item.source_label ?? undefined,
  };
}

export function getSessionHealthLabel(status: SessionStatus): string {
  if (status === 'DEGRADED') {
    return 'Degraded';
  }
  if (status === 'ACTIVE' || status === 'CHECKOUT_READY') {
    return 'Healthy';
  }
  return status.replace('_', ' ');
}

export function getRoleLabel(role: SessionRole): string {
  return role === 'host' ? 'Host' : 'Guest';
}
