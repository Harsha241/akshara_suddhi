"""
Grammar Rules & Validation
===========================
Define grammar rules and validate grammatical correctness.
"""

from typing import List, Optional
from dataclasses import dataclass
from app.core.features import (
    SubjectFeatures, VerbFeatures, NounFeatures, GrammaticalAnalysis,
    Person, Number, Gender, Tense
)


@dataclass
class GrammarError:
    """Represents a grammar error."""
    position: int
    word: str
    error_type: str  # "subject_verb_agreement", "tense_consistency", etc.
    expected_form: Optional[str]
    explanation: str


class GrammarRules:
    """
    Defines grammar rules for Telugu.
    """
    
    @staticmethod
    def check_subject_verb_agreement(
        analysis: GrammaticalAnalysis
    ) -> List[GrammarError]:
        """
        Check if subject and verb agree in person, number, and gender.
        
        Rule: Subject.person == Verb.person
              Subject.number == Verb.number
              Subject.gender == Verb.gender (for 3rd person singular)
        
        Returns:
            List of GrammarErrors
        """
        errors = []
        
        if not analysis.subject or not analysis.verb:
            return errors
        
        subject = analysis.subject
        verb = analysis.verb
        
        # Check person agreement
        if subject.person != verb.person:
            errors.append(GrammarError(
                position=verb.position,
                word=verb.word,
                error_type="subject_verb_agreement_person",
                expected_form=None,
                explanation=(
                    f"Verb does not match subject person: "
                    f"subject is {subject.person.name} person, "
                    f"but verb is {verb.person.name} person"
                ),
            ))
        
        # Check number agreement
        if subject.number != verb.number:
            errors.append(GrammarError(
                position=verb.position,
                word=verb.word,
                error_type="subject_verb_agreement_number",
                expected_form=None,
                explanation=(
                    f"Verb does not match subject number: "
                    f"subject is {subject.number.value}, "
                    f"but verb is {verb.number.value}"
                ),
            ))
        
        # Check gender agreement (important for 3rd person singular)
        if (subject.person == Person.THIRD and 
            subject.number == Number.SINGULAR and 
            subject.gender != verb.gender):
            errors.append(GrammarError(
                position=verb.position,
                word=verb.word,
                error_type="subject_verb_agreement_gender",
                expected_form=None,
                explanation=(
                    f"Verb gender does not match subject: "
                    f"subject is {subject.gender.value}, "
                    f"but verb is {verb.gender.value}"
                ),
            ))
        
        return errors
    
    @staticmethod
    def check_tense_consistency(
        analysis: GrammaticalAnalysis
    ) -> List[GrammarError]:
        """
        Check that all verbs in the sentence use consistent tense.
        
        Returns:
            List of GrammarErrors for tense inconsistencies
        """
        errors = []
        
        if not analysis.verb:
            return errors
        
        # For now, we only check the main verb
        # In future, extract all verbs and check consistency
        
        return errors
    
    @staticmethod
    def check_postposition_agreement(
        analysis: GrammaticalAnalysis
    ) -> List[GrammarError]:
        """
        Check that nouns have appropriate postpositions/cases.
        
        Example:
        "పాఠశాల వెళ్ళాడు" → error (missing "కు")
        "పాఠశాలకు వెళ్ళాడు" → correct
        
        Returns:
            List of GrammarErrors
        """
        errors = []
        
        if not analysis.objects or not analysis.verb:
            return errors
        
        verb = analysis.verb
        
        # Directional verbs require dative case (కు) on object
        directional_verbs = {"వెళ్ళ", "వస", "చేర", "దూసుకోవల"}
        
        if verb.stem in directional_verbs:
            for obj in analysis.objects:
                # Check if noun has dative marker (కు)
                if not obj.word.endswith("కు"):
                    errors.append(GrammarError(
                        position=obj.position,
                        word=obj.word,
                        error_type="postposition_agreement",
                        expected_form=obj.word + "కు",
                        explanation=(
                            f"Directional verb '{verb.stem}' requires dative case. "
                            f"Add 'కు' to '{obj.word}'"
                        ),
                    ))
        
        return errors
    
    @staticmethod
    def validate_all(analysis: GrammaticalAnalysis) -> List[GrammarError]:
        """
        Run all grammar validation rules.
        
        Returns:
            Combined list of all grammar errors found
        """
        errors = []
        
        errors.extend(GrammarRules.check_subject_verb_agreement(analysis))
        errors.extend(GrammarRules.check_tense_consistency(analysis))
        errors.extend(GrammarRules.check_postposition_agreement(analysis))
        
        return errors
