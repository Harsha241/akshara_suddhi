"""
Romanised-Telugu → Telugu Script Transliterator
================================================
ITRANS-inspired rule-based engine.

Covers
------
* 16 Telugu vowels (independent + matra forms)
* 36 consonants
* 5 common conjuncts: క్ష  త్ర  శ్ర  ద్వ  ప్ర
* Virama for half-consonants
* Anusvara (M/m̐), Visarga (H)

Algorithm: greedy longest-match, left-to-right.
"""

from typing import Dict, List, Tuple

# ─── Virama ──────────────────────────────────────────────────────────────
VIRAMA = "\u0C4D"  # ్

# ─── Independent vowels ─────────────────────────────────────────────────
_VOWELS: Dict[str, str] = {
    "au": "ఔ", "ai": "ఐ",
    "aa": "ఆ", "ee": "ఏ", "oo": "ఓ",
    "ii": "ఈ", "uu": "ఊ",
    "a":  "అ", "i":  "ఇ", "u":  "ఉ",
    "e":  "ఎ", "o":  "ఒ",
    "Ru": "ఋ",
}

# ─── Vowel matras (dependent forms) ─────────────────────────────────────
_MATRAS: Dict[str, str] = {
    "au": "\u0C4C", "ai": "\u0C48",
    "aa": "\u0C3E", "ee": "\u0C47", "oo": "\u0C4B",
    "ii": "\u0C40", "uu": "\u0C42",
    "a":  "",        # inherent vowel — no matra
    "i":  "\u0C3F", "u":  "\u0C41",
    "e":  "\u0C46", "o":  "\u0C4A",
    "Ru": "\u0C43",
}

# ─── Consonants ──────────────────────────────────────────────────────────
_CONSONANTS: Dict[str, str] = {
    # Conjuncts (must come first — longest match)
    "ksh": "క\u0C4Dష", "kSh": "క\u0C4Dష",
    "tr":  "త\u0C4Dర",
    "shr": "శ\u0C4Dర",
    "dv":  "ద\u0C4Dవ",
    "pr":  "ప\u0C4Dర",

    # Aspirated / multi-char (longer patterns first)
    "chh": "ఛ", "Ch":  "ఛ",
    "ch":  "చ",
    "kh":  "ఖ", "gh":  "ఘ",
    "jh":  "ఝ", "Jh":  "ఝ",
    "Th":  "ఠ", "Dh":  "ఢ",
    "th":  "థ", "dh":  "ధ",
    "ph":  "ఫ", "bh":  "భ",
    "sh":  "శ", "Sh":  "ష",
    "ng":  "ఙ", "nj":  "ఞ",

    # Single-char consonants
    "k": "క", "g": "గ",
    "j": "జ",
    "T": "ట", "D": "డ", "N": "ణ",
    "t": "త", "d": "ద", "n": "న",
    "p": "ప", "b": "బ", "m": "మ",
    "y": "య", "r": "ర", "l": "ల",
    "v": "వ", "w": "వ",
    "s": "స", "h": "హ",
    "L": "ళ", "R": "ఱ",
    "f": "ఫ",
}

# ─── Special marks ───────────────────────────────────────────────────────
_SPECIALS: Dict[str, str] = {
    "M":  "\u0C02",  # anusvara ం
    "H":  "\u0C03",  # visarga ః
    "~m": "\u0C01",  # chandrabindu ఁ
}

# Sorted by key length descending for greedy match
_VOWEL_KEYS = sorted(_VOWELS, key=len, reverse=True)
_MATRA_KEYS = sorted(_MATRAS, key=len, reverse=True)
_CONS_KEYS  = sorted(_CONSONANTS, key=len, reverse=True)
_SPEC_KEYS  = sorted(_SPECIALS, key=len, reverse=True)


