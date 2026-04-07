"""
Grammatical Analyzer
====================
Analyze tokens and extract grammatical features.
"""

from typing import Optional, List
from app.core.features import (
    SubjectFeatures, VerbFeatures, NounFeatures, GrammaticalAnalysis,
    Person, Number, Gender, Tense, Mood, GrammaticalRole, PRONOUN_FEATURES
)
from app.core.morphology import TeluguMorphology


class GrammaticalAnalyzer:
    """
    Analyzes a sequence of Telugu tokens and extracts grammatical features.
    
    Pipeline:
    1. Identify roles (subject, verb, object)
    2. Extract features from each word
    3. Build grammatical analysis
    """
    
    # ─── Known verbs (simple list for now) ────────────────────────────
    VERB_LIST = {
        # చేయ (do) conjugations
        "చేసాడు", "చేసింది", "చేసాను", "చేసారు",
        "చేస్తున్నాడు", "చేస్తున్నది", "చేస్తున్నాను",
        
        # వెళ్ళు (go) conjugations
        "వెళ్ళాడు", "వెళ్ళింది", "వెళ్ళాను", "వెళ్ళారు",
        "వెళ్తున్నాడు", "వెళ్తున్నది", "వెళ్తున్నాను",
        
        # వస (come) conjugations
        "వచ్చాడు", "వచ్చింది", "వచ్చాను", "వచ్చారు",
        
        # ఇచ్చు (give) conjugations
        "ఇచ్చాడు", "ఇచ్చింది", "ఇచ్చాను", "ఇచ్చారు",
        
        # నిర్మించు (build) conjugations
        "నిర్మించాడు", "నిర్మించింది", "నిర్మించారు",
        
        # Common verbs
        "చదువుకున్నాడు", "చదువుకున్నది", "చదువుకున్నారు",
        "ఉండాలి", "ఉండిపోయాడు", "ఉండిపోయింది",
    }
    
    # ─── Common nouns (for basic noun detection) ────────────────────
    NOUN_LIST = {
        "పాఠశాల", "పాఠశాలకు",  # school
        "ఇల్లు", "ఇల్లకు",       # house
        "కుటుంబం", "కుటుంబానికి",  # family
        "పుస్తకం", "పుస్తకాన్ని",   # book
        "పెన్ను",                   # pen
    }
    
    @staticmethod
    def is_pronoun(word: str) -> bool:
        """Check if word is a known pronoun."""
        return word in PRONOUN_FEATURES
    
    @staticmethod
    def is_verb(word: str) -> bool:
        """Check if word is a known verb."""
        return word in GrammaticalAnalyzer.VERB_LIST
    
    @staticmethod
    def is_noun(word: str) -> bool:
        """Check if word is a known noun."""
        return word in GrammaticalAnalyzer.NOUN_LIST or word.rstrip("ను") in GrammaticalAnalyzer.NOUN_LIST
    
    @staticmethod
    def identify_subject(tokens: List[str]) -> Optional[SubjectFeatures]:
        """
        Identify the subject in a token list.
        
        Strategy:
        1. Look for pronouns at the beginning
        2. Look for pronouns anywhere in the sentence
        3. Infer from verb features
        
        Returns:
            SubjectFeatures or None
        """
        # Strategy 1: Check first token (most common)
        if tokens and GrammaticalAnalyzer.is_pronoun(tokens[0]):
            features = PRONOUN_FEATURES[tokens[0]].copy()
            features.position = 0
            return features
        
        # Strategy 2: Look for pronouns anywhere
        for idx, token in enumerate(tokens):
            if GrammaticalAnalyzer.is_pronoun(token):
                features = PRONOUN_FEATURES[token].copy()
                features.position = idx
                return features
        
        # Strategy 3: Infer from verb (if any)
        # This requires analyzing the verb first
        return None
    
    @staticmethod
    def identify_verb(tokens: List[str]) -> Optional[tuple]:
        """
        Identify the main verb in a token list.
        
        Returns:
            (verb_token, position) or None
        """
        # Look for known verbs
        for idx, token in enumerate(tokens):
            if GrammaticalAnalyzer.is_verb(token):
                return (token, idx)
        
        return None
    
    @staticmethod
    def extract_subject_features(word: str, position: int) -> Optional[SubjectFeatures]:
        """
        Extract grammatical features from a subject (pronoun).
        
        Args:
            word: Subject word
            position: Position in sentence
        
        Returns:
            SubjectFeatures or None
        """
        if word in PRONOUN_FEATURES:
            features = PRONOUN_FEATURES[word].copy()
            features.position = position
            return features
        
        return None
    
    @staticmethod
    def extract_verb_features(word: str, position: int) -> Optional[VerbFeatures]:
        """
        Extract grammatical features from a verb.
        
        Args:
            word: Verb word
            position: Position in sentence
        
        Returns:
            VerbFeatures or None
        """
        stem = TeluguMorphology.get_verb_stem(word)
        if not stem:
            return None
        
        # Infer features from verb form
        person, number, gender, tense = GrammaticalAnalyzer._infer_verb_features(word)
        
        return VerbFeatures(
            person=person,
            number=number,
            gender=gender,
            tense=tense,
            mood=Mood.INDICATIVE,  # Default to indicative
            stem=stem,
            word=word,
            position=position,
        )
    
    @staticmethod
    def _infer_verb_features(word: str) -> tuple:
        """
        Infer person, number, gender, tense from verb form.
        
        Returns:
            (Person, Number, Gender, Tense)
        """
        person = Person.THIRD
        number = Number.SINGULAR
        gender = Gender.MASCULINE
        tense = Tense.PAST
        
        # Past tense detection
        if word.endswith("ాడు"):
            tense = Tense.PAST
            person = Person.THIRD
            number = Number.SINGULAR
            gender = Gender.MASCULINE
        elif word.endswith("ింది"):
            tense = Tense.PAST
            person = Person.THIRD
            number = Number.SINGULAR
            gender = Gender.FEMININE
        elif word.endswith("ాను"):
            tense = Tense.PAST
            person = Person.FIRST
            number = Number.SINGULAR
        elif word.endswith("ావు"):
            tense = Tense.PAST
            person = Person.SECOND
            number = Number.SINGULAR
        elif word.endswith("ారు"):
            tense = Tense.PAST
            number = Number.PLURAL
        elif word.endswith("ాము"):
            tense = Tense.PAST
            person = Person.FIRST
            number = Number.PLURAL
        
        # Present tense detection
        elif word.endswith("తున్నాడు"):
            tense = Tense.PRESENT
            person = Person.THIRD
            number = Number.SINGULAR
            gender = Gender.MASCULINE
        elif word.endswith("తున్నది"):
            tense = Tense.PRESENT
            person = Person.THIRD
            number = Number.SINGULAR
            gender = Gender.FEMININE
        elif word.endswith("తున్నాను"):
            tense = Tense.PRESENT
            person = Person.FIRST
            number = Number.SINGULAR
        
        # Future tense detection
        elif word.endswith("తాడు"):
            tense = Tense.FUTURE
            person = Person.THIRD
            number = Number.SINGULAR
            gender = Gender.MASCULINE
        elif word.endswith("తుంది"):
            tense = Tense.FUTURE
            person = Person.THIRD
            number = Number.SINGULAR
            gender = Gender.FEMININE
        
        return person, number, gender, tense
    
    @staticmethod
    def analyze(tokens: List[str]) -> GrammaticalAnalysis:
        """
        Perform full grammatical analysis on a token sequence.
        
        Args:
            tokens: List of Telugu words
        
        Returns:
            GrammaticalAnalysis with extracted features
        """
        analysis = GrammaticalAnalysis(tokens=tokens)
        
        # Step 1: Identify subject
        subject_token_idx = None
        for idx, token in enumerate(tokens):
            if GrammaticalAnalyzer.is_pronoun(token):
                analysis.subject = GrammaticalAnalyzer.extract_subject_features(token, idx)
                subject_token_idx = idx
                break
        
        # Step 2: Identify verb
        for idx, token in enumerate(tokens):
            if GrammaticalAnalyzer.is_verb(token):
                analysis.verb = GrammaticalAnalyzer.extract_verb_features(token, idx)
                break
        
        # Step 3: Identify objects/nouns
        for idx, token in enumerate(tokens):
            if idx != subject_token_idx and not GrammaticalAnalyzer.is_verb(token):
                if GrammaticalAnalyzer.is_noun(token) or not GrammaticalAnalyzer.is_pronoun(token):
                    # Treat as noun/object
                    noun_features = NounFeatures(
                        person=Person.THIRD,
                        number=Number.SINGULAR,
                        gender=None,  # Infer if needed
                        case=None,
                        word=token,
                        position=idx,
                    )
                    analysis.objects.append(noun_features)
        
        return analysis
