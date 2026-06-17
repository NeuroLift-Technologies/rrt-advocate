/**
 * CDE Layer 3: Behavioral Pattern Analysis.
 *
 * Local-first — no external dependencies. Faithful TypeScript port of
 * `src/crisis/detectors/behavioral_layer.py`.
 *
 * Tracks response latency, message complexity, and looping patterns across a
 * session to detect behavioral indicators of distress that may not be visible
 * in the text content alone.
 *
 * Privacy note: only message metadata (timing, length, hashed word tokens) is
 * stored — never raw message content. Word tokens are passed through an
 * HMAC-SHA256 so set-overlap (Jaccard) behaviour is identical to using raw
 * words while remaining non-reversible.
 */

import { createHmac, randomBytes } from 'node:crypto';
import { type BehavioralAnalysisResult, type ComplexityTrend } from './types.js';

const TOKEN_HASH_KEY: Buffer = process.env.RRT_BEHAVIORAL_TOKEN_KEY
  ? Buffer.from(process.env.RRT_BEHAVIORAL_TOKEN_KEY, 'utf-8')
  : randomBytes(32);

function hashToken(word: string): string {
  return createHmac('sha256', TOKEN_HASH_KEY).update(word, 'utf-8').digest('hex');
}

/** Punctuation stripped from word edges (mirrors Python `str.strip(".,!?;:")`). */
const EDGE_PUNCTUATION = new Set(['.', ',', '!', '?', ';', ':']);

/**
 * Trim leading/trailing edge punctuation from a word. Implemented as a linear
 * character walk rather than a regex to avoid backtracking (ReDoS): the
 * equivalent `^[.,!?;:]+|[.,!?;:]+$` form is a polynomial regex on attacker-
 * controlled input (e.g. long runs of `!`).
 */
function stripEdgePunctuation(word: string): string {
  let start = 0;
  let end = word.length;
  while (start < end && EDGE_PUNCTUATION.has(word[start]!)) start++;
  while (end > start && EDGE_PUNCTUATION.has(word[end - 1]!)) end--;
  return word.slice(start, end);
}

/** Metadata record for a single user message. No content stored. */
interface MessageRecord {
  /** Unix timestamp in seconds. */
  timestamp: number;
  wordCount: number;
  charCount: number;
  sentenceCount: number;
  /** Punctuation chars / total chars. */
  punctuationDensity: number;
  /** Hashed word tokens, for looping (Jaccard) detection. */
  wordSet: Set<string>;
}

function round3(value: number): number {
  return Math.round(value * 1000) / 1000;
}

function jaccard(a: Set<string>, b: Set<string>): number {
  let intersection = 0;
  for (const t of a) {
    if (b.has(t)) intersection++;
  }
  const union = a.size + b.size - intersection;
  return union > 0 ? intersection / union : 0.0;
}

export class BehavioralLayer {
  // Latency anomaly threshold: >5 minutes between messages is flagged.
  private static readonly LATENCY_ANOMALY_THRESHOLD_SECONDS = 300;
  // Looping detection: Jaccard similarity above this threshold = looping.
  private static readonly LOOPING_SIMILARITY_THRESHOLD = 0.55;

  readonly windowSize: number;
  private readonly records: MessageRecord[] = [];
  private lastMessageTime: number | null = null;

  /** @param windowSize Number of recent messages to analyze for trends. */
  constructor(windowSize = 5) {
    this.windowSize = windowSize;
  }

  /** Parse a message and record its behavioral metadata. */
  recordMessage(text: string): MessageRecord {
    const now = Date.now() / 1000;
    const words = text ? text.split(/\s+/).filter((w) => w.length > 0) : [];
    const wordSet = new Set<string>();
    for (const w of words) {
      const normalized = stripEdgePunctuation(w.toLowerCase());
      if (normalized.length > 2) {
        wordSet.add(hashToken(normalized));
      }
    }
    const sentences = text.split(/[.!?]+/).filter((s) => s.trim().length > 0);
    const sentenceCount = Math.max(1, sentences.length);
    let punctCount = 0;
    for (const c of text) {
      if ('.,!?;:()[]{}"\''.includes(c)) punctCount++;
    }
    const punctDensity = punctCount / Math.max(text.length, 1);

    const record: MessageRecord = {
      timestamp: now,
      wordCount: words.length,
      charCount: text.length,
      sentenceCount,
      punctuationDensity: punctDensity,
      wordSet,
    };
    this.records.push(record);
    if (this.records.length > this.windowSize) {
      this.records.shift();
    }
    this.lastMessageTime = now;
    return record;
  }

