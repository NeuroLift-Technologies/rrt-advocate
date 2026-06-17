/**
 * CDE Layer 1: Keyword / Semantic Field Analysis.
 *
 * Local-first — pure pattern matching, no external API.
 *
 * Faithful TypeScript port of `src/crisis/detectors/keyword_layer.py`.
 * Maintains libraries of semantically related phrases organized into
 * neurodivergent-specific distress categories, and detects the presence
 * of these semantic fields in user messages with confidence scoring.
 *
 * Design notes (preserved from the Python source):
 * - Patterns use case-insensitive regex.
 * - The SELF_HARM_RISK field always forces maximum confidence (1.0).
 * - Multiple field activations compound the confidence score (capped at 1.0).
 */

import {
  KeywordSemanticField,
  type KeywordAnalysisResult,
  type KeywordMatch,
} from './types.js';

// ============================================================================
// Semantic Field Libraries
// Anti-Gaslight design: patterns detect distress signals without
// pathologizing normal human language. Patterns and ordering are preserved
// verbatim from the Python source.
// ============================================================================

const FIELD_PATTERNS: ReadonlyArray<readonly [KeywordSemanticField, readonly string[]]> = [
  [
    KeywordSemanticField.NEGATIVE_SELF_TALK,
    [
      'i hate myself',
      "i('m| am) (so |really )?(worthless|useless|stupid|pathetic|awful|terrible|broken)",
      "i('m| am) a failure",
      'i always (mess|screw|f+uck) (up|everything)',
      "i('m| am) the worst",
      'i ruin everything',
      '(nobody|no one) cares (about me|anymore)?',
      "i (can't|cannot) do anything right",
      'why am i (so |like this|like that)',
      "i don't deserve",
      "i('m| am) so (dumb|stupid|bad)",
      "everything('s| is) my fault",
      "i('m| am) not good enough",
      "i('ve| have) ruined (it|everything|this)",
    ],
  ],
  [
    KeywordSemanticField.TASK_AVOIDANCE,
    [
      "(can'?t|cannot) start",
      "(can'?t|cannot) (do|finish|begin|complete|get started)",
      "don'?t know (how to |where to )?begin",
      "(can'?t|cannot) make myself",
      "(i'?ve? been|been) (procrastin|putting it off|avoiding)",
      '(too hard|too difficult|too much)',
      '(giving up|give up|gave up)',
      "what'?s the point",
      "can'?t (be|get) (motivated|started|going)",
      '(paralyzed|paralysed)',
      '(stuck|frozen) (on|with|at)',
    ],
  ],
  [
    KeywordSemanticField.OVERWHELM,
    [
      'too much (going on|happening|at once)',
      "(can'?t|cannot) cope",
      "(can'?t|cannot) handle (this|it|everything|anymore)",
      '(drowning|overwhelm(ed|ing))',
      'everything (is |feels )?(too much|overwhelming|impossible)',
      '(spinning|spiraling|spiral(l)?ing)',
      "(can'?t|cannot) breathe",
      '(shutting down|shutdown|shut(ting)? down)',
      'brain (is |feels )?(fried|overloaded|full|done)',
      '(so many|too many) (things|tasks|thoughts)',
      "(can'?t|cannot) think (straight|clearly)",
    ],
  ],
  [
    KeywordSemanticField.MELTDOWN,
    [
      '(melt(ing|ed|down)|meltdown)',
      '(fall(ing|en) apart|falling to pieces)',
      '(break(ing|down)|breakdown)',
      "(can'?t|cannot) stop (crying|shaking|panicking)",
      '(losing|lost) (it|control|my mind)',
      '(freaking|flipping|losing) out',
      "everything'?s (falling|crumbling|coming) apart",
      '(complete|total|full) (meltdown|breakdown|collapse)',
    ],
  ],
  [
    KeywordSemanticField.SHUTDOWN,
    [
      '(shut(ting)? down|shutdown)',
      '(completely |totally )?(blank|empty|numb|gone|void)',
      "(can'?t|cannot) (feel|think|move|respond)",
      '(dissociat(ing|ed)|dissociation)',
      '(frozen|froze(n)?|freezing)',
      '(checked out|checked off|not (here|present|real))',
      '(going |feel(ing)? )(numb|blank|empty)',
      "(words|thoughts) (won'?t|don'?t) come",
      "(can'?t|cannot) find (words|the words)",
      '(just|totally|completely) (done|gone|empty|blank)',
    ],
  ],
  [
    KeywordSemanticField.HYPERFOCUS_LOOP,
    [
      "(can'?t|cannot) stop (thinking|going back|focusing)",
      '(stuck|looping) (in|on) (a loop|it|this)',
      '(keep|keep on|keeps) (thinking|going back|looping|fixating)',
      '(hyperfocus(ing|ed)?|hyperfixat(ing|ion|ed))',
      '(rabbit hole|down a rabbit)',
      '(obsess(ing|ed|ion)|obsessive)',
      "(can'?t|cannot) (let it go|move on|stop|switch off)",
      '(loop(ing|ed)?|spiral(l)?ing) (back|on|about)',
      '(intrusive|unwanted) (thought|loop|fixation)',
    ],
  ],
  [
    KeywordSemanticField.SELF_HARM_RISK,
    [
      '(want to |going to |going to )(hurt|harm) (myself|me)',
      '(self[- ]?harm|self[- ]?hurt|self[- ]?injur)',
      "don'?t want to (be here|live|exist|continue)",
      '(better off|world (is|would be) better) (without me|if i (was|were) gone)',
      '(thinking about|thought about) (ending|stopping) (it|everything|my life)',
      '(suicid(e|al|ity)|want to die)',
      '(kill|end) myself',
    ],
  ],
];

