export interface Env {
  AI: Ai;
  ASSETS: { fetch: (request: Request) => Promise<Response> };
}

export interface ChatMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

export interface ChatRequestBody {
  messages?: ChatMessage[];
}

export type RiskLevel = "stable" | "elevated" | "high" | "critical";

export interface RiskAssessment {
  level: RiskLevel;
  indicators: string[];
  selfHarmRisk: boolean;
}