  /** Analyze the behavioral signals of a new message. */
  analyze(text: string): BehavioralAnalysisResult {
    if (!text || !text.trim()) {
      return {
        responseLatency: null,
        latencyAnomaly: false,
        messageComplexity: 0.0,
        complexityTrend: 'normal',
        loopingDetected: false,
        loopingSimilarity: 0.0,
        confidenceScore: 0.0,
        metrics: { wordCount: 0, charCount: 0, sentenceCount: 0, punctuationDensity: 0.0 },
      };
    }

    const prevTime = this.lastMessageTime;
    const record = this.recordMessage(text);

    let latency: number | null = null;
    let latencyAnomaly = false;
    if (prevTime !== null) {
      latency = record.timestamp - prevTime;
      latencyAnomaly = latency > BehavioralLayer.LATENCY_ANOMALY_THRESHOLD_SECONDS;
    }

    const complexity = this.computeComplexity(record);
    const complexityTrend = this.computeComplexityTrend();
    const loopingSimilarity = this.computeLoopingSimilarity(record);
    const loopingDetected = loopingSimilarity >= BehavioralLayer.LOOPING_SIMILARITY_THRESHOLD;

    const confidence = this.computeConfidence(
      latencyAnomaly,
      complexity,
      complexityTrend,
      loopingDetected,
    );

    return {
      responseLatency: latency,
      latencyAnomaly,
      messageComplexity: complexity,
      complexityTrend,
      loopingDetected,
      loopingSimilarity,
      confidenceScore: confidence,
      metrics: {
        wordCount: record.wordCount,
        charCount: record.charCount,
        sentenceCount: record.sentenceCount,
        punctuationDensity: record.punctuationDensity,
      },
    };
  }

  /**
   * Compute a normalized complexity score. Very short or fragmented messages
   * score low (0.0 = very simple/distressed); richly engaged messages score
   * high (1.0).
   */
  private computeComplexity(record: MessageRecord): number {
    const wordScore = Math.min(record.wordCount / 30.0, 1.0);
    const avgWordsPerSentence = record.wordCount / record.sentenceCount;
    const sentenceScore = Math.min(avgWordsPerSentence / 15.0, 1.0);
    return round3(wordScore * 0.6 + sentenceScore * 0.4);
  }

  /** Classify the trend in message complexity over the window. */
  private computeComplexityTrend(): ComplexityTrend {
    if (this.records.length < 3) {
      return 'normal';
    }
    const complexities = this.records.map((r) => this.computeComplexity(r));
    const recent = complexities.slice(-3);
    const delta = recent[recent.length - 1] - recent[0];
    if (delta < -0.3) {
      return 'fragmenting';
    }
    if (delta < -0.15) {
      return 'simplifying';
    }
    return 'normal';
  }

  /**
   * Compute Jaccard similarity between the current message and recent history.
   * High similarity (>0.55) across consecutive messages indicates looping.
   */
  private computeLoopingSimilarity(current: MessageRecord): number {
    if (this.records.length < 2) {
      return 0.0;
    }
    const prevRecords = this.records.slice(0, -1); // all except the one just added
    if (prevRecords.length === 0) {
      return 0.0;
    }
    const currentWords = current.wordSet;
    if (currentWords.size === 0) {
      return 0.0;
    }

    const similarities: number[] = [];
    for (const prev of prevRecords.slice(-3)) {
      if (prev.wordSet.size === 0) {
        continue;
      }
      similarities.push(jaccard(currentWords, prev.wordSet));
    }
    return similarities.length > 0 ? round3(Math.max(...similarities)) : 0.0;
  }

  private computeConfidence(
    latencyAnomaly: boolean,
    complexity: number,
    complexityTrend: ComplexityTrend,
    loopingDetected: boolean,
  ): number {
    let confidence = 0.0;
    if (latencyAnomaly) {
      confidence += 0.1;
    }
    if (complexity < 0.1) {
      confidence += 0.2;
    } else if (complexity < 0.2) {
      confidence += 0.1;
    }
    if (complexityTrend === 'fragmenting') {
      confidence += 0.15;
    } else if (complexityTrend === 'simplifying') {
      confidence += 0.05;
    }
    if (loopingDetected) {
      confidence += 0.2;
    }
    return Math.min(1.0, confidence);
  }

  /** Reset all behavioral tracking (new session). */
  reset(): void {
    this.records.length = 0;
    this.lastMessageTime = null;
  }
}
