# Scalaton — Frontend

A TypeScript + Vite + React single-page app for the Scalaton AI Operations Support
Co-pilot, scaffolded after the
[dbxmetagen](https://github.com/databricks-industry-solutions/dbxmetagen)
dashboard and grounded in the specifications under [`../docs`](../docs).

It presents the operational lifecycle — **Triage → War Room → Escalation →
Change Request**, plus a streaming **Co-pilot** chat — as an in-app operator
console. Every AI output is a proposal awaiting explicit human approval
(design-specification §8). The Microsoft Teams Adaptive Cards remain the
specification's approval surface; this console complements them.

## Stack

- Vite + React 19 + TypeScript (TSX)
- Tailwind CSS + PostCSS + autoprefixer
- Vitest for unit tests

## Scripts

```bash
npm install        # install dependencies
npm run dev        # start the dev server (mock mode by default)
npm run build      # type-check and produce the production build in dist/
npm run preview    # serve the production build locally
npm test           # run unit tests (the pure SSE reducer and utilities)
npm run lint       # oxlint
```

## Configuration

Only [`src/config/env.ts`](src/config/env.ts) reads environment variables; every
variable has a default there and a matching entry in [`.env.example`](.env.example).
Copy it to `.env.local` to override:

| Variable | Default | Purpose |
| --- | --- | --- |
| `VITE_API_BASE_URL` | `/api` | Single API base URL; all endpoints derive from it. |
| `VITE_API_MODE` | `mock` | `mock` (no backend) or `live` (proxied backend). |
| `VITE_DEV_PROXY_TARGET` | `http://localhost:8000` | Dev-server proxy target for `/api` in live mode. |
| `VITE_ENABLE_EXTERNAL_WRITES` | `false` | Feature flag for mutating external writes (off in dev/test). |

In **mock mode** (the default) the app runs end to end without a backend, using
fixtures shaped to design-specification §5. In **live mode** the Vite dev server
proxies `/api` to the backend origin; production requests stay same-origin (no
loosened CORS).

## Data layer

All backend calls go through [`src/api/apiClient.ts`](src/api/apiClient.ts)
(fetch + cache); components never call `fetch` directly. Wire types live in
[`src/types/wire.ts`](src/types/wire.ts), derived from the §5 contracts. The
co-pilot stream is split into a pure, tested reducer
([`src/api/sseReducer.ts`](src/api/sseReducer.ts)) and a transport client
([`src/api/streamClient.ts`](src/api/streamClient.ts)).

> The browser `/api/*` endpoints are a net-new backend-for-frontend contract
> (plan decision D4), pending backend-owner confirmation. See
> [`../docs/scalaton-technology-architecture.md`](../docs/scalaton-technology-architecture.md) §4.1.

## Build output

`dist/` is generated and git-ignored; build it in CI/deploy rather than
committing it. Edit sources and rebuild — never hand-patch `dist/`.

## Deploy (Databricks App)

This is a Databricks App served by the Python/FastAPI backend. The current Release 1
scaffold uses mocks and typed contracts; live integrations are a Release 2 concern.
When deploying, finalize the app
definition ([`../app.yaml.example`](../app.yaml.example)) with the
`databricks-apps-python` and `databricks-app-design` skills: bind to
`DATABRICKS_APP_PORT`, reference resources via `valueFrom`, and deploy through
Asset Bundles if a `databricks.yml` is present. Confirm the app is serving with
`databricks apps logs <name>` before declaring success.