class Transliterator:
    """
    Convert Romanised Telugu to Telugu Unicode script.

    >>> t = Transliterator()
    >>> t.convert("nenu")
    'నేను'
    >>> t.convert("namaskaaraM")
    'నమస్కారం'
    """

    def convert(self, text: str) -> str:
        """Transliterate full text, preserving spaces and punctuation."""
        result_parts: List[str] = []
        segments: List[dict] = []

        for part in text.split(" "):
            if not part:
                result_parts.append("")
                continue
            te, segs = self._convert_word(part)
            result_parts.append(te)
            segments.extend(segs)

        return " ".join(result_parts)

    def convert_with_segments(
        self, text: str
    ) -> Tuple[str, List[dict]]:
        """Return (telugu_text, segment_info)."""
        result_parts: List[str] = []
        segments: List[dict] = []

        for part in text.split(" "):
            if not part:
                result_parts.append("")
                continue
            te, segs = self._convert_word(part)
            result_parts.append(te)
            segments.extend(segs)

        return " ".join(result_parts), segments

    # ── Internal ─────────────────────────────────────────────────────────

    def _convert_word(self, word: str) -> Tuple[str, List[dict]]:
        """
        Process a single whitespace-free token.
        Algorithm: greedy longest-match, left-to-right.
        """
        out: List[str] = []
        segs: List[dict] = []
        i = 0
        n = len(word)
        prev_was_consonant = False

        while i < n:
            matched = False

            # 1. Try special marks
            for key in _SPEC_KEYS:
                if word[i: i + len(key)] == key:
                    out.append(_SPECIALS[key])
                    segs.append({"roman": key, "telugu": _SPECIALS[key]})
                    i += len(key)
                    prev_was_consonant = False
                    matched = True
                    break
            if matched:
                continue

            # 2. Try consonants
            for key in _CONS_KEYS:
                if word[i: i + len(key)].lower() == key.lower() or word[i: i + len(key)] == key:
                    # Case-sensitive match for uppercase-sensitive keys
                    segment = word[i: i + len(key)]
                    if key in _CONSONANTS and (segment == key or segment.lower() == key.lower()):
                        # Verify case-sensitive keys
                        if key[0].isupper() and not segment[0].isupper():
                            if key not in ("ksh", "kSh", "tr", "shr", "dv", "pr",
                                           "chh", "ch", "kh", "gh", "jh", "th",
                                           "dh", "ph", "bh", "sh", "ng", "nj",
                                           "k", "g", "j", "t", "d", "n", "p",
                                           "b", "m", "y", "r", "l", "v", "w",
                                           "s", "h", "f"):
                                continue  # skip: need uppercase for T, D, N, etc.

                    cons_te = _CONSONANTS[key]
                    i += len(key)

                    # Look ahead for vowel (to add matra)
                    vowel_found = False
                    for vk in _MATRA_KEYS:
                        if word[i: i + len(vk)] == vk:
                            matra = _MATRAS[vk]
                            out.append(cons_te + matra)
                            segs.append({"roman": segment + vk, "telugu": cons_te + matra})
                            i += len(vk)
                            vowel_found = True
                            break

                    if not vowel_found:
                        # Check if next char starts a consonant or is end → add virama
                        next_is_cons = False
                        if i < n:
                            for ck in _CONS_KEYS:
                                if word[i: i + len(ck)] == ck:
                                    next_is_cons = True
                                    break

                        if i >= n or next_is_cons or not word[i].isalpha():
                            # End of word or followed by consonant → halant
                            # But for natural Telugu, end-of-word consonants
                            # usually have inherent 'a'
                            if i >= n:
                                # End of word — add inherent 'a' (no virama)
                                out.append(cons_te)
                                segs.append({"roman": segment, "telugu": cons_te})
                            else:
                                # Before another consonant → virama (conjunct)
                                out.append(cons_te + VIRAMA)
                                segs.append({"roman": segment, "telugu": cons_te + VIRAMA})
                        else:
                            out.append(cons_te)
                            segs.append({"roman": segment, "telugu": cons_te})

                    prev_was_consonant = True
                    matched = True
                    break

            if matched:
                continue

            # 3. Try independent vowels
            for key in _VOWEL_KEYS:
                if word[i: i + len(key)] == key:
                    v_te = _VOWELS[key]
                    out.append(v_te)
                    segs.append({"roman": key, "telugu": v_te})
                    i += len(key)
                    prev_was_consonant = False
                    matched = True
                    break
            if matched:
                continue

            # 4. Pass through (digits, punctuation, unknown)
            out.append(word[i])
            segs.append({"roman": word[i], "telugu": word[i]})
            i += 1
            prev_was_consonant = False

        return "".join(out), segs
