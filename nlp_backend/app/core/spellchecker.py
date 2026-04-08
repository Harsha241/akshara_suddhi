"""
Spell Checker
==============
Combines Levenshtein distance, phonetic similarity, and N-gram context
to produce ranked spelling suggestions.

Ranking formula
---------------
base_score = FREQ_W × norm_freq + PHONETIC_W × phonetic_sim + LENGTH_PENALTY
final_score = base_score + NGRAM_W × ngram_boost   (when context available)
"""

from typing import Dict, List, Optional

from app.config import (
    FREQ_WEIGHT,
    MAX_EDIT_DISTANCE,
    PHONETIC_WEIGHT,
    TOP_SPELL_SUGGESTIONS,
)
from app.core.levenshtein import generate_candidates
from app.core.ngram import NgramModel
from app.core.phonetic import phonetic_similarity
from app.models import SpellCheckResponse, SpellSuggestion


# ── Telugu morphological suffixes (postpositions + verb endings) ──────────
# Ordered longest-first so we strip the most specific suffix first.
_SUFFIXES = [
    # Postpositions / case markers
    "లోకి", "నుండి", "వైపు", "కోసం", "వరకు", "తోపాటు",
    "లో", "కి", "కు", "తో", "పై", "కింద", "వద్ద", "దగ్గర",
    "మీద", "గురించి", "వల్ల", "ద్వారా", "మధ్య", "లోపల",
    # Verb endings (past / present / future)
    "స్తున్నాడు", "స్తున్నది", "స్తున్నారు", "స్తున్నాను", "స్తున్నావు",
    "తున్నాడు", "తున్నది", "తున్నారు", "తున్నాను",
    "తున్నావు",
    "స్తాడు", "స్తుంది", "స్తారు", "స్తాను", "స్తావు",
    "తాడు", "తుంది", "తారు", "తాను", "తావు",
    "సాడు", "సింది", "సారు", "సాను", "సావు", "సాము",
    "చాడు", "చింది", "చారు", "చాను",
    "ాడు", "ింది", "ారు", "ాను", "ావు", "ాము",
    # Plural / other noun suffixes
    "లు", "ని", "ను",
]

# Common wrong→right phonetic substitutions seen in Telugu typing
_COMMON_TYPOS: Dict[str, str] = {
    # Short/long vowel confusions
    "అ": "ఆ", "ఆ": "అ", "ఇ": "ఈ", "ఈ": "ఇ",
    "ఉ": "ఊ", "ఊ": "ఉ", "ఎ": "ఏ", "ఏ": "ఎ",
    "ఒ": "ఓ", "ఓ": "ఒ",
}


class SpellChecker:
    """
    Stateful spell-checker initialised with a dictionary and N-gram model.

    Parameters
    ----------
    dictionary : {word: frequency}
    ngram_model : NgramModel instance
    """

    def __init__(
        self,
        dictionary: Dict[str, int],
        ngram_model: NgramModel,
    ):
        self.dictionary = dictionary
        self.ngram = ngram_model
        self._max_freq = max(dictionary.values()) if dictionary else 1
        # Build a lower-case index for fuzzy lookup (Telugu is case-insensitive)
        self._dict_list = list(dictionary.keys())

    # ── Public API ───────────────────────────────────────────────────────

    def check(
        self,
        word: str,
        context: Optional[List[str]] = None,
    ) -> SpellCheckResponse:
        """
        Check a single word. Returns structured response with suggestions.
        """
        # 1. Exact match → correct
        if word in self.dictionary:
            return SpellCheckResponse(
                original=word, is_correct=True, suggestions=[]
            )

        # 2. Morphological decomposition: strip suffix, check stem
        stem = self._strip_suffix(word)
        if stem and stem in self.dictionary:
            return SpellCheckResponse(
                original=word, is_correct=True, suggestions=[]
            )

        # 3. If the word is very short (≤2 grapheme clusters), be lenient
        from app.core.unicode_utils import split_grapheme_clusters
        clusters = split_grapheme_clusters(word)
        if len(clusters) <= 2:
            return SpellCheckResponse(
                original=word, is_correct=True, suggestions=[]
            )

        # 4. Generate candidates within edit distance
        raw = generate_candidates(word, self.dictionary, MAX_EDIT_DISTANCE)

        # 5. If no candidates at edit-distance 2, try edit-distance 3 for long words
        if not raw and len(clusters) >= 5:
            raw = generate_candidates(word, self.dictionary, 3.0)

        # 6. Preceding word for bigram context
        preceding = context[-1] if context else None

        # 7. Score and rank
        scored = self._score_candidates(word, raw, preceding)

        # 8. Prefer candidates whose length is close to the input
        # (penalise very different lengths)
        word_len = len(clusters)

        # Sort by combined score descending, take top N
        scored.sort(key=lambda s: -s.score)
        top = scored[:TOP_SPELL_SUGGESTIONS]

        return SpellCheckResponse(
            original=word,
            is_correct=False,
            suggestions=top,
        )

    # ── Internal helpers ─────────────────────────────────────────────────

    def _strip_suffix(self, word: str) -> Optional[str]:
        """
        Try stripping known Telugu suffixes and return the stem if non-empty.
        Returns None if no suffix matched or stem is too short.
        """
        for suf in _SUFFIXES:
            if word.endswith(suf):
                stem = word[: -len(suf)]
                if len(stem) >= 2:  # stem must be at least 2 chars
                    return stem
        return None

    def _score_candidates(
        self,
        word: str,
        raw: List[tuple],
        preceding: Optional[str],
    ) -> List[SpellSuggestion]:
        from app.core.unicode_utils import split_grapheme_clusters
        word_len = len(split_grapheme_clusters(word))
        scored = []

        for candidate, dist, freq in raw:
            cand_len = len(split_grapheme_clusters(candidate))
            norm_freq  = freq / self._max_freq
            phon_sim   = phonetic_similarity(word, candidate)

            # Edit-distance weight: distance-1 gets full score, distance-2 penalised
            dist_weight = 1.0 if dist <= 1.0 else (0.7 if dist <= 2.0 else 0.4)

            # Length similarity bonus: reward candidates close in length
            len_diff   = abs(cand_len - word_len)
            len_bonus  = max(0.0, 0.15 - 0.05 * len_diff)

            base = (
                FREQ_WEIGHT    * norm_freq
                + PHONETIC_WEIGHT * phon_sim * dist_weight
                + len_bonus
            )

            # Bigram context boost (weighted higher now)
            if preceding:
                bp   = self.ngram.bigram_prob(preceding, candidate)
                base += 0.35 * bp

            # Extra boost for edit-distance-1 matches
            if dist <= 1.0:
                base += 0.10

            scored.append(
                SpellSuggestion(
                    word=candidate,
                    score=round(base, 4),
                    frequency=freq,
                    edit_distance=dist,
                )
            )

        return scored