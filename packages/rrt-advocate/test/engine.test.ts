import { describe, expect, it } from 'vitest';
import { CrisisDetector } from '../src/crisisDetector.js';
import { CrisisEngine, CrisisLevel } from '../src/index.js';

// Force the deterministic sentiment fallback for all engine tests.
const engine = () => new CrisisEngine('test-user', { sentimentAnalyzer: null });

describe('CrisisDetector aggregation', () => {
  it('weights layers 0.45 / 0.35 / 0.20 and self-consistently aggregates', async () => {
    const detector = new CrisisDetector({ sentimentAnalyzer: null });
    const ind = await detector.detectCrisisIndicators("everything is falling apart and I can't cope");
    expect(ind.selfHarmRisk).toBe(false);
    const expected = Math.min(
      1.0,
      ind.layer1Confidence * 0.45 + ind.layer2Confidence * 0.35 + ind.layer3Confidence * 0.2,
    );
    expect(ind.aggregateConfidence).toBeCloseTo(expected, 10);
  });

  it('forces aggregate confidence to 1.0 on self-harm risk', async () => {
    const detector = new CrisisDetector({ sentimentAnalyzer: null });
    const ind = await detector.detectCrisisIndicators('i want to kill myself');
    expect(ind.selfHarmRisk).toBe(true);
    expect(ind.aggregateConfidence).toBe(1.0);
    expect(ind.getPrimaryIndicators()).toContain('SELF_HARM_RISK');
  });

  it('surfaces a declining sentiment trend as a primary indicator', async () => {
    const detector = new CrisisDetector({ sentimentAnalyzer: null });
    const ind = await detector.detectCrisisIndicators('i feel hopeless and broken');
    expect(ind.getPrimaryIndicators()).toContain('sentiment_trend:declining');
  });
});

describe('CrisisEngine.assess', () => {
  it('rates a benign message GREEN with a high safety score', async () => {
    const a = await engine().assess('just checking in, all good here today');
    expect(a.crisisLevel).toBe(CrisisLevel.GREEN);
    expect(a.userSafetyScore).toBeCloseTo(1.0, 5);
    expect(a.confidenceScore).toBeLessThan(0.2);
  });

  it('escalates self-harm to BLACK with the bundled emergency interventions', async () => {
    const a = await engine().assess('i want to kill myself');
    expect(a.crisisLevel).toBe(CrisisLevel.BLACK);
    expect(a.userSafetyScore).toBeCloseTo(0.05, 5);
    expect(a.escalationThreshold).toBe(1.0);
    expect(a.primaryIndicators).toContain('SELF_HARM_RISK');
    // Proves the vendored crisis_thresholds.yaml was loaded.
    expect(a.recommendedInterventions).toEqual([
      'emergency_stabilization',
      'professional_contact',
      'crisis_hotline',
      'immediate_safety_measures',
    ]);
    expect(a.contextFactors.self_harm_risk).toBe(true);
  });

  it('resets per-session state without error', () => {
    const e = engine();
    expect(() => e.resetSession()).not.toThrow();
  });
});
