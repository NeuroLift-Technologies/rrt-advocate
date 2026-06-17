/**
 * CDE Layer 2: Sentiment & Emotional Tone Analysis.
 *
 * Local-first — uses `vader-sentiment` for on-device polarity analysis when
 * available, and falls back to a simple heuristic lexicon otherwise (so the
 * layer always runs offline, mirroring the Python source which makes
 * `vaderSentiment` an optional dependency).
 *
 * Faithful TypeScript port of `src/crisis/detectors/sentiment_layer.py`.
 * Tracks sentiment polarity over a sliding window of messages to detect
 * polarity drops indicative of a deteriorating emotional state.
 */

import { createRequire } from 'node:module';
import {
  type SentimentAnalysisResult,
  type SentimentReading,
  type SentimentTrend,
} from './types.js';

/** Polarity scores returned by a VADER-compatible analyzer. */
interface VaderScores {
  compound: number;
  pos: number;
  neg: number;
  neu: number;
}

/** Minimal interface a pluggable sentiment analyzer must satisfy. */
export interface PolarityAnalyzer {
  polarity_scores(text: string): VaderScores;
}

const POSITIVE_WORDS: ReadonlySet<string> = new Set([
  'good', 'great', 'okay', 'fine', 'better', 'calm', 'happy',
  'relieved', 'hopeful', 'grateful', 'thank', 'love', 'safe',
]);

const NEGATIVE_WORDS: ReadonlySet<string> = new Set([
  'bad', 'terrible', 'awful', 'horrible', 'hate', 'depressed',
  'anxious', 'scared', 'hopeless', 'worthless', 'useless',
  'pain', 'hurt', 'suffering', 'stuck', 'broken', 'lost',
  'fail', "can't", 'cannot', 'never', 'worst', 'empty',
]);

/**
 * Attempt to load the optional `vader-sentiment` package. Returns a
 * VADER-compatible analyzer, or null if the package is not installed.
 */
function tryLoadVader(): PolarityAnalyzer | null {
  try {
    const require = createRequire(import.meta.url);
    const vader = require('vader-sentiment') as {
      SentimentIntensityAnalyzer?: PolarityAnalyzer;
    };
    // NOTE: in the JS `vader-sentiment` port, `SentimentIntensityAnalyzer`
    // exposes `polarity_scores` as a STATIC method — it is NOT an instantiable
    // class like Python's `vaderSentiment`. Do NOT `new` it: an instance has no
    // `polarity_scores` and would throw. We use the object directly, and guard
    // that the static method is actually present before trusting it.
    const analyzer = vader?.SentimentIntensityAnalyzer;
    return analyzer && typeof analyzer.polarity_scores === 'function' ? analyzer : null;
  } catch {
    return null;
  }
}

export class SentimentLayer {
  // Polarity drop thresholds for trend classification.
  private static readonly DECLINE_THRESHOLD = -0.15;
  private static readonly SHARP_DECLINE_THRESHOLD = -0.3;

  readonly windowSize: number;
  private readonly window: number[] = [];
  private readonly analyzer: PolarityAnalyzer | null;

  /**
   * @param windowSize Number of recent messages to track for trend analysis.
   * @param analyzer Optional VADER-compatible analyzer. When omitted, the
   *   layer auto-detects `vader-sentiment` and otherwise uses the built-in
   *   heuristic fallback.
   */
  constructor(windowSize = 5, analyzer?: PolarityAnalyzer | null) {
    this.windowSize = windowSize;
    this.analyzer = analyzer === undefined ? tryLoadVader() : analyzer;
  }

