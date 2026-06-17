import { describe, expect, it } from 'vitest';
import { BehavioralLayer } from '../src/behavioralLayer.js';

describe('BehavioralLayer', () => {
  it('returns a zeroed result for blank input', () => {
    const r = new BehavioralLayer().analyze('   ');
    expect(r.messageComplexity).toBe(0);
    expect(r.loopingDetected).toBe(false);
    expect(r.responseLatency).toBeNull();
    expect(r.metrics.wordCount).toBe(0);
  });

  it('computes a normalized complexity score', () => {
    // 15 words, one sentence → word_score=0.5, sentence_score=1.0 → 0.7
    const text =
      'alpha bravo charlie delta echo foxtrot golf hotel india juliet kilo lima mike november oscar';
    const r = new BehavioralLayer().analyze(text);
    expect(r.metrics.wordCount).toBe(15);
    expect(r.messageComplexity).toBeCloseTo(0.7, 5);
    expect(r.complexityTrend).toBe('normal');
  });

  it('detects looping on a repeated message', () => {
    const layer = new BehavioralLayer();
    const text = 'thinking about the same worry again and again right now';
    const first = layer.analyze(text);
    expect(first.loopingDetected).toBe(false);
    const second = layer.analyze(text);
    expect(second.loopingSimilarity).toBeCloseTo(1.0, 5);
    expect(second.loopingDetected).toBe(true);
    expect(second.confidenceScore).toBeCloseTo(0.2, 5);
  });

  it('detects a fragmenting complexity trend', () => {
    const layer = new BehavioralLayer();
    layer.analyze('alpha bravo charlie delta echo foxtrot golf hotel india juliet kilo lima mike november oscar');
    layer.analyze('uniform victor whiskey xray yankee zulu');
    const r = layer.analyze('done finished');
    expect(r.complexityTrend).toBe('fragmenting');
  });

  it('resets session state', () => {
    const layer = new BehavioralLayer();
    layer.analyze('thinking about the same worry again and again right now');
    layer.reset();
    const r = layer.analyze('thinking about the same worry again and again right now');
    expect(r.loopingDetected).toBe(false);
  });
});
