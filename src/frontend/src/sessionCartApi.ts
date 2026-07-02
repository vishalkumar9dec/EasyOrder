import {
  adaptSessionBootstrap,
  type ApiCartItem,
  type ApiSessionBootstrap,
  type CheckoutPreviewGroup,
  type SessionBootstrapViewModel,
} from './sessionBootstrap';
import type { DietaryTag, Vertical } from './playgroundModel';

export interface CartItemCreateInput {
  name: string;
  quantity: number;
  price: number;
  dietary_tag: DietaryTag;
  vertical: Vertical;
  restaurant_id?: string;
  restaurant_name?: string;
  brand_name?: string;
  source_label?: string;
}

export interface CartItemUpdateInput {
  quantity?: number;
  price?: number;
  dietary_tag?: DietaryTag;
}

export type RealtimeConnectionState = 'connecting' | 'connected' | 'reconnecting' | 'offline';

export interface ApiCheckoutIssue {
  code: string;
  message: string;
  vertical: Vertical;
  item_id?: string | null;
  source_label?: string | null;
  new_price?: string | number | null;
  substitutes: ApiCartItem[];
}

export interface ApiCheckoutValidationResponse {
  status: string;
  checkout_ready: boolean;
  groups: Array<{
    group_id: string;
    vertical: Vertical;
    source_id: string;
    source_label: string;
    item_count: number;
    subtotal: string | number;
    items: ApiCartItem[];
  }>;
  issues: ApiCheckoutIssue[];
}

export interface CheckoutValidationViewModel {
  status: string;
  checkoutReady: boolean;
  groups: CheckoutPreviewGroup[];
  issues: ApiCheckoutIssue[];
}

export interface ApiCheckoutStepResult {
  group_id: string;
  vertical: Vertical;
  source_label: string;
  status: string;
  checkout_url?: string | null;
  error_message?: string | null;
}

export interface ApiCheckoutConfirmResponse {
  status: string;
  checkout_complete: boolean;
  partial_success: boolean;
  steps: ApiCheckoutStepResult[];
}

export interface CheckoutStepViewModel {
  groupId: string;
  vertical: Vertical;
  sourceLabel: string;
  status: string;
  checkoutUrl?: string;
  errorMessage?: string;
}

export interface CheckoutConfirmViewModel {
  status: string;
  checkoutComplete: boolean;
  partialSuccess: boolean;
  steps: CheckoutStepViewModel[];
}

export function reconcileCartItems(
  current: ApiCartItem[],
  incoming: ApiCartItem[],
): ApiCartItem[] {
  const byId = new Map<number | string, ApiCartItem>();
  for (const item of current) {
    byId.set(item.id ?? item.item_id, item);
  }
  for (const item of incoming) {
    byId.set(item.id ?? item.item_id, item);
  }
  const incomingKeys = new Set(incoming.map((item) => item.id ?? item.item_id));
  return Array.from(byId.entries())
    .filter(([key]) => incomingKeys.has(key))
    .map(([, item]) => item)
    .sort((left, right) => (left.id ?? 0) - (right.id ?? 0));
}

export async function fetchSessionSnapshot(
  sessionId: string,
  token: string,
): Promise<SessionBootstrapViewModel> {
  const response = await fetch(sessionUrl(sessionId, token));
  if (!response.ok) {
    throw new Error(`Session refresh failed with ${response.status}`);
  }
  return adaptSessionBootstrap((await response.json()) as ApiSessionBootstrap);
}

export async function createCartItem(
  sessionId: string,
  token: string,
  input: CartItemCreateInput,
): Promise<SessionBootstrapViewModel> {
  return mutateSession(sessionId, token, {
    method: 'POST',
    path: 'cart-items',
    body: input,
  });
}

export async function updateCartItem(
  sessionId: string,
  token: string,
  cartItemId: number,
  input: CartItemUpdateInput,
): Promise<SessionBootstrapViewModel> {
  return mutateSession(sessionId, token, {
    method: 'PATCH',
    path: `cart-items/${cartItemId}`,
    body: input,
  });
}

export async function deleteCartItem(
  sessionId: string,
  token: string,
  cartItemId: number,
): Promise<SessionBootstrapViewModel> {
  return mutateSession(sessionId, token, {
    method: 'DELETE',
    path: `cart-items/${cartItemId}`,
  });
}

export async function validateCheckout(
  sessionId: string,
  token: string,
): Promise<CheckoutValidationViewModel> {
  const response = await fetch(`/api/session/${sessionId}/checkout?token=${encodeURIComponent(token)}`, {
    method: 'POST',
  });
  const payload = await response.json();
  if (response.status === 409) {
    return adaptCheckoutValidation(payload.detail as ApiCheckoutValidationResponse);
  }
  if (!response.ok) {
    throw new Error(`Checkout validation failed with ${response.status}`);
  }
  return adaptCheckoutValidation(payload as ApiCheckoutValidationResponse);
}

export async function confirmCheckout(
  sessionId: string,
  token: string,
  oauthCode = 'mock-oauth-code',
): Promise<CheckoutConfirmViewModel> {
  const response = await fetch(`/api/session/${sessionId}/checkout/confirm?token=${encodeURIComponent(token)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ oauth_code: oauthCode }),
  });
  if (!response.ok) {
    throw new Error(`Checkout confirmation failed with ${response.status}`);
  }
  return adaptCheckoutConfirm((await response.json()) as ApiCheckoutConfirmResponse);
}

export function adaptCheckoutValidation(
  payload: ApiCheckoutValidationResponse,
): CheckoutValidationViewModel {
  return {
    status: payload.status,
    checkoutReady: payload.checkout_ready,
    groups: payload.groups.map((group) => ({
      groupId: group.group_id,
      vertical: group.vertical,
      sourceLabel: group.source_label,
      itemCount: group.item_count,
      subtotal: Number(group.subtotal),
    })),
    issues: payload.issues,
  };
}

export function adaptCheckoutConfirm(
  payload: ApiCheckoutConfirmResponse,
): CheckoutConfirmViewModel {
  return {
    status: payload.status,
    checkoutComplete: payload.checkout_complete,
    partialSuccess: payload.partial_success,
    steps: payload.steps.map((step) => ({
      groupId: step.group_id,
      vertical: step.vertical,
      sourceLabel: step.source_label,
      status: step.status,
      checkoutUrl: step.checkout_url ?? undefined,
      errorMessage: step.error_message ?? undefined,
    })),
  };
}

async function mutateSession(
  sessionId: string,
  token: string,
  request: {
    method: 'POST' | 'PATCH' | 'DELETE';
    path: string;
    body?: unknown;
  },
): Promise<SessionBootstrapViewModel> {
  const response = await fetch(`/api/session/${sessionId}/${request.path}?token=${encodeURIComponent(token)}`, {
    method: request.method,
    headers: request.body ? { 'Content-Type': 'application/json' } : undefined,
    body: request.body ? JSON.stringify(request.body) : undefined,
  });
  if (!response.ok) {
    throw new Error(`Cart mutation failed with ${response.status}`);
  }
  return adaptSessionBootstrap((await response.json()) as ApiSessionBootstrap);
}

function sessionUrl(sessionId: string, token: string): string {
  return `/api/session/${sessionId}?token=${encodeURIComponent(token)}`;
}
