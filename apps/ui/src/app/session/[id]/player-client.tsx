"use client";

import { useEffect, useRef } from "react";
import "rrweb-player/dist/style.css";

export default function RRWebPlayerClient({ events }: { events: any[] }) {
  const container = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cleanup: (() => void) | undefined;

    (async () => {
      const Player = (await import("rrweb-player")).default as any;
      if (!container.current) return;
      const instance = new Player({
        target: container.current,
        props: { events, showController: true, width: 1024, height: 600 },
      });

      cleanup = () => {
        try {
          // rrweb-player doesn't expose a destroy API; remove DOM node
          if (container.current) container.current.innerHTML = "";
        } catch {}
      };
    })();

    return () => cleanup?.();
  }, [events]);

  return <div ref={container} />;
}
