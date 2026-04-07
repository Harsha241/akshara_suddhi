"""
Grammar Corrector
=================
Apply corrections with locking mechanism to prevent overwriting.
"""

from typing import List, Dict, Set
from app.core.features import GrammaticalAnalysis
from app.core.rules import GrammarError
from app.core.morphology import TeluguMorphology


class CorrectionLock:
    """
    Mechanism to prevent overwriting already-corrected words.
    """
    
    def __init__(self, tokens: List[str]):
        self.tokens = tokens
        self.locked_positions: Set[int] = set()
        self.correction_history: Dict[int, str] = {}  # position -> corrected_word
    
    def is_locked(self, position: int) -> bool:
        """Check if a position is locked."""
        return position in self.locked_positions
    
    def lock(self, position: int, corrected_word: str) -> None:
        """Lock a position with its correction."""
        if position not in self.locked_positions:
            self.locked_positions.add(position)
            self.correction_history[position] = corrected_word
    
    def get_current_token(self, position: int) -> str:
        """Get the current token (original or corrected)."""
        if position in self.correction_history:
            return self.correction_history[position]
        return self.tokens[position] if position < len(self.tokens) else ""
    
    def update_token(self, position: int, new_word: str) -> bool:
        """
        Update a token if not locked.
        
        Returns:
            True if update was successful, False if locked
        """
        if self.is_locked(position):
            return False
        
        self.tokens[position] = new_word
        self.correction_history[position] = new_word
        return True
    
    def apply_and_lock(self, position: int, corrected_word: str) -> bool:
        """
        Apply correction and lock the position.
        
        Returns:
            True if successful, False if already locked
        """
        if self.is_locked(position):
            return False
        
        self.tokens[position] = corrected_word
        self.lock(position, corrected_word)
        return True


class GrammarCorrector:
    """
    Apply grammar corrections to tokens based on errors.
    """
    
    @staticmethod
    def correct_subject_verb_agreement(
        tokens: List[str],
        analysis: GrammaticalAnalysis,
        locks: CorrectionLock,
        errors: List[GrammarError],
    ) -> List[str]:
        """
        Correct subject-verb agreement errors.
        
        Strategy:
        1. Extract verb stem
        2. Regenerate verb with subject features
        3. Lock the correction
        """
        corrected_tokens = tokens.copy()
        
        if not analysis.subject or not analysis.verb:
            return corrected_tokens
        
        # Find grammar errors related to subject-verb agreement
        agreement_errors = [
            e for e in errors 
            if "subject_verb_agreement" in e.error_type
        ]
        
        if not agreement_errors or locks.is_locked(analysis.verb.position):
            return corrected_tokens
        
        verb = analysis.verb
        subject = analysis.subject
        
        # Regenerate verb with subject features
        correct_verb = TeluguMorphology.conjugate_verb(
            stem=verb.stem,
            person=subject.person,
            number=subject.number,
            gender=subject.gender,
            tense=verb.tense,
        )
        
        if correct_verb and correct_verb != verb.word:
            success = locks.apply_and_lock(verb.position, correct_verb)
            if success:
                corrected_tokens[verb.position] = correct_verb
        
        return corrected_tokens
    
    @staticmethod
    def correct_postposition_agreement(
        tokens: List[str],
        locks: CorrectionLock,
        errors: List[GrammarError],
    ) -> List[str]:
        """
        Correct postposition/case markers on nouns.
        """
        corrected_tokens = tokens.copy()
        
        # Find postposition errors
        postposition_errors = [
            e for e in errors 
            if e.error_type == "postposition_agreement"
        ]
        
        for error in postposition_errors:
            position = error.position
            if locks.is_locked(position):
                continue
            
            if error.expected_form:
                success = locks.apply_and_lock(position, error.expected_form)
                if success:
                    corrected_tokens[position] = error.expected_form
        
        return corrected_tokens
    
    @staticmethod
    def apply_grammar_corrections(
        tokens: List[str],
        analysis: GrammaticalAnalysis,
        errors: List[GrammarError],
    ) -> tuple:
        """
        Apply all grammar corrections with locking mechanism.
        
        Args:
            tokens: Original tokens
            analysis: Grammatical analysis results
            errors: List of detected errors
        
        Returns:
            (corrected_tokens, locks, applied_corrections)
        """
        corrected_tokens = tokens.copy()
        locks = CorrectionLock(tokens)
        applied_corrections = []
        
        # Step 1: Correct subject-verb agreement (priority 1)
        corrected_tokens = GrammarCorrector.correct_subject_verb_agreement(
            corrected_tokens, analysis, locks, errors
        )
        
        # Track applied corrections
        if analysis.verb and locks.is_locked(analysis.verb.position):
            applied_corrections.append({
                "position": analysis.verb.position,
                "original": tokens[analysis.verb.position],
                "corrected": corrected_tokens[analysis.verb.position],
                "error_type": "subject_verb_agreement",
            })
        
        # Step 2: Correct postposition agreement (priority 2)
        corrected_tokens = GrammarCorrector.correct_postposition_agreement(
            corrected_tokens, locks, errors
        )
        
        # Track applied corrections
        for pos, corrected in locks.correction_history.items():
            if pos != analysis.verb.position if analysis.verb else True:
                applied_corrections.append({
                    "position": pos,
                    "original": tokens[pos],
                    "corrected": corrected,
                    "error_type": "postposition_agreement",
                })
        
        return corrected_tokens, locks, applied_corrections
