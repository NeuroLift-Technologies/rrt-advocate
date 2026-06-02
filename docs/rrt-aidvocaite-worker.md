# RRT AIdvocAIte Worker Assistant

This repo includes a deployable RRT AIdvocAIte chat assistant adapted from `nlt-chat-1`.

The Worker adds:
- `/api/chat` streaming chat responses through Cloudflare Workers AI.
- An RRT-specific system prompt grounded in Ash, Sol, Echo, Kai, and Myra.
- A local text pre-check that labels stable, elevated, high, or critical distress signals before the model responds.
- A compact browser UI in `public/` for calm, consent-led support.

```bash
npm install
npm run dev
npm run check
```

The Python crisis engine remains the source implementation for local-first RRT behavior. The Worker surface is a hosted assistant layer and does not replace the Python CDE, TOI/OTOI, or intervention pipeline.
