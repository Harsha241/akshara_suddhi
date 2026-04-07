"""
Linguistic Grammar Engine (New)
================================
Redesigned grammar checking using linguistic analysis pipeline.

Pipeline:
1. Tokenize input
2. Analyze grammatical structure
3. Extract features
4. Validate rules
5. Apply corrections with locking
6. Return results
"""

from typing import List, Optional
from app.core.analyzer import GrammaticalAnalyzer
from app.core.rules import GrammarRules, GrammarError
from app.core.corrector import GrammarCorrector
from app.core.unicode_utils import tokenize_telugu
from app.models import GrammarCheckResponse


class LinguisticGrammarEngine:
    """
    Grammar engine based on proper linguistic analysis.
    
    Features:
    - Feature-based validation (not pattern matching)
    - Proper verb regeneration (not suffix replacement)
    - Locking mechanism to prevent overwriting
    - Clear separation of analysis, validation, correction
    """
    
    def __init__(self):
        """Initialize the grammar engine."""
        self.analyzer = GrammaticalAnalyzer()
        self.rules = GrammarRules()
    
    def check(self, tokens: List[str]) -> GrammarCheckResponse:
        """
        Check a sentence for grammar errors.
        
        Pipeline:
        1. Analyze grammatical structure → extract features
        2. Validate rules → detect errors
        3. Correct errors → apply fixes with locking
        4. Return response
        
        Args:
            tokens: List of Telugu words
        
        Returns:
            GrammarCheckResponse with errors and corrections
        """
        # Step 1: Grammatical Analysis
        analysis = self.analyzer.analyze(tokens)
        
        # Step 2: Validate Grammar Rules
        errors = self.rules.validate_all(analysis)
        
        # Step 3: Apply Corrections
        corrected_tokens, locks, applied_corrections = GrammarCorrector.apply_grammar_corrections(
            tokens, analysis, errors
        )
        
        # Step 4: Build Response
        response = GrammarCheckResponse(
            sentence=" ".join(tokens),
            errors=[],
            corrected_sentence=" ".join(corrected_tokens) if applied_corrections else None,
        )
        
        # Convert errors to response format
        for error in errors:
            response.errors.append({
                "word": error.word,
                "position": error.position,
                "rule_category": error.error_type,
                "correction": error.expected_form or error.word,
                "explanation": error.explanation,
            })
        
        return response
    
    def analyze_and_debug(self, tokens: List[str]) -> dict:
        """
        Analyze and return detailed debug information.
        
        Useful for understanding what the engine detected.
        
        Returns:
            {
                "tokens": list,
                "analysis": {
                    "subject": SubjectFeatures,
                    "verb": VerbFeatures,
                    "objects": [NounFeatures],
                },
                "errors": [GrammarError],
                "corrections": [...],
            }
        """
        analysis = self.analyzer.analyze(tokens)
        errors = self.rules.validate_all(analysis)
        corrected_tokens, locks, applied = GrammarCorrector.apply_grammar_corrections(
            tokens, analysis, errors
        )
        
        return {
            "tokens": tokens,
            "analysis": {
                "subject": analysis.subject,
                "verb": analysis.verb,
                "objects": analysis.objects,
            },
            "errors": errors,
            "corrections": applied,
            "corrected_tokens": corrected_tokens,
        }


# ─── Function-level API for backward compatibility ─────────────────────

_engine = None


def get_engine() -> LinguisticGrammarEngine:
    """Get or create the singleton grammar engine."""
    global _engine
    if _engine is None:
        _engine = LinguisticGrammarEngine()
    return _engine


def check_grammar(tokens: List[str]) -> GrammarCheckResponse:
    """
    Check grammar for a token list.
    
    Args:
        tokens: List of Telugu words
    
    Returns:
        GrammarCheckResponse
    """
    engine = get_engine()
    return engine.check(tokens)
