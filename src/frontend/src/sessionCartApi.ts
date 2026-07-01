import {
  adaptSessionBootstrap,
  type ApiCartItem,
  type ApiSessionBootstrap,
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
