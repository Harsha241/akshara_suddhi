"""
Spell Checker
==============
Combines Levenshtein distance, phonetic similarity, and N-gram context
to produce ranked spelling suggestions.

Ranking formula
---------------
base_score = FREQ_W × norm_freq + PHONETIC_W × phonetic_sim
final_score = base_score + 0.2 × ngram_boost   (when context available)
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


_COMMON_POSTPOS = ("కు", "కి", "లో", "లోకి")


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

    # ── Public API ───────────────────────────────────────────────────────

    def check(
        self,
        word: str,
        context: Optional[List[str]] = None,
    ) -> SpellCheckResponse:
        """
        Check a single word. Returns structured response with suggestions.
        """
        # Exact match → correct
        if word in self.dictionary:
            return SpellCheckResponse(
                original=word, is_correct=True, suggestions=[]
            )

        # Inflected word with common postposition suffix → treat as correct
        # when the stem exists in dictionary.
        for suf in _COMMON_POSTPOS:
            if word.endswith(suf) and len(word) > len(suf) + 1:
                stem = word[: -len(suf)]
                if stem in self.dictionary:
                    return SpellCheckResponse(
                        original=word, is_correct=True, suggestions=[]
                    )

        # Generate candidates within edit distance
        raw = generate_candidates(
            word, self.dictionary, MAX_EDIT_DISTANCE
        )

        # Determine preceding word for bigram context
        preceding = context[-1] if context else None

        # Score and rank
        scored = []
        for candidate, dist, freq in raw:
            norm_freq = freq / self._max_freq
            phon_sim  = phonetic_similarity(word, candidate)
            base      = FREQ_WEIGHT * norm_freq + PHONETIC_WEIGHT * phon_sim

            # Bigram boost
            if preceding:
                bp = self.ngram.bigram_prob(preceding, candidate)
                base += 0.2 * bp

            scored.append(
                SpellSuggestion(
                    word=candidate,
                    score=round(base, 4),
                    frequency=freq,
                    edit_distance=dist,
                )
            )

        # Sort by combined score descending, take top N
        scored.sort(key=lambda s: -s.score)
        top = scored[:TOP_SPELL_SUGGESTIONS]

        return SpellCheckResponse(
            original=word,
            is_correct=False,
            suggestions=top,
        )
