import { useEffect, useState } from 'react';

import { fetchSessionSnapshot, type RealtimeConnectionState } from './sessionCartApi';
import type { SessionBootstrapViewModel } from './sessionBootstrap';

export function useSupabaseCartRealtime({
  sessionId,
  token,
  onSnapshot,
}: {
  sessionId: string;
  token: string | null;
  onSnapshot: (session: SessionBootstrapViewModel) => void;
}) {
  const [connectionState, setConnectionState] = useState<RealtimeConnectionState>('connecting');

  useEffect(() => {
    if (!token) {
      setConnectionState('offline');
      return;
    }

    let cancelled = false;
    let failures = 0;

    async function refresh() {
      try {
        const snapshot = await fetchSessionSnapshot(sessionId, token as string);
        if (cancelled) {
          return;
        }
        failures = 0;
        setConnectionState('connected');
        onSnapshot(snapshot);
      } catch {
        if (cancelled) {
          return;
        }
        failures += 1;
        setConnectionState(failures > 1 ? 'offline' : 'reconnecting');
      }
    }

    setConnectionState('connecting');
    void refresh();
    const intervalId = window.setInterval(refresh, 2500);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [sessionId, token, onSnapshot]);

  return { connectionState };
}
