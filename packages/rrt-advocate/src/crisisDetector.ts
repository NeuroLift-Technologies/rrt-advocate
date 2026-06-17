/**
 * Crisis Detector — 3-Layer Unified Pipeline.
 *
 * Faithful TypeScript port of `src/crisis/detectors/crisis_detector.py`.
 * Orchestrates all three CDE layers and aggregates their outputs into a
 * unified {@link CrisisIndicators} object for the CrisisAssessor.
 *
 * Local-first design: all three layers run on-device.
 *
 *   Layer 1 (keyword)    weight: 0.45
 *   Layer 2 (sentiment)  weight: 0.35
 *   Layer 3 (behavioral) weight: 0.20
 */

import { BehavioralLayer } from './behavioralLayer.js';
import { KeywordLayer } from './keywordLayer.js';
import { type PolarityAnalyzer, SentimentLayer } from './sentimentLayer.js';
import {
  KeywordSemanticField,
  type BehavioralAnalysisResult,
  type KeywordAnalysisResult,
  type SentimentAnalysisResult,
  type SentimentTrend,
} from './types.js';

const LAYER_WEIGHTS = { layer1: 0.45, layer2: 0.35, layer3: 0.2 } as const;

/**
 * Aggregated output from all three CDE layers, passed to the CrisisAssessor
 * for final crisis level determination.
 */
export class CrisisIndicators {
  timestamp: Date;
  rawText: string;

  keywordResult: KeywordAnalysisResult | null = null;
  sentimentResult: SentimentAnalysisResult | null = null;
  behavioralResult: BehavioralAnalysisResult | null = null;

  selfHarmRisk = false;
  detectedSemanticFields: string[] = [];
  sentimentTrend: SentimentTrend = 'stable';
  loopingDetected = false;
  behavioralComplexity = 1.0;

  layer1Confidence = 0.0;
  layer2Confidence = 0.0;
  layer3Confidence = 0.0;
  aggregateConfidence = 0.0;

  constructor(timestamp: Date, rawText: string) {
    this.timestamp = timestamp;
    this.rawText = rawText;
  }

  /** Recompute aggregateConfidence from layer scores and weights. */
  computeAggregate(): void {
    if (this.selfHarmRisk) {
      this.aggregateConfidence = 1.0;
      return;
    }
    this.aggregateConfidence = Math.min(
      1.0,
      this.layer1Confidence * LAYER_WEIGHTS.layer1 +
        this.layer2Confidence * LAYER_WEIGHTS.layer2 +
        this.layer3Confidence * LAYER_WEIGHTS.layer3,
    );
  }

  /** Return a human-readable list of the primary detected indicators. */
  getPrimaryIndicators(): string[] {
    const indicators: string[] = [];
    if (this.selfHarmRisk) {
      indicators.push('SELF_HARM_RISK');
    }
    indicators.push(...this.detectedSemanticFields);
    if (this.sentimentTrend === 'declining' || this.sentimentTrend === 'sharply_declining') {
      indicators.push(`sentiment_trend:${this.sentimentTrend}`);
    }
    if (this.loopingDetected) {
      indicators.push('behavioral_looping');
    }
    if (this.behavioralComplexity < 0.15) {
      indicators.push('behavioral_shutdown_signal');
    }
    return indicators;
  }
}

export class CrisisDetector {
  private readonly keywordLayer: KeywordLayer;
  private readonly sentimentLayer: SentimentLayer;
  private readonly behavioralLayer: BehavioralLayer;

  /**
   * @param options.sentimentAnalyzer Optional VADER-compatible analyzer for
   *   Layer 2. When omitted, Layer 2 auto-detects `vader-sentiment` and
   *   otherwise uses its built-in heuristic fallback.
   */
  constructor(options: { sentimentAnalyzer?: PolarityAnalyzer | null } = {}) {
    this.keywordLayer = new KeywordLayer();
    this.sentimentLayer = new SentimentLayer(5, options.sentimentAnalyzer);
    this.behavioralLayer = new BehavioralLayer(5);
  }

  /**
   * Run the full 3-layer analysis on a user message.
   *
   * @param message User message text.
   * @param timestamp Message timestamp (defaults to now).
   * @returns CrisisIndicators aggregated from all layers.
   */
  async detectCrisisIndicators(message = '', timestamp?: Date): Promise<CrisisIndicators> {
    const ts = timestamp ?? new Date();

    const keywordResult = this.keywordLayer.analyze(message);
    const sentimentResult = this.sentimentLayer.analyze(message);
    const behavioralResult = this.behavioralLayer.analyze(message);

    const indicators = new CrisisIndicators(ts, message);
    indicators.keywordResult = keywordResult;
    indicators.sentimentResult = sentimentResult;
    indicators.behavioralResult = behavioralResult;
    indicators.selfHarmRisk = keywordResult.selfHarmDetected;
    indicators.detectedSemanticFields = keywordResult.detectedFields.map(
      (f) => f as KeywordSemanticField as string,
    );
    indicators.sentimentTrend = sentimentResult.trend;
    indicators.loopingDetected = behavioralResult.loopingDetected;
    indicators.behavioralComplexity = behavioralResult.messageComplexity;
    indicators.layer1Confidence = keywordResult.confidenceScore;
    indicators.layer2Confidence = sentimentResult.confidenceScore;
    indicators.layer3Confidence = behavioralResult.confidenceScore;

    indicators.computeAggregate();
    return indicators;
  }

  /** Reset all layer state for a new session. */
  resetSession(): void {
    this.sentimentLayer.resetWindow();
    this.behavioralLayer.reset();
  }
}
