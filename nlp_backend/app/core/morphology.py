"""
Telugu Morphology & Conjugation
=================================
Handle verb conjugation and word form generation.
"""

from typing import Dict, Optional
from app.core.features import Person, Number, Gender, Tense, Mood


class VerbStem:
    """
    Represents a verb stem and its conjugation patterns.
    
    Example:
    stem = "చేయ" (to do)
    → చేసాడు (did - masculine)
    → చేసింది (did - feminine)
    → చేసాను (did - first person)
    """
    
    def __init__(self, stem: str):
        self.stem = stem


class TeluguMorphology:
    """
    Conjugate Telugu verbs based on grammatical features.
    """
    
    # ─── Verb stems with their past forms ────────────────────────────
    VERB_STEMS = {
        # వెళ్ళు (go) family
        "వెళ్ళ": {
            "past_masculine": "వెళ్ళాడు",
            "past_feminine": "వెళ్ళింది",
            "past_neuter": "వెళ్ళింది",
            "past_1st": "వెళ్ళాను",
            "past_2nd": "వెళ్ళావు",
            "past_plural": "వెళ్ళారు",
            "present_masculine": "వెళ్తున్నాడు",
            "present_feminine": "వెళ్తున్నది",
            "present_neuter": "వెళ్తున్నది",
            "present_1st": "వెళ్తున్నాను",
            "future_masculine": "వెళతాడు",
            "future_feminine": "వెళతుంది",
        },
        # చేయ (do) family
        "చేయ": {
            "past_masculine": "చేసాడు",
            "past_feminine": "చేసింది",
            "past_neuter": "చేసింది",
            "past_1st": "చేసాను",
            "past_2nd": "చేసావు",
            "past_plural": "చేసారు",
            "present_masculine": "చేస్తున్నాడు",
            "present_feminine": "చేస్తున్నది",
            "present_neuter": "చేస్తున్నది",
            "present_1st": "చేస్తున్నాను",
            "future_masculine": "చేయాడు",
            "future_feminine": "చేయుంది",
        },
        # నిర్మించు (build) family
        "నిర్మించ": {
            "past_masculine": "నిర్మించాడు",
            "past_feminine": "నిర్మించింది",
            "past_neuter": "నిర్మించింది",
            "past_1st": "నిర్మించాను",
            "past_plural": "నిర్మించారు",
        },
        # వస్ (come) family
        "వస": {
            "past_masculine": "వచ్చాడు",
            "past_feminine": "వచ్చింది",
            "past_neuter": "వచ్చింది",
            "past_1st": "వచ్చాను",
            "past_plural": "వచ్చారు",
        },
        # ఇచ్చ (give) family
        "ఇచ్చ": {
            "past_masculine": "ఇచ్చాడు",
            "past_feminine": "ఇచ్చింది",
            "past_neuter": "ఇచ్చింది",
            "past_1st": "ఇచ్చాను",
            "past_plural": "ఇచ్చారు",
        },
    }
    
    # ─── Conjugation suffix patterns ─────────────────────────────────
    CONJUGATION_PATTERNS = {
        # Key: (tense, person, number, gender)
        # Value: (suffix_pattern, stem_suffix)
        
        # Past tense patterns
        (Tense.PAST, Person.THIRD, Number.SINGULAR, Gender.MASCULINE): "ాడు",
        (Tense.PAST, Person.THIRD, Number.SINGULAR, Gender.FEMININE): "ింది",
        (Tense.PAST, Person.THIRD, Number.SINGULAR, Gender.NEUTER): "ింది",
        (Tense.PAST, Person.THIRD, Number.PLURAL, Gender.MASCULINE): "ారు",
        (Tense.PAST, Person.FIRST, Number.SINGULAR, Gender.MASCULINE): "ాను",
        (Tense.PAST, Person.FIRST, Number.PLURAL, Gender.MASCULINE): "ాము",
        (Tense.PAST, Person.SECOND, Number.SINGULAR, Gender.MASCULINE): "ావు",
        (Tense.PAST, Person.SECOND, Number.PLURAL, Gender.MASCULINE): "ారు",
        
        # Present tense patterns
        (Tense.PRESENT, Person.THIRD, Number.SINGULAR, Gender.MASCULINE): "తున్నాడు",
        (Tense.PRESENT, Person.THIRD, Number.SINGULAR, Gender.FEMININE): "తున్నది",
        (Tense.PRESENT, Person.THIRD, Number.SINGULAR, Gender.NEUTER): "తున్నది",
        (Tense.PRESENT, Person.FIRST, Number.SINGULAR, Gender.MASCULINE): "తున్నాను",
        
        # Future tense patterns
        (Tense.FUTURE, Person.THIRD, Number.SINGULAR, Gender.MASCULINE): "తాడు",
        (Tense.FUTURE, Person.THIRD, Number.SINGULAR, Gender.FEMININE): "తుంది",
        (Tense.FUTURE, Person.THIRD, Number.SINGULAR, Gender.NEUTER): "తుంది",
    }
    
    @staticmethod
    def get_verb_stem(full_verb: str) -> Optional[str]:
        """
        Extract stem from a conjugated verb.
        
        Example:
        "చేసాడు" → "చేయ"
        "వెళ్ళాడు" → "వెళ్ళ"
        """
        past_suffixes = ["ాడు", "ింది", "ాను", "ావు", "ారు", "ాము"]
        
        for stem, forms in TeluguMorphology.VERB_STEMS.items():
            if full_verb in forms.values():
                return stem
        
        # Heuristic: try removing common past suffixes
        for suffix in past_suffixes:
            if full_verb.endswith(suffix):
                return full_verb[:-len(suffix)]
        
        return None
    
    @staticmethod
    def conjugate_verb(
        stem: str,
        person: Person,
        number: Number,
        gender: Gender,
        tense: Tense,
    ) -> Optional[str]:
        """
        Generate conjugated verb form.
        
        Args:
            stem: Verb root (e.g., "చేయ", "వెళ్ళ")
            person: Person (1st, 2nd, 3rd)
            number: Number (singular, plural)
            gender: Gender (masculine, feminine, neuter)
            tense: Tense (past, present, future)
        
        Returns:
            Conjugated verb form or None if not found.
            
        Example:
            stem="చేయ", person=THIRD, number=SINGULAR, gender=FEMININE, tense=PAST
            → "చేసింది"
        """
        # Try predefined conjugation table first
        key = (tense, person, number, gender)
        if key in TeluguMorphology.CONJUGATION_PATTERNS:
            suffix = TeluguMorphology.CONJUGATION_PATTERNS[key]
            return stem + suffix
        
        # Fallback: try looking up in stem table
        if stem in TeluguMorphology.VERB_STEMS:
            forms = TeluguMorphology.VERB_STEMS[stem]
            
            # Build lookup key based on features
            tense_prefix = "past" if tense == Tense.PAST else \
                          "present" if tense == Tense.PRESENT else \
                          "future"
            
            if number == Number.SINGULAR:
                if gender == Gender.MASCULINE:
                    key_name = f"{tense_prefix}_masculine"
                elif gender == Gender.FEMININE:
                    key_name = f"{tense_prefix}_feminine"
                else:  # NEUTER
                    key_name = f"{tense_prefix}_neuter"
            else:  # PLURAL
                if person == Person.FIRST:
                    key_name = f"{tense_prefix}_1st_plural"
                elif person == Person.SECOND:
                    key_name = f"{tense_prefix}_2nd_plural"
                else:
                    key_name = f"{tense_prefix}_plural"
            
            return forms.get(key_name)
        
        return None
    
    @staticmethod
    def get_possible_stems(word: str) -> list:
        """
        Identify possible stems from a word.
        
        Example:
        "వెళ్ళాడు" → ["వెళ్ళ"]
        "చేసింది" → ["చేయ"]
        """
        stems = []
        
        # Direct lookup
        for stem in TeluguMorphology.VERB_STEMS:
            forms = TeluguMorphology.VERB_STEMS[stem]
            if word in forms.values():
                stems.append(stem)
        
        # Suffix heuristic
        past_suffixes = ["ాడు", "ింది", "ాను", "ావు", "ారు", "ాము"]
        for suffix in past_suffixes:
            if word.endswith(suffix):
                possible_stem = word[:-len(suffix)]
                if possible_stem not in stems:
                    stems.append(possible_stem)
        
        return stems
