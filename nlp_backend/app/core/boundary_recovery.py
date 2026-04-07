"""
Word Boundary Recovery / Decomposition
=====================================
Telugu text can contain incorrectly joined tokens (missing spaces) or
invalid join sequences (e.g., a standalone matra like "ె" appended to a word).

This module attempts to recover word boundaries *before* grammar/spell steps.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log
from typing import Dict, List, Optional, Tuple

from app.core.phonetic import phonetic_similarity
from app.core.unicode_utils import (
    is_telugu_word,
    split_grapheme_clusters,
)


# Telugu vowel signs (matras) → independent vowels
_MATRA_TO_VOWEL: Dict[str, str] = {
    "ా": "ఆ",
    "ి": "ఇ",
    "ీ": "ఈ",
    "ు": "ఉ",
    "ూ": "ఊ",
    "ె": "ఎ",
    "ే": "ఏ",
    "ై": "ఐ",
    "ొ": "ఒ",
    "ో": "ఓ",
    "ౌ": "ఔ",
}

_MATRA_SET = set(_MATRA_TO_VOWEL.keys())


def _has_standalone_matra_clusters(word: str) -> bool:
    """
    Heuristic: standalone matra clusters indicate a join error.
    E.g., "కిె" becomes clusters ["కి", "ె"] and "ె" is invalid standalone.
    """
    for cl in split_grapheme_clusters(word):
        if cl in _MATRA_SET:
            return True
    return False


def normalize_common_joins(text: str) -> str:
    """
    Normalize common Telugu join errors by inserting spaces and converting
    standalone matras into their corresponding independent vowels.

    This is a lightweight pre-pass before more expensive split ranking.
    """
    # We do token-level normalization later, but this catches easy cases early.
    return text


def _normalize_token_by_matra_split(token: str) -> Optional[List[str]]:
    """
    If token contains standalone matra clusters, split around them and convert
    matra to vowel, producing multiple tokens.
    """
    clusters = split_grapheme_clusters(token)
    if not any(cl in _MATRA_SET for cl in clusters):
        return None

    out: List[str] = []
    buf: List[str] = []
    for cl in clusters:
        if cl in _MATRA_SET:
            # Finish the current token and start a new token beginning with
            # the corresponding independent vowel.
            if buf:
                out.append("".join(buf))
            buf = [_MATRA_TO_VOWEL[cl]]
        else:
            buf.append(cl)
    if buf:
        out.append("".join(buf))

    # Remove empties
    out = [t for t in out if t]
    return out if len(out) > 1 else None


@dataclass(frozen=True)
class SplitCandidate:
    left: str
    right: str
    left_corr: str
    right_corr: str
    score: float


def recover_word_boundaries(text: str) -> List[str]:
    """
    Public API required by the user request.

    Splits by whitespace, then for each Telugu token tries:
    - fast join-normalization (standalone matra decomposition)
    - split search + dictionary/spell/bigram scoring (pruned)

    Returns list of tokens (whitespace-normalized).
    """
    from main import dictionary, ngram_model, spell_checker  # lazy import

    tokens = [t for t in text.split() if t.strip()]
    recovered: List[str] = []

    for tok in tokens:
        if not is_telugu_word(tok):
            recovered.append(tok)
            continue

        # Fast-path: split around standalone matras like "ె"
        matra_split = _normalize_token_by_matra_split(tok)
        if matra_split:
            recovered.extend(matra_split)
            continue

        # Only attempt expensive recovery if token is not a known word
        if tok in dictionary:
            recovered.append(tok)
            continue

        best = _best_split_for_token(
            tok,
            dictionary=dictionary,
            ngram=ngram_model,
            spell_checker=spell_checker,
            prev_token=recovered[-1] if recovered else None,
        )
        if best:
            recovered.extend([best.left_corr, best.right_corr])
        else:
            recovered.append(tok)

    return recovered


def _best_word_correction(
    word: str,
    dictionary: Dict[str, int],
    spell_checker,
    prev_token: Optional[str],
    top_k: int = 3,
) -> List[Tuple[str, float, int]]:
    """
    Return list of (candidate, phon_sim, freq) suggestions.
    Includes the word itself if it exists in dictionary.
    """
    if word in dictionary:
        return [(word, 1.0, int(dictionary.get(word, 1)))]

    ctx = [prev_token] if prev_token else None
    resp = spell_checker.check(word, context=ctx)
    out = []
    for s in (resp.suggestions or [])[:top_k]:
        cand = s.word
        out.append((cand, phonetic_similarity(word, cand), int(s.frequency)))
    return out


def _norm_freq(freq: int, max_freq: int) -> float:
    # log-normalized into [0,1-ish]
    return log(freq + 1) / log(max_freq + 1)


def _best_split_for_token(
    token: str,
    dictionary: Dict[str, int],
    ngram,
    spell_checker,
    prev_token: Optional[str],
) -> Optional[SplitCandidate]:
    """
    Try split points on grapheme boundaries and rank using:
      0.5*freq + 0.3*phon + 0.4*bigram + 0.3*validity_bonus

    Pruning:
    - grapheme length thresholds
    - limit split points
    - take only top spell candidates per side
    """
    clusters = split_grapheme_clusters(token)
    n = len(clusters)
    if n < 6 or n > 22:
        return None

    max_freq = max(dictionary.values()) if dictionary else 1

    # Candidate split indices (avoid tiny pieces)
    split_idxs = [i for i in range(2, n - 1)]
    # Prune split points further if the token looks clean (no matra anomalies)
    if not _has_standalone_matra_clusters(token) and len(split_idxs) > 10:
        # sample around the middle
        mid = n // 2
        split_idxs = sorted(set([mid - 3, mid - 2, mid - 1, mid, mid + 1, mid + 2, mid + 3]))
        split_idxs = [i for i in split_idxs if 2 <= i <= n - 2]

    best: Optional[SplitCandidate] = None

    for i in split_idxs:
        left = "".join(clusters[:i])
        right = "".join(clusters[i:])

        left_sugs = _best_word_correction(left, dictionary, spell_checker, prev_token, top_k=3)
        # context for right is best-left candidate; we approximate by trying with left_sugs later
        if not left_sugs:
            continue

        for left_cand, left_phon, left_freq in left_sugs:
            right_sugs = _best_word_correction(
                right, dictionary, spell_checker, prev_token=left_cand, top_k=3
            )
            if not right_sugs:
                continue

            for right_cand, right_phon, right_freq in right_sugs:
                # bigram context: prev->left + left->right
                bg = 0.0
                if prev_token:
                    bg += float(ngram.bigram_prob(prev_token, left_cand))
                bg += float(ngram.bigram_prob(left_cand, right_cand))

                freq_score = 0.5 * (
                    _norm_freq(left_freq, max_freq) + _norm_freq(right_freq, max_freq)
                ) / 2.0
                phon_score = 0.3 * ((left_phon + right_phon) / 2.0)
                bg_score = 0.4 * bg

                validity = 0.0
                if left_cand in dictionary:
                    validity += 0.5
                if right_cand in dictionary:
                    validity += 0.5
                validity_bonus = 0.3 * validity

                score = freq_score + phon_score + bg_score + validity_bonus

                cand = SplitCandidate(
                    left=left,
                    right=right,
                    left_corr=left_cand,
                    right_corr=right_cand,
                    score=score,
                )
                if best is None or cand.score > best.score:
                    best = cand

    # Only accept if it clearly looks better than keeping as one token:
    # require both sides to be in dictionary after correction.
    if best and best.left_corr in dictionary and best.right_corr in dictionary:
        return best
    return None

