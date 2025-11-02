// Server Component
export const dynamic = "force-dynamic"; // no caching

type SessionRow = {
  session_id: string;
  started_at: string;
  user_id?: string;
  user_email?: string;
};

async function getSessions(): Promise<SessionRow[]> {
  const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  const READ_KEY =
    process.env.READ_KEY ?? process.env.NEXT_PUBLIC_READ_KEY ?? "dev_read_123";

  const res = await fetch(`${API}/sessions?read_key=${READ_KEY}`, {
    cache: "no-store",
  });

  if (!res.ok) return [];
  const data = await res.json();
  return data.sessions ?? [];
}

export default async function Home() {
  const sessions = await getSessions();

  return (
    <div className="font-sans grid grid-rows-[20px_1fr_20px] items-center justify-items-center min-h-screen p-8 pb-20 gap-16 sm:p-20">
      <main className="flex flex-col gap-[24px] row-start-2 max-w-[900px] w-full">
        <h1 className="text-2xl font-semibold">rrHog — Sessions</h1>
        {sessions.length === 0 ? (
          <p className="opacity-70">
            No sessions yet. Open your demo site at{" "}
            <a className="underline" href="http://localhost:3001" target="_blank" rel="noreferrer">
              http://localhost:3001
            </a>{" "}
            and interact to generate some rrweb events.
          </p>
        ) : (
          <ul className="space-y-2">
            {sessions.map((s) => (
              <li key={s.session_id} className="rounded-lg border border-black/10 dark:border-white/15 p-3">
                <a className="underline" href={`/session/${s.session_id}`}>
                  {s.session_id.slice(0, 8)}…
                </a>
                <div className="text-sm opacity-80">
                  {new Date(s.started_at).toLocaleString()} •{" "}
                  {s.user_email || s.user_id || "anon"}
                </div>
              </li>
            ))}
          </ul>
        )}
      </main>

      <footer className="row-start-3 flex gap-6 flex-wrap items-center justify-center">
        <a
          className="flex items-center gap-2 hover:underline hover:underline-offset-4"
          href="https://nextjs.org/learn?utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"
          target="_blank"
          rel="noopener noreferrer"
        >
          <img src="/file.svg" alt="" width={16} height={16} aria-hidden />
          Learn
        </a>
        <a
          className="flex items-center gap-2 hover:underline hover:underline-offset-4"
          href="https://vercel.com/templates?framework=next.js&utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"
          target="_blank"
          rel="noopener noreferrer"
        >
          <img src="/window.svg" alt="" width={16} height={16} aria-hidden />
          Templates
        </a>
        <a
          className="flex items-center gap-2 hover:underline hover:underline-offset-4"
          href="https://nextjs.org?utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"
          target="_blank"
          rel="noopener noreferrer"
        >
          <img src="/globe.svg" alt="" width={16} height={16} aria-hidden />
          nextjs.org →
        </a>
      </footer>
    </div>
  );
}
