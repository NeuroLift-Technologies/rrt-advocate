import { describe, expect, it } from 'vitest';
import { SentimentLayer } from '../src/sentimentLayer.js';

// Force the deterministic heuristic fallback by passing `null` (no VADER).
const makeLayer = () => new SentimentLayer(5, null);

describe('SentimentLayer (heuristic fallback)', () => {
  it('scores clearly positive text as stable with no crisis confidence', () => {
    const r = makeLayer().analyze('i feel good and calm');
    expect(r.currentReading.compound).toBeCloseTo(0.5, 5);
    expect(r.trend).toBe('stable');
    expect(r.confidenceScore).toBe(0);
  });

  it('flags a negative first message as declining', () => {
    const r = makeLayer().analyze('i feel hopeless and broken');
    expect(r.currentReading.compound).toBeCloseTo(-0.5, 5);
    expect(r.trend).toBe('declining');
    expect(r.confidenceScore).toBeCloseTo(0.25, 5);
  });

  it('detects a sharp decline across the window', () => {
    const layer = makeLayer();
    layer.analyze('good great calm happy');
    const r = layer.analyze('hopeless worthless broken depressed awful');
    expect(r.currentReading.compound).toBeCloseTo(-0.7143, 3);
    expect(r.trend).toBe('sharply_declining');
    expect(r.confidenceScore).toBeCloseTo(0.5, 5);
  });

  it('detects recovery after a negative reading', () => {
    const layer = makeLayer();
    layer.analyze('hopeless broken');
    const r = layer.analyze('good great calm happy relieved');
    expect(r.trend).toBe('recovering');
    expect(r.confidenceScore).toBe(0);
  });

  it('resets the sliding window', () => {
    const layer = makeLayer();
    layer.analyze('hopeless broken');
    layer.resetWindow();
    expect(layer.getWindowSummary().readingsCount).toBe(0);
  });
});
