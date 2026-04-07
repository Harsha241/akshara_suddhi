"""
Telugu Unicode Utilities
========================
- Grapheme cluster segmentation  (కి, క్ష  → single units)
- Character classification        (vowel / consonant / matra / modifier)
- Tokenization for mixed Telugu + English text

Telugu Unicode block: U+0C00 – U+0C7F
"""

import re
import unicodedata
from typing import List

# ─── Telugu code-point ranges ───────────────────────────────────────────
CHANDRABINDU = 0x0C01
ANUSVARA     = 0x0C02
VISARGA      = 0x0C03

VOWEL_LO, VOWEL_HI         = 0x0C05, 0x0C14
CONSONANT_LO, CONSONANT_HI = 0x0C15, 0x0C39
EXTRA_CONSONANTS            = {0x0C33, 0x0C58, 0x0C59, 0x0C5A}

MATRA_LO, MATRA_HI = 0x0C3E, 0x0C4C
VIRAMA              = 0x0C4D
DIGIT_LO, DIGIT_HI = 0x0C66, 0x0C6F

# ─── Single-char classifiers ───────────────────────────────────────────

def is_telugu_char(ch: str) -> bool:
    return 0x0C00 <= ord(ch) <= 0x0C7F

def is_vowel(cp: int) -> bool:
    return VOWEL_LO <= cp <= VOWEL_HI

def is_consonant(cp: int) -> bool:
    return (CONSONANT_LO <= cp <= CONSONANT_HI) or cp in EXTRA_CONSONANTS

def is_matra(cp: int) -> bool:
    return MATRA_LO <= cp <= MATRA_HI

def is_virama(cp: int) -> bool:
    return cp == VIRAMA

def is_modifier(cp: int) -> bool:
    return cp in (CHANDRABINDU, ANUSVARA, VISARGA)

# ─── Word-level classifiers ────────────────────────────────────────────

def is_telugu_word(word: str) -> bool:
    """True when >50 % of alphabetic chars are Telugu."""
    if not word:
        return False
    te = sum(1 for c in word if is_telugu_char(c))
    al = sum(1 for c in word if c.isalpha() or is_telugu_char(c))
    return al > 0 and te / al > 0.5

def is_english_word(word: str) -> bool:
    return bool(word) and all(c.isascii() and c.isalpha() for c in word)

def is_punctuation_or_number(token: str) -> bool:
    return bool(
        re.fullmatch(
            r'[0-9\u0C66-\u0C6F.,!?;:\-–—\'\"()\[\]{}…।॥/\\@#$%^&*+=<>~`]+',
            token,
        )
    )

# ─── Grapheme cluster segmentation ─────────────────────────────────────

def split_grapheme_clusters(text: str) -> List[str]:
    """
    Split Telugu text into grapheme clusters.

    Rules
    -----
    * Consonant  → absorb  (virama + consonant)*  → absorb matra?  → absorb modifier*
    * Vowel      → absorb modifier*
    * Non-Telugu → one cluster per character

    Examples
    --------
    >>> split_grapheme_clusters("నేను")
    ['నే', 'ను']
    >>> split_grapheme_clusters("క్షమ")
    ['క్ష', 'మ']
    """
    clusters: List[str] = []
    chars = list(text)
    n = len(chars)
    i = 0

    while i < n:
        ch = chars[i]
        cp = ord(ch)

        # Non-Telugu → standalone
        if not is_telugu_char(ch):
            clusters.append(ch)
            i += 1
            continue

        buf = [ch]
        i += 1

        if is_consonant(cp):
            # Absorb conjuncts: (virama + consonant)*
            while i < n:
                ncp = ord(chars[i])
                if is_virama(ncp) and i + 1 < n and is_consonant(ord(chars[i + 1])):
                    buf.append(chars[i])      # virama
                    buf.append(chars[i + 1])   # consonant
                    i += 2
                elif is_virama(ncp):
                    buf.append(chars[i]); i += 1; break
                elif is_matra(ncp):
                    buf.append(chars[i]); i += 1; break
                else:
                    break
            # trailing modifiers
            while i < n and is_modifier(ord(chars[i])):
                buf.append(chars[i]); i += 1

        elif is_vowel(cp):
            while i < n and is_modifier(ord(chars[i])):
                buf.append(chars[i]); i += 1

        clusters.append("".join(buf))

    return clusters

def grapheme_len(text: str) -> int:
    return len(split_grapheme_clusters(text))

# ─── Normalization & tokenization ───────────────────────────────────────

def normalize_telugu(text: str) -> str:
    return unicodedata.normalize("NFC", text)

def tokenize_telugu(text: str) -> List[str]:
    """Split mixed Telugu/English text into word-level tokens."""
    tokens = re.findall(
        r'[\u0C00-\u0C7F]+|[a-zA-Z]+|[0-9]+|[^\s\u0C00-\u0C7Fa-zA-Z0-9]',
        text,
    )
    return [t for t in tokens if t.strip()]


def tokenize_telugu_with_spans(text: str) -> List[dict]:
    """
    Tokenize mixed Telugu/English text into tokens with character spans.

    Returns a list of dicts: { "text": str, "start": int, "end": int }
    """
    out: List[dict] = []
    pat = re.compile(
        r'[\u0C00-\u0C7F]+|[a-zA-Z]+|[0-9]+|[^\s\u0C00-\u0C7Fa-zA-Z0-9]'
    )
    for m in pat.finditer(text):
        tok = m.group(0)
        if not tok.strip():
            continue
        out.append({"text": tok, "start": m.start(), "end": m.end()})
    return out
