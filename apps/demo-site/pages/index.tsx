import { useEffect, useState } from 'react';
import { initRRHog } from '@/lib/rrhog';

const INGEST = process.env.NEXT_PUBLIC_RRHOG_INGEST || 'http://localhost:8000/i';
const WRITE_KEY = process.env.NEXT_PUBLIC_RRHOG_WRITE_KEY || 'dev_write_123';

export default function Demo() {
  const [started, setStarted] = useState(false);
  const [mode, setMode] = useState<'anon'|'user'>('anon');

  useEffect(() => {
    if (started) return;
    setStarted(true);
    const user = mode === 'user' ? { id: 'u_123', email: 'demo@example.com' } : undefined;
    initRRHog({
      writeKey: WRITE_KEY,
      ingestUrl: INGEST,
      user
    });
  }, [started, mode]);

  return (
    <main style={{maxWidth: 800, margin: '2rem auto', fontFamily:'system-ui'}}>
      <h1>Demo Site (rrweb recorder)</h1>
      <p>This page records your interactions and sends rrweb events to the local API.</p>

      <div style={{display:'flex', gap: '1rem', marginTop:'1rem'}}>
        <button onClick={()=>alert('Hello!')}>Click me</button>
        <a href="#" onClick={(e)=>{e.preventDefault(); prompt('Type something');}}>Open prompt</a>
        <button onClick={()=>window.location.hash = `#${Math.floor(Math.random()*1000)}`}>Change hash</button>
      </div>

      <div style={{marginTop:'2rem'}}>
        <label>
          <input type="radio" name="identity" checked={mode==='anon'} onChange={()=>setMode('anon')} /> Anonymous
        </label>
        <label style={{marginLeft:'1rem'}}>
          <input type="radio" name="identity" checked={mode==='user'} onChange={()=>setMode('user')} /> Logged-in demo user
        </label>
        <p style={{opacity:0.7}}>Switching toggles user identity used in new events. (Reload to start a fresh session id.)</p>
      </div>

      <p style={{marginTop:'2rem'}}>
        Now open the <a href="http://localhost:3000" target="_blank" rel="noreferrer">Analytics UI</a> and watch the replay.
      </p>
    </main>
  );
}
