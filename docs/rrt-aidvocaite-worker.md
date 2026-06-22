# RRT AIdvocAIte Worker Assistant

This repo includes a deployable RRT AIdvocAIte chat assistant adapted from `nlt-chat-1`.

The Worker adds:
- `/api/chat` streaming chat responses through Cloudflare Workers AI.
- An RRT-specific system prompt grounded in Ash, Sol, Echo, Kai, and Myra.
- A local text pre-check that labels stable, elevated, high, or critical distress signals before the model responds.
- A compact browser UI in `public/` for calm, consent-led support.

## Source map

| Path | Role |
|---|---|
| `package.json` | Root Worker scripts and direct dev dependency on `wrangler` 4.59.1. |
| `wrangler.jsonc` | Worker configuration: `src/index.ts`, `public/` assets, Workers AI binding `AI`, observability, and source maps. |
| `src/index.ts` | Worker entrypoint, API routes, prompt, streaming response handling, and local text pre-check. |
| `src/types.ts` | Worker `Env`, chat message, request body, and risk-level interfaces. |
| `public/index.html`, `public/chat.js` | Static chat UI that calls `/api/chat` and displays the `x-rrt-risk-level` header. |

The package under `packages/rrt-advocate/` is the local-first TypeScript Crisis Detection Engine library. It is not the Wrangler Worker package; run its build/test commands from `packages/rrt-advocate/`, and run Worker commands from the repository root.

## Local Worker workflow

Run these commands from the repository root:

```bash
npm install
npm run dev
npm run check
```

Useful scripts:

| Command | What it does |
|---|---|
| `npm run dev` / `npm start` | Starts `wrangler dev` for local Worker/UI testing. |
| `npm run check` | Runs `tsc --noEmit` and `wrangler deploy --dry-run` without publishing. |
| `npm run cf-typegen` | Runs `wrangler types`; use after changing `wrangler.jsonc` bindings. |
| `npm run deploy` | Runs `wrangler deploy`; production deployment requires explicit human approval under OTOI. |

`wrangler.jsonc` binds static assets as `ASSETS` and Workers AI as `AI`. Workers AI requests run against Cloudflare infrastructure, including during local Worker development, so use an authenticated Cloudflare account with Workers AI enabled before testing model responses.

This repository currently tracks `packages/rrt-advocate/package-lock.json` for the CDE package, but does not track a root `package-lock.json` for the Worker tooling. If `npm install` creates a root lockfile during local verification, either intentionally commit it as a separate dependency-management change or remove it before opening a documentation-only PR. In ephemeral environments where you only need to run the root scripts, `npm install --no-package-lock` avoids lockfile churn.

## API contract

### `GET /api/health`

Returns a JSON health response:

```json
{ "ok": true, "assistant": "RRT AIdvocAIte" }
```

### `POST /api/chat`

Accepts recent chat messages:

```json
{
  "messages": [
    { "role": "user", "content": "I am overwhelmed and shutting down" }
  ]
}
```

The Worker:

1. Keeps only valid `system`, `user`, and `assistant` messages.
2. Truncates each message to 4,000 characters and keeps the latest 16 messages.
3. Runs the local text pre-check in `src/index.ts`.
4. Streams the Workers AI response as `text/event-stream`.
5. Sets `x-rrt-risk-level` to `stable`, `elevated`, `high`, or `critical`.

Only `POST` is allowed for `/api/chat`; other methods return `405`. Requests without a non-empty user message return `400`.

## Safety and architecture constraints

The Python crisis engine remains the source implementation for local-first RRT behavior. The Worker surface is a hosted assistant layer and does not replace the Python CDE, TOI/OTOI, or intervention pipeline.

The Worker pre-check is a lightweight route-level signal for response framing. Do not treat it as a replacement for `config/crisis_thresholds.yaml`, the Python CDE, or the package-local CDE library. Changes to crisis detection thresholds, persona blending, or safety-critical intervention behavior require escalation under the repository governance rules.
