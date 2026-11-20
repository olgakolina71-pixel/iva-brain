# IVA Brain — Cloudflare runtime

This is the Cloudflare Worker adaptation of the IVA Brain prototype.

- Durable Object SQLite persists state, memories, and experiences.
- One alarm every 10 minutes advances its internal clock and autonomous loop.
- Internal time: 1 real hour = 1 IVA day.
- The API is protected by a Worker secret named `API_TOKEN`.
- This is a simulated cognitive architecture; it does not claim consciousness.
- No training datasets are loaded. Updates are driven by runtime experiences and feedback.

## Endpoints

All requests need `Authorization: Bearer YOUR_API_TOKEN`.

- `GET /status`
- `GET /memories?limit=20`
- `POST /event` JSON: `{"event":"text"}`
- `POST /feedback` JSON: `{"value":"good|bad|neutral"}`
- `POST /sleep`
- `POST /wake`

## Deploy from GitHub

1. In Cloudflare Dashboard, Workers & Pages → Create → Connect to Git.
2. Connect this repository and select branch `main`.
3. Build command: `npx wrangler deploy`; no build output directory.
4. After first deployment, open Worker Settings → Variables and Secrets and add a secret named `API_TOKEN`.
5. Generate a long random token locally and store it somewhere private. Never commit it.

The Durable Object migration in `wrangler.jsonc` creates SQLite-backed storage.
