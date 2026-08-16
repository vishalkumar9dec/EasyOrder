// Account API client and view-model adapters (task 11.2, ADR 0006).
// The PWA renders the same records the WhatsApp chat answers with; all
// requests ride the session cookie set by /api/auth/otp/verify.

export interface ApiOrder {
  session_id: string;
  created_at: string;
  status: string;
  item_count: number;
  total: string;
  review_url: string;
}

export interface OrderView {
  sessionId: string;
  startedLabel: string;
  statusLabel: string;
  statusClass: string;
  itemsLabel: string;
  totalLabel: string;
  reviewUrl: string;
}

const STATUS_LABELS: Record<string, string> = {
  INITIALIZING: 'Setting up',
  ACTIVE: 'Being planned',
  DEGRADED: 'Planned (partial sources)',
  CHECKOUT_READY: 'Ready for checkout',
  ORDERED: 'Placed',
};

export function adaptOrder(order: ApiOrder): OrderView {
  const started = new Date(order.created_at);
  const startedLabel = Number.isNaN(started.getTime())
    ? ''
    : started.toLocaleString([], {
        day: '2-digit',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit',
      });
  return {
    sessionId: order.session_id,
    startedLabel,
    statusLabel: STATUS_LABELS[order.status] ?? order.status,
    statusClass: `order-status--${order.status.toLowerCase()}`,
    itemsLabel: `${order.item_count} item${order.item_count === 1 ? '' : 's'}`,
    totalLabel: `₹${Number(order.total).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`,
    reviewUrl: order.review_url,
  };
}

export function adaptOrders(orders: ApiOrder[]): OrderView[] {
  return orders.map(adaptOrder);
}

export interface ApiLiveOrderItem {
  name: string;
  quantity: number;
}

export interface ApiLiveOrder {
  order_id: string;
  restaurant_name: string;
  items: ApiLiveOrderItem[];
  total: string;
  status: string;
  delivery_deadline: string | null;
  target_placement_at: string | null;
  created_at: string;
}

export interface ApiLiveOrders {
  wa_id: string;
  scheduled: ApiLiveOrder[];
  ongoing: ApiLiveOrder[];
  historical: ApiLiveOrder[];
}

export interface LiveOrderView {
  orderId: string;
  restaurantName: string;
  itemsLabel: string;
  totalLabel: string;
  statusLabel: string;
  statusClass: string;
  timingLabel: string | null;
}

const LIVE_ORDER_STATUS_LABELS: Record<string, string> = {
  PENDING_CONFIRMATION: 'Awaiting your confirmation',
  SCHEDULED: 'Scheduled',
  PLACED: 'Placed',
  DELIVERED: 'Delivered',
  CANCELLED: 'Cancelled',
  FAILED: 'Failed',
};

