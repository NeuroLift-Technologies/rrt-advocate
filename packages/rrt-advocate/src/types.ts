/**
 * Shared types for the RRT Advocate Crisis Detection Engine (CDE).
 *
 * This is a faithful TypeScript port of the Python CDE under
 * `src/crisis/` in the `rrt-advocate` repository. Field names are
 * idiomatic camelCase; the underlying semantics, weights, thresholds,
 * and formulas are preserved exactly from the Python source.
 *
 * Local-first by design: every type here is produced by on-device
 * analysis with no external API calls.
 */

/**
 * Semantic fields representing distinct flavors of neurodivergent distress.
 * Each field maps to a set of keyword patterns. Multiple field activations
 * compound the overall crisis confidence score.
 */
export enum KeywordSemanticField {
  NEGATIVE_SELF_TALK = 'negative_self_talk',
  TASK_AVOIDANCE = 'task_avoidance',
  OVERWHELM = 'overwhelm',
  MELTDOWN = 'meltdown',
  SHUTDOWN = 'shutdown',
  HYPERFOCUS_LOOP = 'hyperfocus_loop',
  /** High-priority escalation trigger. */
  SELF_HARM_RISK = 'self_harm_risk',
}

/** Crisis severity level. Values mirror the Python `CrisisLevel` enum. */
export enum CrisisLevel {
  GREEN = 'stable',
  YELLOW = 'elevated',
  ORANGE = 'high',
  RED = 'critical',
  BLACK = 'emergency',
}

/** A single keyword pattern match within a semantic field. */
export interface KeywordMatch {
  field: KeywordSemanticField;
  /** The source regex pattern string that matched. */
  pattern: string;
  /** The exact substring that matched. */
  matchedText: string;
  /** Character offset of the match within the message. */
  position: number;
}

/** Result of Layer 1 keyword/semantic field analysis. */
export interface KeywordAnalysisResult {
  detectedFields: KeywordSemanticField[];
  matches: KeywordMatch[];
  confidenceScore: number;
  selfHarmDetected: boolean;
  primaryField: KeywordSemanticField | null;
}

/** A single sentiment analysis reading from one message. */
export interface SentimentReading {
  /** Overall polarity: -1.0 (very negative) to +1.0 (very positive). */
  compound: number;
  positive: number;
  negative: number;
  neutral: number;
  /** First 60 chars for debugging. */
  textSnippet: string;
}

/** Sentiment trend classification over the sliding window. */
export type SentimentTrend =
  | 'stable'
  | 'declining'
  | 'sharply_declining'
  | 'recovering';

/** Result of Layer 2 sentiment analysis for a single message. */
export interface SentimentAnalysisResult {
  currentReading: SentimentReading;
  /** Drop from recent window average (negative = drop). */
  polarityDrop: number;
  /** Average compound over the window (prior to this message). */
  windowAverage: number;
  trend: SentimentTrend;
  /** Contribution to overall crisis confidence. */
  confidenceScore: number;
  windowReadings: number[];
}

/** Message complexity trend classification. */
export type ComplexityTrend = 'normal' | 'simplifying' | 'fragmenting';

/** Result of Layer 3 behavioral pattern analysis. */
export interface BehavioralAnalysisResult {
  /** Seconds since last message (null if first message in session). */
  responseLatency: number | null;
  latencyAnomaly: boolean;
  /** Normalized complexity score (0.0–1.0). */
  messageComplexity: number;
  complexityTrend: ComplexityTrend;
  loopingDetected: boolean;
  /** Jaccard similarity to recent messages. */
  loopingSimilarity: number;
  confidenceScore: number;
  metrics: {
    wordCount: number;
    charCount: number;
    sentenceCount: number;
    punctuationDensity: number;
  };
}

/** Comprehensive crisis assessment, mirroring the Python `CrisisAssessment`. */
export interface CrisisAssessment {
  timestamp: Date;
  crisisLevel: CrisisLevel;
  primaryIndicators: string[];
  secondaryIndicators: string[];
  confidenceScore: number;
  /** Estimated duration in milliseconds, or null when unknown. */
  estimatedDuration: number | null;
  recommendedInterventions: string[];
  escalationThreshold: number;
  userSafetyScore: number;
  contextFactors: Record<string, unknown>;
}
