import type { Metadata } from "next";
import dynamic from "next/dynamic";

// Client-only player component (SSR-safe)
const RRWebPlayer = dynamic(() => import("./player-client"), { ssr: false });

export const dynamic = "force-dynamic";

type ReplayData = { session_id: string; events: any[] };

export function generateMetadata({ params }: { params: { id: string } }): Metadata {
  return {
    title: `Session ${params.id} — rrHog`,
  };
}

async function getReplay(id: string): Promise<ReplayData> {
  const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  const READ_KEY =
    process.env.READ_KEY ?? process.env.NEXT_PUBLIC_READ_KEY ?? "dev_read_123";

  const res = await fetch(
    `${API}/replay?session_id=${encodeURIComponent(id)}&read_key=${READ_KEY}`,
    { cache: "no-store" }
  );
  if (!res.ok) return { session_id: id, events: [] };
  return res.json();
}

export default async function SessionPage({ params }: { params: { id: string } }) {
  const data = await getReplay(params.id);

  return (
    <div className="font-sans max-w-[1100px] mx-auto p-6 sm:p-10">
      <a href="/" className="underline">&larr; Back</a>
      <h1 className="text-2xl font-semibold mt-3">Session: {params.id}</h1>
      <div className="mt-6">
        <RRWebPlayer events={data.events} />
      </div>
    </div>
  );
}
