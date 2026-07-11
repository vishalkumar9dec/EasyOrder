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