  /** Analyze the sentiment of a message and update the sliding window. */
  analyze(text: string): SentimentAnalysisResult {
    const reading = this.scoreText(text);
    const windowValues = [...this.window];
    const windowAverage =
      windowValues.length > 0
        ? windowValues.reduce((a, b) => a + b, 0) / windowValues.length
        : reading.compound;
    const polarityDrop = reading.compound - windowAverage;

    // Add current reading to the window (bounded to windowSize).
    this.window.push(reading.compound);
    if (this.window.length > this.windowSize) {
      this.window.shift();
    }

    const trend = this.classifyTrend(reading.compound, polarityDrop);
    const confidence = this.computeConfidence(reading, trend);

    return {
      currentReading: reading,
      polarityDrop,
      windowAverage,
      trend,
      confidenceScore: confidence,
      windowReadings: [...this.window],
    };
  }

  private scoreText(text: string): SentimentReading {
    const snippet = text.length > 60 ? text.slice(0, 60) : text;
    if (this.analyzer !== null) {
      const scores = this.analyzer.polarity_scores(text);
      return {
        compound: scores.compound,
        positive: scores.pos,
        negative: scores.neg,
        neutral: scores.neu,
        textSnippet: snippet,
      };
    }
    return this.fallbackScore(text, snippet);
  }

  /**
   * Simple heuristic polarity scorer for when VADER is unavailable.
   * Counts positive and negative indicator words for a rough compound score.
   */
  private fallbackScore(text: string, snippet: string): SentimentReading {
    const textLower = text.toLowerCase();
    const cleaned = textLower.replace(/[^a-z\s]/g, '');
    const words = new Set(cleaned.split(/\s+/).filter((w) => w.length > 0));

    let posCount = 0;
    let negCount = 0;
    for (const w of words) {
      if (POSITIVE_WORDS.has(w)) posCount++;
      if (NEGATIVE_WORDS.has(w)) negCount++;
    }

    const total = posCount + negCount;
    let compound = total === 0 ? 0.0 : (posCount - negCount) / (total + 2); // Damped
    compound = Math.max(-1.0, Math.min(1.0, compound));
    const negRatio = negCount / Math.max(total, 1);

    return {
      compound,
      positive: posCount / Math.max(total, 1),
      negative: negRatio,
      neutral: 1.0 - Math.abs(compound),
      textSnippet: snippet,
    };
  }

  private classifyTrend(current: number, polarityDrop: number): SentimentTrend {
    // Note: the window already contains the current reading at this point,
    // matching the Python ordering (append before classify).
    if (this.window.length < 2) {
      return current < -0.3 ? 'declining' : 'stable';
    }
    if (polarityDrop <= SentimentLayer.SHARP_DECLINE_THRESHOLD) {
      return 'sharply_declining';
    }
    if (polarityDrop <= SentimentLayer.DECLINE_THRESHOLD) {
      return 'declining';
    }
    if (polarityDrop >= 0.15) {
      return 'recovering';
    }
    return 'stable';
  }

  private computeConfidence(reading: SentimentReading, trend: SentimentTrend): number {
    let confidence = 0.0;

    // Base from current compound score (very negative = high confidence).
    if (reading.compound < -0.6) {
      confidence += 0.3;
    } else if (reading.compound < -0.3) {
      confidence += 0.15;
    } else if (reading.compound < 0.0) {
      confidence += 0.05;
    }

    // Bonus for sharp or sustained decline.
    if (trend === 'sharply_declining') {
      confidence += 0.2;
    } else if (trend === 'declining') {
      confidence += 0.1;
    }

    return Math.min(1.0, confidence);
  }

  /** Reset the sliding window (e.g., after a session break). */
  resetWindow(): void {
    this.window.length = 0;
  }

  getWindowSummary(): {
    windowSize: number;
    readingsCount: number;
    average: number;
    trend: number;
  } {
    const values = this.window;
    return {
      windowSize: this.windowSize,
      readingsCount: values.length,
      average: values.length > 0 ? values.reduce((a, b) => a + b, 0) / values.length : 0.0,
      trend: values.length >= 2 ? values[values.length - 1] - values[0] : 0.0,
    };
  }
}