// ============================================================================
// INTENTIONAL DIVERGENCE FROM THE PYTHON SOURCE — apostrophe fail-open.
// ----------------------------------------------------------------------------
// The Python patterns require literal apostrophes in places (e.g. `i (can't|
// cannot)`, `i('m| am)`, `i don't deserve`, `everything('s| is)`). Voice-
// dictated / smart-quote text ("cant", "dont", "wont", "im", "youre",
// "everythings") would silently MISS those patterns. Because this is the
// 0.45-weighted Layer 1, a miss here is the worst case for the whole CDE.
//
// So — unlike every other formula/threshold/weight in this port, which is a
// faithful 1:1 of the Python — the matcher here is deliberately made
// apostrophe-insensitive: apostrophes are stripped from BOTH the input text
// and the compiled patterns, so "can't" and "cant" match identically. This is
// the same fail-open behaviour adopted in nlt-sdl. See KNOWN_LIMITATIONS.md.
// ============================================================================

/** ASCII apostrophe, right single quote (U+2019), modifier letter apostrophe (U+02BC). */
const APOSTROPHES = /['’ʼ]/g;

/** Strip apostrophes from input text so dictation/smart-quote forms match. */
function stripApostrophes(text: string): string {
  return text.replace(APOSTROPHES, '');
}

/**
 * Make a pattern source apostrophe-insensitive to match {@link stripApostrophes}
 * input. Removes the optional-apostrophe token `'?` first (so `can'?t` → `cant`,
 * not the broken `can?t`), then any remaining literal apostrophes (so `i('m|
 * am)` → `i(m| am)`).
 */
function normalizePattern(source: string): string {
  return source.replace(/'\?/g, '').replace(/'/g, '');
}

/** Confidence weights for each semantic field. */
const FIELD_CONFIDENCE_WEIGHTS: Record<KeywordSemanticField, number> = {
  [KeywordSemanticField.NEGATIVE_SELF_TALK]: 0.15,
  [KeywordSemanticField.TASK_AVOIDANCE]: 0.1,
  [KeywordSemanticField.OVERWHELM]: 0.15,
  [KeywordSemanticField.MELTDOWN]: 0.25,
  [KeywordSemanticField.SHUTDOWN]: 0.2,
  [KeywordSemanticField.HYPERFOCUS_LOOP]: 0.1,
  [KeywordSemanticField.SELF_HARM_RISK]: 1.0, // Always escalates to maximum
};

interface CompiledField {
  field: KeywordSemanticField;
  /** Parallel arrays: compiled regex and its original source string. */
  patterns: RegExp[];
  sources: string[];
}

export class KeywordLayer {
  private readonly compiled: CompiledField[];

  constructor() {
    this.compiled = FIELD_PATTERNS.map(([field, patterns]) => ({
      field,
      // Compile apostrophe-insensitive (see divergence note above)...
      patterns: patterns.map((p) => new RegExp(normalizePattern(p), 'i')),
      // ...but keep the original source string for human-readable reporting.
      sources: [...patterns],
    }));
  }

  /**
   * Analyze text for semantic field matches.
   *
   * @param text User message text to analyze.
   * @returns Detected fields, matches, and a compounded confidence score.
   */
  analyze(text: string): KeywordAnalysisResult {
    if (!text || !text.trim()) {
      return {
        detectedFields: [],
        matches: [],
        confidenceScore: 0.0,
        selfHarmDetected: false,
        primaryField: null,
      };
    }

    // Match against the apostrophe-stripped form (see divergence note above).
    // `matchedText`/`position` therefore index into the normalized haystack.
    const haystack = stripApostrophes(text);

    const detectedFields: KeywordSemanticField[] = [];
    const allMatches: KeywordMatch[] = [];
    const fieldMatchCounts = new Map<KeywordSemanticField, number>();

    for (const { field, patterns, sources } of this.compiled) {
      const matchesForField: KeywordMatch[] = [];
      for (let i = 0; i < patterns.length; i++) {
        const match = patterns[i].exec(haystack);
        if (match) {
          matchesForField.push({
            field,
            pattern: sources[i],
            matchedText: match[0],
            position: match.index,
          });
        }
      }
      if (matchesForField.length > 0) {
        detectedFields.push(field);
        fieldMatchCounts.set(field, matchesForField.length);
        allMatches.push(...matchesForField);
      }
    }

    const confidence = this.computeConfidence(detectedFields, fieldMatchCounts);
    const selfHarm = detectedFields.includes(KeywordSemanticField.SELF_HARM_RISK);

    // Primary field = highest (weight * match count).
    let primary: KeywordSemanticField | null = null;
    if (detectedFields.length > 0) {
      primary = detectedFields.reduce((best, f) => {
        const score = (FIELD_CONFIDENCE_WEIGHTS[f] ?? 0.0) * (fieldMatchCounts.get(f) ?? 1);
        const bestScore =
          (FIELD_CONFIDENCE_WEIGHTS[best] ?? 0.0) * (fieldMatchCounts.get(best) ?? 1);
        return score > bestScore ? f : best;
      }, detectedFields[0]);
    }

    return {
      detectedFields,
      matches: allMatches,
      confidenceScore: confidence,
      selfHarmDetected: selfHarm,
      primaryField: primary,
    };
  }

  /**
   * Compute overall confidence from detected fields.
   *
   * Self-harm detection always returns 1.0. Otherwise, compounds field
   * weights with a small diminishing bonus for repeated matches.
   */
  private computeConfidence(
    detectedFields: KeywordSemanticField[],
    fieldMatchCounts: Map<KeywordSemanticField, number>,
  ): number {
    if (detectedFields.includes(KeywordSemanticField.SELF_HARM_RISK)) {
      return 1.0;
    }
    if (detectedFields.length === 0) {
      return 0.0;
    }

    let total = 0.0;
    for (const f of detectedFields) {
      const weight = FIELD_CONFIDENCE_WEIGHTS[f] ?? 0.1;
      const countBonus = Math.min(0.05 * ((fieldMatchCounts.get(f) ?? 1) - 1), 0.1);
      total += weight + countBonus;
    }
    return Math.min(1.0, total);
  }
}
