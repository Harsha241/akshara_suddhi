"""
N-gram Language Model
======================
Unigram + Bigram with Laplace smoothing.

P_laplace(w2 | w1) = (count(w1,w2) + α) / (count(w1) + α·V)

Used to contextually re-rank spell-check candidates.
"""

import math
from typing import Dict, Optional

from app.config import LAPLACE_ALPHA


class NgramModel:
    """
    Stores unigram and bigram counts loaded from JSON.

    Parameters
    ----------
    unigrams : {word: count}
    bigrams  : {word1: {word2: count}}
    """

    def __init__(
        self,
        unigrams: Dict[str, int],
        bigrams: Dict[str, Dict[str, int]],
    ):
        self.unigrams = unigrams
        self.bigrams = bigrams
        self.total_unigrams = sum(unigrams.values()) or 1
        self.vocab_size = len(unigrams) or 1

    # ── Probabilities ────────────────────────────────────────────────────

    def unigram_prob(self, word: str) -> float:
        """P(word) with Laplace smoothing."""
        count = self.unigrams.get(word, 0)
        return (count + LAPLACE_ALPHA) / (
            self.total_unigrams + LAPLACE_ALPHA * self.vocab_size
        )

    def bigram_prob(self, w1: str, w2: str) -> float:
        """P(w2 | w1) with Laplace smoothing."""
        w1_count = self.unigrams.get(w1, 0)
        pair_count = self.bigrams.get(w1, {}).get(w2, 0)
        return (pair_count + LAPLACE_ALPHA) / (
            w1_count + LAPLACE_ALPHA * self.vocab_size
        )

    def log_bigram_prob(self, w1: str, w2: str) -> float:
        return math.log(self.bigram_prob(w1, w2))

    # ── Context Re-ranking ───────────────────────────────────────────────

    def contextual_score(
        self,
        candidate: str,
        preceding_word: Optional[str] = None,
    ) -> float:
        """
        Return log-probability score for a candidate given context.
        Falls back to unigram when no preceding word is available.
        """
        if preceding_word:
            return self.log_bigram_prob(preceding_word, candidate)
        return math.log(self.unigram_prob(candidate))
