/**
 * Crisis Assessor.
 *
 * Faithful TypeScript port of `src/crisis/assessors/crisis_assessor.py`.
 * Maps {@link CrisisIndicators} from the 3-layer CDE to a specific
 * {@link CrisisLevel}, applying the thresholds from `crisis_thresholds.yaml`
 * to produce a final {@link CrisisAssessment}.
 */

import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import yaml from 'js-yaml';
import { type CrisisIndicators } from './crisisDetector.js';
import { CrisisLevel, type CrisisAssessment } from './types.js';

/** Lowercase config key for each crisis level (matches Python `level.name.lower()`). */
const LEVEL_KEY: Record<CrisisLevel, string> = {
  [CrisisLevel.GREEN]: 'green',
  [CrisisLevel.YELLOW]: 'yellow',
  [CrisisLevel.ORANGE]: 'orange',
  [CrisisLevel.RED]: 'red',
  [CrisisLevel.BLACK]: 'black',
};

// Aggregate confidence → crisis level thresholds: [low, high, level].
const LEVEL_THRESHOLDS: ReadonlyArray<readonly [number, number, CrisisLevel]> = [
  [0.0, 0.2, CrisisLevel.GREEN],
  [0.2, 0.4, CrisisLevel.YELLOW],
  [0.4, 0.7, CrisisLevel.ORANGE],
  [0.7, 0.9, CrisisLevel.RED],
  [0.9, 1.01, CrisisLevel.BLACK],
];

const DEFAULT_INTERVENTIONS: Record<CrisisLevel, string[]> = {
  [CrisisLevel.GREEN]: [],
  [CrisisLevel.YELLOW]: ['breathing_exercise', 'grounding_technique'],
  [CrisisLevel.ORANGE]: ['guided_meditation', 'cognitive_restructuring'],
  [CrisisLevel.RED]: ['intensive_grounding', 'crisis_counseling'],
  [CrisisLevel.BLACK]: ['emergency_stabilization', 'crisis_hotline'],
};

const ESCALATION_THRESHOLDS: Record<CrisisLevel, number> = {
  [CrisisLevel.GREEN]: 0.4,
  [CrisisLevel.YELLOW]: 0.6,
  [CrisisLevel.ORANGE]: 0.75,
  [CrisisLevel.RED]: 0.9,
  [CrisisLevel.BLACK]: 1.0,
};

interface ThresholdConfig {
  intervention_mapping?: Record<string, { recommended_interventions?: string[] }>;
  [key: string]: unknown;
}

/** Resolve the bundled `config/crisis_thresholds.yaml` shipped with the package. */
function defaultConfigPath(): string {
  return fileURLToPath(new URL('../config/crisis_thresholds.yaml', import.meta.url));
}

export class CrisisAssessor {
  readonly userId: string;
  private readonly config: ThresholdConfig;

  /**
   * @param userId Stable, pseudonymous user identifier (used only for logging
   *   context; no content is persisted).
   * @param configPath Path to a `crisis_thresholds.yaml`. Defaults to the
   *   copy bundled with this package.
   */
  constructor(userId: string, configPath: string = defaultConfigPath()) {
    this.userId = userId;
    this.config = CrisisAssessor.loadConfig(configPath);
  }

  private static loadConfig(path: string): ThresholdConfig {
    try {
      const raw = readFileSync(path, 'utf-8');
      return (yaml.load(raw) as ThresholdConfig) ?? {};
    } catch (error) {
      // Safety-critical: never run silently on a missing/unreadable thresholds
      // file. Mirror the Python source, which logs a warning, so operators know
      // the assessor fell back to built-in default interventions.
      console.warn(
        `[rrt-advocate] Could not load crisis thresholds from "${path}"; ` +
          `falling back to built-in default interventions. ` +
          `${error instanceof Error ? error.message : String(error)}`,
      );
      return {};
    }
  }

  /** Produce a CrisisAssessment from CrisisIndicators. */
  async assessCrisis(indicators: CrisisIndicators): Promise<CrisisAssessment> {
    const confidence = indicators.aggregateConfidence;
    let level = this.mapConfidenceToLevel(confidence);

    // Self-harm always escalates to BLACK.
    if (indicators.selfHarmRisk) {
      level = CrisisLevel.BLACK;
    }

    const safetyScore = this.computeSafetyScore(indicators);
    const interventions = this.getRecommendedInterventions(level);
    const primary = indicators.getPrimaryIndicators();

    return {
      timestamp: indicators.timestamp,
      crisisLevel: level,
      primaryIndicators: primary,
      secondaryIndicators: indicators.detectedSemanticFields,
      confidenceScore: confidence,
      estimatedDuration: null,
      recommendedInterventions: interventions,
      escalationThreshold: this.getEscalationThreshold(level),
      userSafetyScore: safetyScore,
      contextFactors: {
        self_harm_risk: indicators.selfHarmRisk,
        sentiment_trend: indicators.sentimentTrend,
        looping_detected: indicators.loopingDetected,
        behavioral_complexity: indicators.behavioralComplexity,
        layer_scores: {
          keyword: indicators.layer1Confidence,
          sentiment: indicators.layer2Confidence,
          behavioral: indicators.layer3Confidence,
        },
      },
    };
  }

  private mapConfidenceToLevel(confidence: number): CrisisLevel {
    for (const [low, high, level] of LEVEL_THRESHOLDS) {
      if (low <= confidence && confidence < high) {
        return level;
      }
    }
    return CrisisLevel.BLACK;
  }

  /**
   * Compute a user safety score (1.0 = fully safe, 0.0 = immediate danger).
   * Inversely related to aggregate confidence, with extra penalties for
   * self-harm risk and behavioral shutdown signals.
   */
  private computeSafetyScore(indicators: CrisisIndicators): number {
    if (indicators.selfHarmRisk) {
      return 0.05;
    }
    let base = 1.0 - indicators.aggregateConfidence;
    if (indicators.loopingDetected) {
      base -= 0.1;
    }
    if (indicators.behavioralComplexity < 0.1) {
      base -= 0.15; // Shutdown signal
    }
    if (indicators.sentimentTrend === 'sharply_declining') {
      base -= 0.1;
    }
    return Math.max(0.05, Math.min(1.0, base));
  }

  private getRecommendedInterventions(level: CrisisLevel): string[] {
    const mapping = this.config.intervention_mapping ?? {};
    const levelKey = LEVEL_KEY[level];
    const entry = mapping[levelKey];
    if (entry) {
      return entry.recommended_interventions ?? [];
    }
    return DEFAULT_INTERVENTIONS[level];
  }

  private getEscalationThreshold(level: CrisisLevel): number {
    return ESCALATION_THRESHOLDS[level] ?? 0.8;
  }
}
