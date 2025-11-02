import { v4 as uuidv4 } from 'uuid';

// Light wrapper around rrweb for the POC, not a full SDK
export function initRRHog(opts: {
  writeKey: string;
  ingestUrl: string;            // e.g. http://localhost:8000/i
  user?: { id?: string; email?: string } | null;
  batchSize?: number;           // default 50
  flushIntervalMs?: number;     // default 5000
}) {
  const { writeKey, ingestUrl, user, batchSize = 50, flushIntervalMs = 5000 } = opts;

  const storageKey = 'rrhog:session_id';
  let sessionId = (typeof window !== 'undefined' && (window.localStorage.getItem(storageKey) || '')) || '';
  if (!sessionId) {
    sessionId = uuidv4();
    try { window.localStorage.setItem(storageKey, sessionId); } catch {}
  }

  let seq = 0;
  let buffer: any[] = [];
  let timer: any = null;

  async function flush(reason = 'timer') {
    if (buffer.length === 0) return;
    const payload = {
      seq: seq++,
      session_id: sessionId,
      url: window.location.href,
      user: user ? { ...user, anonymous: !user?.id && !user?.email } : { anonymous: true },
      events: buffer
    };
    buffer = [];
    try {
      const body = JSON.stringify(payload);
      if (navigator.sendBeacon) {
        const blob = new Blob([body], { type: 'application/json' });
        navigator.sendBeacon(ingestUrl, blob); // headers not supported; key goes in auth
      } else {
        await fetch(ingestUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${writeKey}`
          },
          body
        });
      }
    } catch (e) {
      console.warn('rrHog flush failed', e);
    }
  }

  function schedule() {
    clearTimeout(timer);
    timer = setTimeout(() => flush('timer'), flushIntervalMs);
  }

  async function start() {
    const { record } = await import('rrweb');
    record({
      emit(event) {
        buffer.push(event);
        if (buffer.length >= batchSize) flush('batch');
        else schedule();
      },
    });

    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden') flush('visibilitychange');
    });
    window.addEventListener('beforeunload', () => flush('beforeunload'));
  }

  start();

  return {
    stop: () => {
      clearTimeout(timer);
    }
  };
}
