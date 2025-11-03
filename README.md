# rrHog — OSS Web Analytics & Session Replay (rrweb + ClickHouse)

> Open-source, self-hosted web analytics & session monitoring built on **rrweb** with **async ingestion** for rock-solid reliability.  
> Stack: **FastAPI** (ingest/read) • **NATS JetStream** (queue) • **ClickHouse** (events) • **Postgres** (meta) • **Next.js** (UI)

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Docs](https://img.shields.io/badge/docs-Architecture-brightgreen)](ARCHITECTURE.md)

## Quick start
```bash
docker compose up -d
# Demo site:       http://localhost:4001
# Analytics UI:    http://localhost:4000
# API (healthz):   http://localhost:8000/healthz
```

**Default dev keys**
- WRITE: `dev_write_123`
- READ:  `dev_read_123`

## Why rrHog?
Most analytics pipelines lose data when DBs or networks hiccup. rrHog **ACKs fast** and persists to a **durable queue** first, so ingestion keeps flowing even if storage is down.

## Features
- 🌀 Async ingest (`202` immediately)
- 🎥 rrweb session replay + rrweb-player UI
- ⚡ ClickHouse analytics tables
- 🧰 Next.js dashboard
- 🐳 Docker Compose one-box
- 🔒 Per-project keys + basic PII guards

See **[ARCHITECTURE.md](ARCHITECTURE.md)** for schemas and diagrams.


## Repo metadata (GitHub)
- **Description:** `rrHog — Open-source, self-hosted web analytics & session replay built on rrweb. FastAPI + NATS JetStream + ClickHouse, Next.js UI.`
- **Topics (11):** `open-source, self-hosted, web-analytics, session-replay, session-recording, rrweb, clickhouse, fastapi, nats-jetstream, postgresql, nextjs`

## Community
- Start here: [CONTRIBUTING.md](CONTRIBUTING.md)
- Code of Conduct: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- Support: [SUPPORT.md](SUPPORT.md)
- Roadmap: [ROADMAP.md](ROADMAP.md)

## Security
Please report vulnerabilities privately — see [SECURITY.md](SECURITY.md).

## License
MIT © 2025 You & Contributors — see [LICENSE](LICENSE).

> 💖 Want to support? Add a **GitHub Sponsors** button by creating `.github/FUNDING.yml` later.
