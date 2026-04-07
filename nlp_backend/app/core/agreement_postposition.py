"""
Subject–Verb Agreement + Postposition Insertion
================================================
This module fixes grammar issues that *won't* trigger spell correction
because all tokens are dictionary-valid.

Capabilities (minimal but extensible):
- Detect subject pronouns: నేను, నీవు/నువ్వు, అతను, ఆమె, వారు
- Fix simple present/future verb endings to match subject:
    తాడు/తుంది/తారు/తాను/తాము/తావు  -> subject-appropriate ending
- Insert common postposition "కు" for motion verbs like "వెళ్త..."

It returns GrammarError objects with start/end offsets when token spans
are provided by tokenization.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from app.models import GrammarError


@dataclass(frozen=True)
class SubjectInfo:
    pronoun: str
    person: str  # "1"|"2"|"3"
    number: str  # "sg"|"pl"
    gender: Optional[str] = None  # "m"|"f"|None


_SUBJECTS: Dict[str, SubjectInfo] = {
    "నేను": SubjectInfo("నేను", "1", "sg"),
    "నీవు": SubjectInfo("నీవు", "2", "sg"),
    "నువ్వు": SubjectInfo("నువ్వు", "2", "sg"),
    "అతను": SubjectInfo("అతను", "3", "sg", "m"),
    "ఆమె": SubjectInfo("ఆమె", "3", "sg", "f"),
    "వారు": SubjectInfo("వారు", "3", "pl"),
    "మీరు": SubjectInfo("మీరు", "2", "pl"),
}


# Simple present / future style endings
_VERB_ENDINGS = ("తాడు", "తుంది", "తారు", "తాను", "తాము", "తావు")
_VERB_END_RE = re.compile("(" + "|".join(map(re.escape, _VERB_ENDINGS)) + r")$")

# Present continuous endings
_PRES_CONT_ENDINGS = (
    "తున్నాడు",
    "తున్నది",
    "తున్నారు",
    "తున్నాను",
    "తున్నాము",
    "తున్నావు",
    "తోంది",
)
_PRES_CONT_END_RE = re.compile("(" + "|".join(map(re.escape, _PRES_CONT_ENDINGS)) + r")$")

# Past-tense agreement endings (seen in grammar_engine tense patterns)
_PAST_ENDINGS = ("ాడు", "ింది", "ారు", "ాను", "ాము", "ావు")
_PAST_END_RE = re.compile("(" + "|".join(map(re.escape, _PAST_ENDINGS)) + r")$")


def detect_subject(tokens: Sequence[str]) -> Optional[Tuple[int, SubjectInfo]]:
    """Return (index, SubjectInfo) for the first subject pronoun found."""
    for i, t in enumerate(tokens):
        if t in _SUBJECTS:
            return i, _SUBJECTS[t]
    return None


def _target_ending(subj: SubjectInfo) -> str:
    if subj.person == "1" and subj.number == "sg":
        return "తాను"
    if subj.person == "2" and subj.number == "sg":
        return "తావు"
    if subj.person == "2" and subj.number == "pl":
        return "తారు"
    if subj.person == "3" and subj.number == "pl":
        return "తారు"
    if subj.person == "3" and subj.number == "sg":
        # Gendered default for 3sg when we know it (e.g., ఆమె -> తుంది).
        if subj.gender == "f":
            return "తుంది"
        return "తాడు"
    return "తాడు"


def _target_pres_cont_ending(subj: SubjectInfo) -> str:
    if subj.person == "1" and subj.number == "sg":
        return "తున్నాను"
    if subj.person == "2" and subj.number == "sg":
        return "తున్నావు"
    if subj.person == "2" and subj.number == "pl":
        return "తున్నారు"
    if subj.person == "3" and subj.number == "pl":
        return "తున్నారు"
    if subj.person == "3" and subj.number == "sg":
        if subj.gender == "f":
            return "తున్నది"
        return "తున్నాడు"
    return "తున్నాడు"


def _target_past_ending(subj: SubjectInfo) -> str:
    if subj.person == "1" and subj.number == "sg":
        return "ాను"
    if subj.person == "2" and subj.number == "sg":
        return "ావు"
    if subj.person == "2" and subj.number == "pl":
        return "ారు"
    if subj.person == "3" and subj.number == "pl":
        return "ారు"
    if subj.person == "3" and subj.number == "sg":
        if subj.gender == "f":
            return "ింది"
        return "ాడు"
    return "ాడు"


def correct_verb_agreement(
    tokens: List[str],
    token_spans: Optional[Sequence[dict]] = None,
) -> Tuple[List[str], List[GrammarError]]:
    """
    Fix verb forms to match detected subject.

    Important: Telugu sentences can have multiple verbs (compound clauses).
    We correct *each* verb-like token whose ending clearly mismatches the subject,
    rather than only the last verb.
    """
    subj = detect_subject(tokens)
    if not subj:
        return tokens, []
    _, subj_info = subj

    corrected = list(tokens)
    errors: List[GrammarError] = []

    for verb_idx, original in enumerate(tokens):
        m = (
            _PRES_CONT_END_RE.search(original)
            or _VERB_END_RE.search(original)
            or _PAST_END_RE.search(original)
        )
        if not m:
            continue

        ending = m.group(1)
        if _PAST_END_RE.search(original):
            wanted = _target_past_ending(subj_info)
            new_word = _PAST_END_RE.sub(wanted, original)
        elif _PRES_CONT_END_RE.search(original):
            wanted = _target_pres_cont_ending(subj_info)
            new_word = _PRES_CONT_END_RE.sub(wanted, original)
        else:
            wanted = _target_ending(subj_info)
            new_word = _VERB_END_RE.sub(wanted, original)

        if ending == wanted or new_word == original:
            continue

        corrected[verb_idx] = new_word

        start = end = None
        if token_spans and 0 <= verb_idx < len(token_spans):
            start = token_spans[verb_idx].get("start")
            end = token_spans[verb_idx].get("end")

        errors.append(
            GrammarError(
                word=original,
                position=verb_idx,
                rule_category="subject_verb_agreement",
                correction=new_word,
                explanation=f"Verb form adjusted to match subject '{subj_info.pronoun}'.",
                start=start,
                end=end,
            )
        )

    return corrected, errors


_MOTION_VERB_PREFIXES = ("వెళ్త", "పోత", "వచ్చ")
_HAS_POSTPOS_RE = re.compile(r"(కు|కి|లో|లోకి)$")
_VOWEL_END_RE = re.compile(r".*[ాిీుూెేైొోౌ]$")


def insert_postpositions(
    tokens: List[str],
    token_spans: Optional[Sequence[dict]] = None,
) -> Tuple[List[str], List[GrammarError]]:
    """
    Very small, high-precision rule:
    If we detect a motion verb (e.g. 'వెళ్త...') and the token right before it
    is a bare noun without a postposition, append 'కు'.
    """
    corrected = list(tokens)
    errors: List[GrammarError] = []

    # Find a motion verb candidate (last token starting with a prefix)
    verb_idx = None
    for i in range(len(tokens) - 1, -1, -1):
        if any(tokens[i].startswith(p) for p in _MOTION_VERB_PREFIXES):
            verb_idx = i
            break
    if verb_idx is None or verb_idx == 0:
        return corrected, errors

    noun_idx = verb_idx - 1
    noun = tokens[noun_idx]

    # Skip if already has a common postposition marker
    if _HAS_POSTPOS_RE.search(noun):
        return corrected, errors

    # Don't attach to pronouns or punctuation-like tokens
    if noun in _SUBJECTS:
        return corrected, errors
    if not noun.strip():
        return corrected, errors

    # Choose 'కి' after vowel-ending nouns, else 'కు' (simple, high-precision heuristic)
    # Examples: "ఇంటి" -> "ఇంటికి", "బడి" -> "బడికి", "పాఠశాల" -> "పాఠశాలకు"
    suffix = "కి" if _VOWEL_END_RE.fullmatch(noun) else "కు"
    new_noun = noun + suffix
    corrected[noun_idx] = new_noun

    start = end = None
    if token_spans and 0 <= noun_idx < len(token_spans):
        start = token_spans[noun_idx].get("start")
        end = token_spans[noun_idx].get("end")

    errors.append(
        GrammarError(
            word=noun,
            position=noun_idx,
            rule_category="postposition_insertion",
            correction=new_noun,
            explanation="Added a common postposition for motion verb context.",
            start=start,
            end=end,
        )
    )

    return corrected, errors


def apply_agreement_and_postpositions(
    tokens: List[str],
    token_spans: Optional[Sequence[dict]] = None,
) -> Tuple[List[str], List[GrammarError]]:
    """
    Apply agreement first, then postposition insertion.
    Returns (corrected_tokens, errors).
    """
    t1, e1 = correct_verb_agreement(tokens, token_spans=token_spans)
    t2, e2 = insert_postpositions(t1, token_spans=token_spans)
    return t2, [*e1, *e2]

