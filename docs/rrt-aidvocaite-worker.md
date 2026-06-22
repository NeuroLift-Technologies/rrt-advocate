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

## Runtime shape

The Worker serves two surfaces from the same deployment:

- `/` and non-`/api/` paths are delegated to the static asset binding and serve
  the browser chat UI from `public/`.
- `/api/*` paths are handled in `src/index.ts`; unknown API routes return
  `404`.

The browser keeps an in-memory `chatHistory`, posts it to `/api/chat`, reads the
SSE response stream with `ReadableStream.getReader()`, and appends chunks from
either Workers AI-style `response` fields or OpenAI-style
`choices[0].delta.content` fields. The UI does not persist chat history across
page reloads.

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

### Local smoke tests

After `npm run dev` starts Wrangler, verify the non-model route first:

```bash
curl http://localhost:8787/api/health
```

Expected response:

```json
{ "ok": true, "assistant": "RRT AIdvocAIte" }
```

If `npm run dev` opens a Wrangler OAuth flow in an unauthenticated environment,
you can still exercise the non-model health route with local mode:

```bash
npx wrangler dev --local --ip 127.0.0.1
```

In local mode the `ASSETS` binding is available, but the `AI` binding is not
supported. Use authenticated normal `wrangler dev` before testing `/api/chat` or
browser model responses.

Then verify the chat route with a short prompt:

```bash
curl -i http://localhost:8787/api/chat \
  -H "content-type: application/json" \
  --data '{"messages":[{"role":"user","content":"I am overwhelmed and shutting down"}]}'
```

The response should be `text/event-stream` and include an `x-rrt-risk-level`
header. For the example above, the local pre-check sees two high-distress
signals (`overwhelm language` and `shutdown language`), so the expected header
is `x-rrt-risk-level: high`.

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
3. Finds the latest user message and runs the local text pre-check against that
   message only.
4. Replaces any caller-supplied system messages with the Worker-owned RRT system
   prompt plus a risk-instruction system message.
5. Streams the Workers AI response as `text/event-stream`.
6. Sets `x-rrt-risk-level` to `stable`, `elevated`, `high`, or `critical`.

Only `POST` is allowed for `/api/chat`; other methods return `405`. Requests without a non-empty user message return `400`.

Risk levels are route-local response-framing hints:

| Level | Source condition |
|---|---|
| `stable` | No configured local distress patterns matched. |
| `elevated` | One high-distress pattern matched. |
| `high` | Two or more high-distress patterns matched. |
| `critical` | Any self-harm pattern matched. |

For `critical` responses, the Worker injects a crisis-resource sentence into the
model instructions before the user conversation. The Worker still returns a
streamed model response; it does not call emergency services or escalate outside
the user's control.

## Troubleshooting

| Symptom | Likely cause | Check |
|---|---|---|
| `npm run check` creates a root `package-lock.json` | `npm install` was run without `--no-package-lock` | Remove the lockfile for docs-only work unless the dependency change is intentional. |
| `npm run dev` opens a browser-based OAuth prompt | Wrangler needs Cloudflare authentication before remote Workers AI dev can start | Complete `npx wrangler login`, or use `npx wrangler dev --local --ip 127.0.0.1` for `/api/health` only. |
| `wrangler dev` starts but `/api/chat` fails | The Cloudflare account is not authenticated or Workers AI is not enabled | Run `npx wrangler whoami`; confirm the account has Workers AI access. |
| Browser UI shows a connection error | `/api/chat` returned a non-2xx response or the SSE stream closed before content arrived | Test `/api/health`, then call `/api/chat` with `curl -i` to inspect status and headers. |
| `x-rrt-risk-level` is missing | The request did not reach the successful streaming path | Check for `400`, `405`, `404`, or `500` responses first. |
| Static UI routes fail while API routes work | Asset binding or `public/` path is misconfigured | Confirm `wrangler.jsonc` still binds `ASSETS` to `./public`. |

## Safety and architecture constraints

The Python crisis engine remains the source implementation for local-first RRT behavior. The Worker surface is a hosted assistant layer and does not replace the Python CDE, TOI/OTOI, or intervention pipeline.

The Worker pre-check is a lightweight route-level signal for response framing. Do not treat it as a replacement for `config/crisis_thresholds.yaml`, the Python CDE, or the package-local CDE library. Changes to crisis detection thresholds, persona blending, or safety-critical intervention behavior require escalation under the repository governance rules.
