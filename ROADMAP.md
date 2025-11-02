# Roadmap

## v0 (MVP)
- [x] Ingest `/i` (batch rrweb) → NATS → CH bulk insert
- [x] Playback API + rrweb-player UI
- [x] Docker Compose + seed script
- [ ] Basic dashboards (pageviews, sessions, top pages)
- [ ] Per-project keys, rate limits

## v0.1–0.2
- [ ] Error events (console/network) + rage clicks
- [ ] Materialized views: retention, paths
- [ ] Quotas & retention policies per project
- [ ] S3/MinIO blob offload option for rrweb payloads

## v0.3+
- [ ] SSO (OIDC) & RBAC
- [ ] Multi-region ingest option
- [ ] Helm chart & Terraform examples
- [ ] Public demo with synthetic data