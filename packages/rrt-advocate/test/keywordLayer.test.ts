import { describe, expect, it } from 'vitest';
import { KeywordLayer } from '../src/keywordLayer.js';
import { KeywordSemanticField } from '../src/types.js';

describe('KeywordLayer', () => {
  const layer = new KeywordLayer();

  it('returns an empty result for blank input', () => {
    const r = layer.analyze('   ');
    expect(r.detectedFields).toEqual([]);
    expect(r.confidenceScore).toBe(0);
    expect(r.selfHarmDetected).toBe(false);
    expect(r.primaryField).toBeNull();
  });

  it('detects self-harm risk and forces confidence to 1.0', () => {
    const r = layer.analyze('honestly I want to kill myself');
    expect(r.selfHarmDetected).toBe(true);
    expect(r.detectedFields).toContain(KeywordSemanticField.SELF_HARM_RISK);
    expect(r.confidenceScore).toBe(1.0);
    expect(r.primaryField).toBe(KeywordSemanticField.SELF_HARM_RISK);
  });

  it('detects a single overwhelm field with its base weight', () => {
    const r = layer.analyze("I can't cope with this");
    expect(r.detectedFields).toContain(KeywordSemanticField.OVERWHELM);
    expect(r.selfHarmDetected).toBe(false);
    expect(r.confidenceScore).toBeCloseTo(0.15, 5);
  });

  it('detects negative self-talk', () => {
    const r = layer.analyze('i hate myself so much right now');
    expect(r.detectedFields).toContain(KeywordSemanticField.NEGATIVE_SELF_TALK);
    expect(r.confidenceScore).toBeCloseTo(0.15, 5);
  });

  it('compounds confidence across multiple distinct fields', () => {
    // OVERWHELM (0.15) + MELTDOWN (0.25) = 0.40 (no repeats → no count bonus)
    const r = layer.analyze("everything is falling apart and I can't cope");
    expect(r.detectedFields).toContain(KeywordSemanticField.MELTDOWN);
    expect(r.detectedFields).toContain(KeywordSemanticField.OVERWHELM);
    expect(r.confidenceScore).toBeCloseTo(0.4, 5);
  });

  it('fails open on apostrophe-free dictation input (intentional divergence)', () => {
    // "can't cope" dictated as "cant cope" must still fire OVERWHELM.
    expect(layer.analyze('i cant cope').detectedFields).toContain(
      KeywordSemanticField.OVERWHELM,
    );
    // "i don't deserve" dictated as "i dont deserve".
    expect(layer.analyze('i dont deserve this').detectedFields).toContain(
      KeywordSemanticField.NEGATIVE_SELF_TALK,
    );
    // "i'm not good enough" dictated as "im not good enough".
    expect(layer.analyze('im not good enough honestly').detectedFields).toContain(
      KeywordSemanticField.NEGATIVE_SELF_TALK,
    );
    // Smart-quote apostrophe (U+2019) must behave identically to ASCII.
    expect(layer.analyze('i can’t cope').detectedFields).toContain(
      KeywordSemanticField.OVERWHELM,
    );
  });

  it('caps compounded confidence at 1.0', () => {
    const r = layer.analyze(
      "i hate myself, everything is falling apart, i can't cope, i can't start, " +
        "i can't stop thinking about it, i feel completely numb",
    );
    expect(r.confidenceScore).toBeLessThanOrEqual(1.0);
  });
});