function formatDateTime(value: string | null): string | null {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleString([], {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function adaptLiveOrder(order: ApiLiveOrder): LiveOrderView {
  const timingSource = order.target_placement_at ?? order.delivery_deadline;
  const timingLabel = formatDateTime(timingSource);
  return {
    orderId: order.order_id,
    restaurantName: order.restaurant_name,
    itemsLabel: order.items.map((item) => `${item.name} x${item.quantity}`).join(', '),
    totalLabel: `₹${Number(order.total).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`,
    statusLabel: LIVE_ORDER_STATUS_LABELS[order.status] ?? order.status,
    statusClass: `order-status--${order.status.toLowerCase()}`,
    timingLabel: timingLabel ? `Target: ${timingLabel}` : null,
  };
}

export function adaptLiveOrders(orders: ApiLiveOrder[]): LiveOrderView[] {
  return orders.map(adaptLiveOrder);
}

export async function fetchLiveOrders(): Promise<ApiLiveOrders> {
  const response = await fetch('/api/me/orders/live');
  if (!response.ok) throw new Error(await readError(response));
  return (await response.json()) as ApiLiveOrders;
}

export interface ApiSpendBucket {
  total: string;
  count: number;
}

export interface ApiSpend {
  wa_id: string;
  currency: string;
  total: string;
  order_count: number;
  group_orders: ApiSpendBucket;
  restaurant_orders: ApiSpendBucket;
}

export interface SpendView {
  totalLabel: string;
  ordersLabel: string;
  groupOrdersLabel: string;
  restaurantOrdersLabel: string;
  isEmpty: boolean;
}

function orderCountLabel(count: number): string {
  return `${count} order${count === 1 ? '' : 's'}`;
}

export function formatAmount(value: string): string {
  const amount = Number(value);
  if (!Number.isFinite(amount)) return '₹0.00';
  return `₹${amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
}

export function adaptSpend(spend: ApiSpend): SpendView {
  return {
    totalLabel: formatAmount(spend.total),
    ordersLabel: `across ${orderCountLabel(spend.order_count)}`,
    groupOrdersLabel: `${formatAmount(spend.group_orders.total)} · ${orderCountLabel(
      spend.group_orders.count,
    )}`,
    restaurantOrdersLabel: `${formatAmount(spend.restaurant_orders.total)} · ${orderCountLabel(
      spend.restaurant_orders.count,
    )}`,
    isEmpty: spend.order_count === 0,
  };
}

export async function fetchSpend(): Promise<ApiSpend> {
  const response = await fetch('/api/me/spend');
  if (!response.ok) throw new Error(await readError(response));
  return (await response.json()) as ApiSpend;
}

export interface ApiFavourite {
  restaurant_name: string;
  order_count: number;
  last_ordered_at: string;
}

export interface ApiProfile {
  wa_id: string;
  observations: number;
  is_confident: boolean;
  min_observations: number;
  typical_budget: string | null;
  budget_ceiling: string | null;
  usual_headcount: number | null;
  dietary_tendency: string | null;
  favourites: ApiFavourite[];
  busiest_weekday: string | null;
  busiest_hour: number | null;
  last_ordered_at: string | null;
}

export interface ProfileTrait {
  label: string;
  value: string;
}

export interface ProfileView {
  headline: string;
  traits: ProfileTrait[];
  isConfident: boolean;
  isEmpty: boolean;
}

function hourLabel(hour: number): string {
  const suffix = hour < 12 ? 'am' : 'pm';
  const twelve = hour % 12 === 0 ? 12 : hour % 12;
  return `${twelve}${suffix}`;
}

export function adaptProfile(profile: ApiProfile): ProfileView {
  const traits: ProfileTrait[] = [];
  if (profile.typical_budget) {
    traits.push({ label: 'Usual budget', value: formatAmount(profile.typical_budget) });
  }
  if (profile.usual_headcount) {
    traits.push({ label: 'Usually feeding', value: `${profile.usual_headcount} people` });
  }
  if (profile.favourites.length > 0) {
    const top = profile.favourites[0];
    traits.push({
      label: 'Goes back to',
      value: `${top.restaurant_name} · ${top.order_count}x`,
    });
  }
  if (profile.dietary_tendency && profile.dietary_tendency !== 'ANY') {
    traits.push({ label: 'Usually orders', value: profile.dietary_tendency });
  }
  if (profile.busiest_weekday) {
    const hour = profile.busiest_hour === null ? '' : `, around ${hourLabel(profile.busiest_hour)}`;
    traits.push({ label: 'Orders most on', value: `${profile.busiest_weekday}${hour}` });
  }

  // Below the threshold the profile is shown but explicitly not in use, so the
  // page never implies a default was applied when it wasn't.
  const remaining = profile.min_observations - profile.observations;
  return {
    headline: profile.is_confident
      ? `Learned from your last ${profile.observations} orders`
      : `${remaining} more order${remaining === 1 ? '' : 's'} until EasyOrder starts using this`,
    traits,
    isConfident: profile.is_confident,
    isEmpty: profile.observations === 0,
  };
}

export async function fetchProfile(): Promise<ApiProfile> {
  const response = await fetch('/api/me/profile');
  if (!response.ok) throw new Error(await readError(response));
  return (await response.json()) as ApiProfile;
}

export function isValidPhoneInput(phone: string): boolean {
  return /^\+?[\d\s-]{8,18}$/.test(phone.trim());
}

async function readError(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (typeof body.detail === 'string') return body.detail;
  } catch {
    // fall through to generic message
  }
  return `Request failed (${response.status})`;
}

export async function requestOtp(phone: string): Promise<void> {
  const response = await fetch('/api/auth/otp/request', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone }),
  });
  if (!response.ok) throw new Error(await readError(response));
}

export async function verifyOtp(phone: string, code: string): Promise<string> {
  const response = await fetch('/api/auth/otp/verify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone, code }),
  });
  if (!response.ok) throw new Error(await readError(response));
  const body = await response.json();
  return body.wa_id as string;
}

export async function fetchMe(): Promise<string | null> {
  const response = await fetch('/api/me');
  if (response.status === 401) return null;
  if (!response.ok) throw new Error(await readError(response));
  const body = await response.json();
  return body.wa_id as string;
}

export async function fetchOrders(): Promise<ApiOrder[]> {
  const response = await fetch('/api/me/orders');
  if (!response.ok) throw new Error(await readError(response));
  const body = await response.json();
  return body.orders as ApiOrder[];
}

export async function logout(): Promise<void> {
  await fetch('/api/auth/logout', { method: 'POST' });
}
