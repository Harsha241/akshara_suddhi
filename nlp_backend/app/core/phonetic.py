"""
Telugu Phonetic Similarity
==========================
Confused-pair substitution costs 0.5 instead of 1.0.
Groups based on articulatory features (place, manner, voicing).
"""

from typing import List

from app.core.unicode_utils import split_grapheme_clusters

# ─── Phonetic confusion groups ──────────────────────────────────────────
CONFUSION_GROUPS: List[set] = [
    # Sibilants
    {"శ", "ష", "స"},
    # Labial approx / stop
    {"బ", "వ"},
    # Retroflex
    {"ళ", "డ"},
    # Nasals
    {"న", "ణ"},
    # Dental stops
    {"త", "థ"},
    {"ద", "ధ"},
    # Velar stops
    {"క", "గ"},
    {"ఖ", "ఘ"},
    # Retroflex stops
    {"ట", "డ"},
    {"ఠ", "ఢ"},
    # Palatal stops
    {"చ", "జ"},
    {"ఛ", "ఝ"},
    # Labial stops
    {"ప", "బ"},
    {"ఫ", "భ"},
    # Liquids
    {"ర", "ల", "ళ"},
    # Nasals broad
    {"మ", "న"},
    # Short / long vowels
    {"అ", "ఆ"}, {"ఇ", "ఈ"}, {"ఉ", "ఊ"}, {"ఎ", "ఏ"}, {"ఒ", "ఓ"},
    # Short / long matras
    {"ి", "ీ"}, {"ు", "ూ"}, {"ె", "ే"}, {"ొ", "ో"},
]

# Pre-compute pair set for O(1) lookup
_PAIRS: set = set()
for _g in CONFUSION_GROUPS:
    _gl = list(_g)
    for _i in range(len(_gl)):
        for _j in range(_i + 1, len(_gl)):
            _PAIRS.add(frozenset({_gl[_i], _gl[_j]}))


def is_confused_pair(a: str, b: str) -> bool:
    if a == b:
        return True
    return frozenset({a, b}) in _PAIRS


def substitution_cost(a: str, b: str) -> float:
    """0.0 identical · 0.5 confused pair · 1.0 otherwise"""
    if a == b:
        return 0.0
    return 0.5 if is_confused_pair(a, b) else 1.0


def phonetic_similarity(word_a: str, word_b: str) -> float:
    """
    Score in [0, 1].  Compares base characters of aligned grapheme clusters.
    """
    ca = split_grapheme_clusters(word_a)
    cb = split_grapheme_clusters(word_b)
    mx = max(len(ca), len(cb))
    if mx == 0:
        return 1.0
    score = 0.0
    for i in range(mx):
        if i < len(ca) and i < len(cb):
            if ca[i] == cb[i]:
                score += 1.0
            elif is_confused_pair(ca[i][0], cb[i][0]):
                score += 0.75
    return score / mx
