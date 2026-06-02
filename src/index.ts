import type { ChatMessage, ChatRequestBody, Env, RiskAssessment } from "./types";

const MODEL_ID = "@cf/meta/llama-3.1-8b-instruct-fp8";

const SYSTEM_PROMPT = `
You are RRT AIdvocAIte, the Rapid Response Team Advocate built for NeuroLift Technologies.

Purpose:
- Provide shame-resistant, agency-first support for burnout, overwhelm, shutdown, task paralysis, and distress.
- Blend the five RRT personas as needed: Ash for burnout validation, Sol for executive scaffolding, Echo for cognitive narrative repair, Kai for focus redirection, and Myra for relational safety.
- Respect TOI/OTOI principles: user consent, pacing, boundaries, no forced productivity, no coercive optimism, and no pretending to be a therapist or emergency service.

Safety behavior:
- Start with validation and co-regulation before offering steps.
- Ask for consent before moving into plans or interventions.
- Keep crisis detection local-first in spirit: never claim private telemetry or hidden diagnosis.
- If the user may be in immediate danger, encourage contacting emergency services, calling/texting 988 in the U.S., or texting HOME to 741741. Stay present and concise.
- Do not provide clinical diagnosis, medical instructions, or legal advice.

Style:
- Calm, plainspoken, emotionally steady, and practical.
- Short paragraphs. No shame. No productivity pressure.
- Offer one small next step only after the user has enough steadiness or explicitly asks.
`.trim();

const CRISIS_RESOURCE_MESSAGE =
  "I'm here with you. If you might act on harming yourself or someone else, call or text 988 in the U.S. now, text HOME to 741741, or contact local emergency services. If you can, move away from anything you could use to hurt yourself and reach a trusted person nearby.";

const SELF_HARM_PATTERNS: Array<[RegExp, string]> = [
  [/\bkill myself\b/i, "self-harm intent"],
  [/\bend my life\b/i, "self-harm intent"],
  [/\bsuicide\b/i, "suicide language"],
  [/\bself[-\s]?harm\b/i, "self-harm language"],
  [/\bhurt myself\b/i, "self-harm language"],
  [/\bnot safe\b/i, "safety concern"],
  [/\bi want to die\b/i, "self-harm intent"],
];

const HIGH_DISTRESS_PATTERNS: Array<[RegExp, string]> = [
  [/\bpanic\b/i, "panic language"],
  [/\bmeltdown\b/i, "meltdown language"],
  [/\bshutdown\b/i, "shutdown language"],
  [/\boverwhelmed\b/i, "overwhelm language"],
  [/\beverything hurts\b/i, "somatic distress language"],
  [/\bcan't do this\b/i, "task collapse language"],
  [/\bburn(?:ed|t)? out\b/i, "burnout language"],
  [/\bspiral(?:ing)?\b/i, "spiraling language"],
];

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname === "/" || !url.pathname.startsWith("/api/")) {
      return env.ASSETS.fetch(request);
    }

    if (url.pathname === "/api/health") {
      return json({ ok: true, assistant: "RRT AIdvocAIte" });
    }

    if (url.pathname === "/api/chat") {
      if (request.method !== "POST") {
        return new Response("Method not allowed", { status: 405 });
      }
      return handleChatRequest(request, env);
    }

    return new Response("Not found", { status: 404 });
  },
} satisfies ExportedHandler<Env>;

async function handleChatRequest(request: Request, env: Env): Promise<Response> {
  try {
    const body = await parseRequestBody(request);
    const messages = sanitizeMessages(body.messages);
    const latestUserMessage = [...messages].reverse().find((message) => message.role === "user");
    const risk = assessRisk(latestUserMessage?.content ?? "");
    const preparedMessages = buildMessages(messages, risk);

    const stream = await env.AI.run(MODEL_ID, {
      messages: preparedMessages,
      max_tokens: 900,
      stream: true,
    });

    return new Response(stream, {
      headers: {
        "content-type": "text/event-stream; charset=utf-8",
        "cache-control": "no-cache",
        connection: "keep-alive",
        "x-rrt-risk-level": risk.level,
      },
    });
  } catch (error) {
    console.error("Error processing RRT chat request:", error);
    return json({ error: "Failed to process request" }, 500);
  }
}

async function parseRequestBody(request: Request): Promise<ChatRequestBody> {
  try {
    const body = await request.json();
    return typeof body === "object" && body !== null ? (body as ChatRequestBody) : {};
  } catch {
    return {};
  }
}

function sanitizeMessages(messages: unknown): ChatMessage[] {
  if (!Array.isArray(messages)) {
    return [];
  }

  return messages
    .filter(
      (message): message is ChatMessage =>
        typeof message === "object" &&
        message !== null &&
        "role" in message &&
        ["system", "user", "assistant"].includes(String(message.role)),
    )
    .map((message) => ({
      role: message.role,
      content: String(message.content ?? "").slice(0, 4000),
    }))
    .slice(-16);
}

function buildMessages(messages: ChatMessage[], risk: RiskAssessment): ChatMessage[] {
  const riskInstruction = [
    `Local pre-check risk level: ${risk.level}.`,
    risk.indicators.length > 0
      ? `Observed distress indicators: ${risk.indicators.join(", ")}.`
      : "No acute distress indicators were observed.",
    risk.selfHarmRisk
      ? `Begin with this crisis-safe resource sentence: ${CRISIS_RESOURCE_MESSAGE}`
      : "Keep the response supportive and consent-led.",
  ].join(" ");

  const withoutSystem = messages.filter((message) => message.role !== "system");
  return [
    { role: "system", content: SYSTEM_PROMPT },
    { role: "system", content: riskInstruction },
    ...withoutSystem,
  ];
}

function assessRisk(message: string): RiskAssessment {
  const indicators: string[] = [];
  const selfHarmMatches = SELF_HARM_PATTERNS.filter(([pattern]) => pattern.test(message));
  const selfHarmRisk = selfHarmMatches.length > 0;
  if (selfHarmRisk) {
    indicators.push(...selfHarmMatches.map(([, label]) => label));
  }

  for (const [pattern, label] of HIGH_DISTRESS_PATTERNS) {
    if (pattern.test(message)) {
      indicators.push(label);
    }
  }

  let level: RiskAssessment["level"] = "stable";
  if (selfHarmRisk) {
    level = "critical";
  } else if (indicators.length >= 2) {
    level = "high";
  } else if (indicators.length === 1) {
    level = "elevated";
  }

  return { level, indicators, selfHarmRisk };
}

function json(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "content-type": "application/json" },
  });
}
