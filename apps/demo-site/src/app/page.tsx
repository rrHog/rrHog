"use client";

import Image from "next/image";
import { useEffect, useRef, useState } from "react";

/** ---- Config via env ---- */
const INGEST =
  process.env.NEXT_PUBLIC_RRHOG_INGEST ?? "http://localhost:8000/i";
const WRITE_KEY =
  process.env.NEXT_PUBLIC_RRHOG_WRITE_KEY ?? "dev_write_123";

/** ---- Small in-file rrHog helper (no SDK needed for POC) ---- */
type IdentityMode = "anon" | "user";

function getSessionId(): string {
  try {
    const k = "rrhog:session_id";
    let v = localStorage.getItem(k);
    if (!v) {
      v = (crypto as any).randomUUID?.() ?? Math.random().toString(36).slice(2);
      localStorage.setItem(k, v);
    }
    return v;
  } catch {
    return Math.random().toString(36).slice(2);
  }
}

export default function Home() {
  // Toggle identity to simulate logged-in vs anonymous users
  const [mode, setMode] = useState<IdentityMode>("anon");
  const modeRef = useRef<IdentityMode>("anon");
  const started = useRef(false);

  useEffect(() => {
    modeRef.current = mode;
  }, [mode]);

  useEffect(() => {
    if (started.current) return;
    started.current = true;

    (async () => {
      const { record } = await import("rrweb");

      const sessionId = getSessionId();
      let seq = 0;
      let buffer: any[] = [];
      let timer: any = null;

      const batchSize = 50;
      const flushIntervalMs = 5000;

      const user = () =>
        modeRef.current === "user"
          ? { id: "u_123", email: "demo@example.com", anonymous: false }
          : { anonymous: true };

      async function flush(reason: string) {
        if (buffer.length === 0) return;

        const events = buffer;
        buffer = [];

        const payload = {
          // include key in body so sendBeacon works (no headers support)
          project_write_key: WRITE_KEY,
          session_id: sessionId,
          seq: seq++,
          ts: new Date().toISOString(),
          url: location.href,
          user: user(),
          events,
        };

        try {
          const body = JSON.stringify(payload);
          if ("sendBeacon" in navigator) {
            const blob = new Blob([body], { type: "application/json" });
            navigator.sendBeacon(INGEST, blob);
          } else {
            await fetch(INGEST, {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${WRITE_KEY}`,
              },
              body,
            });
          }
        } catch (e) {
          console.warn("rrHog flush failed", e);
        }
      }

      function schedule() {
        clearTimeout(timer);
        timer = setTimeout(() => void flush("timer"), flushIntervalMs);
      }

      record({
        emit(event: any) {
          buffer.push(event);
          if (buffer.length >= batchSize) void flush("batch");
          else schedule();
        },
      });

      // Flush when tab goes to background or before unload
      document.addEventListener("visibilitychange", () => {
        if (document.visibilityState === "hidden") void flush("hidden");
      });
      window.addEventListener("beforeunload", () => void flush("beforeunload"));
    })();
  }, []);

  return (
    <div className="font-sans grid grid-rows-[20px_1fr_20px] items-center justify-items-center min-h-screen p-8 pb-20 gap-16 sm:p-20">
      <main className="flex flex-col gap-[32px] row-start-2 items-center sm:items-start">
        <Image
          className="dark:invert"
          src="/next.svg"
          alt="Next.js logo"
          width={180}
          height={38}
          priority
        />

        {/* Recording status */}
        <div className="rounded-lg border border-black/10 dark:border-white/15 px-4 py-3 w-full sm:w-[560px] bg-black/[.03] dark:bg-white/[.04]">
          <div className="text-sm/6">
            <strong>Recording</strong> rrweb events →
            <code className="ml-1 bg-black/[.05] dark:bg-white/[.06] px-1 py-0.5 rounded">
              {INGEST}
            </code>
          </div>
          <div className="mt-2 flex items-center gap-4">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="radio"
                name="identity"
                checked={mode === "anon"}
                onChange={() => setMode("anon")}
              />
              Anonymous
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="radio"
                name="identity"
                checked={mode === "user"}
                onChange={() => setMode("user")}
              />
              Logged-in demo user
              <span className="opacity-70">(id: u_123)</span>
            </label>
          </div>
        </div>

        {/* “Try me” interactions to generate events */}
        <div className="flex gap-4 items-center flex-col sm:flex-row">
          <button
            className="rounded-full border border-solid border-transparent transition-colors flex items-center justify-center bg-foreground text-background gap-2 hover:bg-[#383838] dark:hover:bg-[#ccc] font-medium text-sm sm:text-base h-10 sm:h-12 px-4 sm:px-5"
            onClick={() => alert("Hello from rrHog demo!")}
          >
            Click me
          </button>
          <button
            className="rounded-full border border-solid border-black/[.08] dark:border-white/[.145] transition-colors flex items-center justify-center hover:bg-[#f2f2f2] dark:hover:bg-[#1a1a1a] hover:border-transparent font-medium text-sm sm:text-base h-10 sm:h-12 px-4 sm:px-5 w-full sm:w-auto md:w-[158px]"
            onClick={() => {
              const x = prompt("Type something");
              console.log("Prompt value:", x);
            }}
          >
            Open prompt
          </button>
          <button
            className="rounded-full border border-solid border-black/[.08] dark:border-white/[.145] transition-colors flex items-center justify-center hover:bg-[#f2f2f2] dark:hover:bg-[#1a1a1a] hover:border-transparent font-medium text-sm sm:text-base h-10 sm:h-12 px-4 sm:px-5 w-full sm:w-auto"
            onClick={() => {
              location.hash = `#${Math.floor(Math.random() * 1000)}`;
            }}
          >
            Change hash
          </button>
        </div>

        {/* Default sample instructions */}
        <ol className="font-mono list-inside list-decimal text-sm/6 text-center sm:text-left">
          <li className="mb-2 tracking-[-.01em]">
            Edit{" "}
            <code className="bg-black/[.05] dark:bg-white/[.06] font-mono font-semibold px-1 py-0.5 rounded">
              src/app/page.tsx
            </code>{" "}
            and keep interacting with the page.
          </li>
          <li className="tracking-[-.01em]">
            Open the analytics UI at{" "}
            <a
              href="http://localhost:3000"
              target="_blank"
              rel="noreferrer"
              className="underline"
            >
              http://localhost:3000
            </a>{" "}
            to see sessions & replays.
          </li>
        </ol>
      </main>

      {/* Footer from the sample template */}
      <footer className="row-start-3 flex gap-[24px] flex-wrap items-center justify-center">
        <a
          className="flex items-center gap-2 hover:underline hover:underline-offset-4"
          href="https://nextjs.org/learn?utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"
          target="_blank"
          rel="noopener noreferrer"
        >
          <Image aria-hidden src="/file.svg" alt="File icon" width={16} height={16} />
          Learn
        </a>
        <a
          className="flex items-center gap-2 hover:underline hover:underline-offset-4"
          href="https://vercel.com/templates?framework=next.js&utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"
          target="_blank"
          rel="noopener noreferrer"
        >
          <Image aria-hidden src="/window.svg" alt="Window icon" width={16} height={16} />
          Examples
        </a>
        <a
          className="flex items-center gap-2 hover:underline hover:underline-offset-4"
          href="https://nextjs.org?utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"
          target="_blank"
          rel="noopener noreferrer"
        >
          <Image aria-hidden src="/globe.svg" alt="Globe icon" width={16} height={16} />
          Go to nextjs.org →
        </a>
      </footer>
    </div>
  );
}
