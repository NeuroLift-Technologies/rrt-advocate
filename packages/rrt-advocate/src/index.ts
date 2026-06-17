/**
 * `@neurolift-technologies/rrt-advocate` — TypeScript port of the RRT Advocate
 * **Crisis Detection Engine (CDE)**: a 3-layer, local-first crisis detection
 * and assessment pipeline from the NeuroLift HAIEF Solidarity Framework.
 *
 * This package is a faithful port of the Python CDE (`src/crisis/` in the
 * `rrt-advocate` repository). It preserves every layer weight, threshold, and
 * confidence formula from the canonical Python source. **Crisis thresholds are
 * safety-critical** — the bundled `config/crisis_thresholds.yaml` is a vendored
 * copy of the canonical file and must stay in sync with it.
 *
 * Scope: this package ports the **detection & assessment engine** only. The
 * persona/dialogue/intervention *response* layers remain Python-canonical.
 *
 * @example
 * ```ts
 * import { CrisisEngine, CrisisLevel } from "@neurolift-technologies/rrt-advocate";
 *
 * const engine = new CrisisEngine("user-123");
 * const assessment = await engine.assess("I can't cope, everything is too much");
 * if (assessment.crisisLevel !== CrisisLevel.GREEN) {
 *   // route to appropriate support
 * }
 * ```
 */

import { CrisisAssessor } from './crisisAssessor.js';
import { CrisisDetector, type CrisisIndicators } from './crisisDetector.js';
import { type PolarityAnalyzer } from './sentimentLayer.js';
import { type CrisisAssessment } from './types.js';

// Layers and pipeline.
export { KeywordLayer } from './keywordLayer.js';
export { SentimentLayer, type PolarityAnalyzer } from './sentimentLayer.js';
export { BehavioralLayer } from './behavioralLayer.js';
export { CrisisDetector, CrisisIndicators } from './crisisDetector.js';
export { CrisisAssessor } from './crisisAssessor.js';

// Types and enums.
export {
  KeywordSemanticField,
  CrisisLevel,
  type KeywordMatch,
  type KeywordAnalysisResult,
  type SentimentReading,
  type SentimentTrend,
  type SentimentAnalysisResult,
  type ComplexityTrend,
  type BehavioralAnalysisResult,
  type CrisisAssessment,
} from './types.js';

export interface CrisisEngineOptions {
  /** Path to a `crisis_thresholds.yaml`. Defaults to the bundled copy. */
  configPath?: string;
  /**
   * Optional VADER-compatible analyzer for Layer 2. When omitted, Layer 2
   * auto-detects `vader-sentiment` and otherwise uses its heuristic fallback.
   */
  sentimentAnalyzer?: PolarityAnalyzer | null;
}

/**
 * Convenience facade that wires the {@link CrisisDetector} and
 * {@link CrisisAssessor} together, mirroring the Python
 * `RRTAdvocate.assess_current_state` path: detect indicators, then assess.
 *
 * This is the detection/assessment surface only — it does not generate
 * persona-blended responses or interventions.
 */
export class CrisisEngine {
  private readonly detector: CrisisDetector;
  private readonly assessor: CrisisAssessor;

  constructor(userId: string, options: CrisisEngineOptions = {}) {
    this.detector = new CrisisDetector({ sentimentAnalyzer: options.sentimentAnalyzer });
    this.assessor = new CrisisAssessor(userId, options.configPath);
  }

  /** Run the full 3-layer detection on a message and return raw indicators. */
  detect(message = '', timestamp?: Date): Promise<CrisisIndicators> {
    return this.detector.detectCrisisIndicators(message, timestamp);
  }

  /** Detect and assess a single message, returning a {@link CrisisAssessment}. */
  async assess(message = '', timestamp?: Date): Promise<CrisisAssessment> {
    const indicators = await this.detector.detectCrisisIndicators(message, timestamp);
    return this.assessor.assessCrisis(indicators);
  }

  /** Reset per-session detector state (sentiment window + behavioral history). */
  resetSession(): void {
    this.detector.resetSession();
  }
}
