import { calculateCartTotal, type CartItem, type DietaryTag, type Vertical } from './playgroundModel';

export type SessionRole = 'host' | 'guest';
export type SessionStatus = 'INITIALIZING' | 'ACTIVE' | 'DEGRADED' | 'CHECKOUT_READY' | 'ORDERED';

export interface ApiSessionWarning {
  code: string;
  message: string;
  vertical?: Vertical | null;
  item_id?: string | null;
}

export interface ApiSessionEvent {
  id?: number | null;
  session_id?: string | null;
  event_type:
    | 'whatsapp_inbound'
    | 'session_created'
    | 'links_sent'
    | 'handoff_delivered'
    | 'handoff_failed';
  message_text?: string | null;
  intent_label?: string | null;
  message_id?: string | null;
  sender_wa_id?: string | null;
  mode?: string | null;
  request_id?: string | null;
  created_at?: string | null;
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
  timeline: ApiSessionEvent[];
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
  warnings: ApiSessionWarning[];
  cart: CartItem[];
  checkoutEligible: boolean;
  total: number;
  timeline: ApiSessionEvent[];
}

export interface CheckoutPreviewGroup {
  groupId: string;
  vertical: Vertical;
  sourceLabel: string;
  itemCount: number;
  subtotal: number;
}

export interface BudgetStatusViewModel {
  percent: number;
  delta: number;
  isOverBudget: boolean;
  hasWarning: boolean;
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
    warnings: payload.warnings,
    cart,
    checkoutEligible: payload.checkout_eligible,
    total: calculateCartTotal(cart),
    timeline: payload.timeline ?? [],
  };
}

export function getBudgetStatus(session: SessionBootstrapViewModel): BudgetStatusViewModel {
  const percent = session.budgetLimit > 0
    ? Math.min(100, Math.round((session.total / session.budgetLimit) * 100))
    : 100;
  const delta = session.budgetLimit - session.total;
  return {
    percent,
    delta,
    isOverBudget: delta < 0,
    hasWarning: session.budgetWarning || delta < 0,
  };
}

export function getWarningTitle(warning: ApiSessionWarning): string {
  if (warning.code === 'BUDGET_EXCEEDED') {
    return 'Budget review';
  }
  if (warning.code === 'DIETARY_MISMATCH') {
    return 'Dietary review';
  }
  if (warning.code === 'VERTICAL_TIMEOUT') {
    return 'Degraded availability';
  }
  if (warning.code === 'SOURCE_ATTRIBUTION_MISSING') {
    return 'Source review';
  }
  return warning.code.replaceAll('_', ' ').toLowerCase();
}

export function getItemWarnings(
  item: CartItem,
  session: SessionBootstrapViewModel,
): ApiSessionWarning[] {
  const warningMap = new Map<string, ApiSessionWarning>();
  for (const warning of session.warnings) {
    if (warning.item_id === item.id) {
      warningMap.set(warning.code, warning);
    }
  }
  if (
    session.dietaryPreference === 'VEG'
    && item.vertical === 'food'
    && item.dietaryTag === 'NON-VEG'
  ) {
    warningMap.set('DIETARY_MISMATCH', {
      code: 'DIETARY_MISMATCH',
      message: `Non-veg item '${item.name}' appears in a vegetarian session.`,
      vertical: item.vertical,
      item_id: item.id,
    });
  }
  return Array.from(warningMap.values());
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
    restaurantId: item.restaurant_id ?? undefined,
    restaurantName: item.restaurant_name ?? undefined,
    brandName: item.brand_name ?? undefined,
    sourceLabel: item.source_label ?? undefined,
  };
}

export function buildCheckoutPreviewGroups(cart: CartItem[]): CheckoutPreviewGroup[] {
  const groups = new Map<string, CheckoutPreviewGroup>();
  for (const item of cart) {
    const sourceKey = item.vertical === 'food'
      ? (item.restaurantId ?? item.restaurantName ?? 'unknown-restaurant')
      : 'instamart';
    const groupId = `${item.vertical}:${sourceKey}`;
    const sourceLabel = item.vertical === 'food'
      ? (item.restaurantName ?? 'Unknown restaurant')
      : (item.sourceLabel ?? 'Instamart');
    const current = groups.get(groupId) ?? {
      groupId,
      vertical: item.vertical,
      sourceLabel,
      itemCount: 0,
      subtotal: 0,
    };
    current.itemCount += item.quantity;
    current.subtotal += item.quantity * item.unitPrice;
    groups.set(groupId, current);
  }
  return Array.from(groups.values()).sort((left, right) => {
    if (left.vertical !== right.vertical) {
      return left.vertical === 'food' ? -1 : 1;
    }
    return left.sourceLabel.localeCompare(right.sourceLabel);
  });
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
