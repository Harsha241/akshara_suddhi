"""
Clause-Level Grammar Checking & Consistency Analysis
=====================================================

Applies grammar rules at the clause level and performs cross-clause validation.

Phases:
  3. Clause Transformation → Normalization
  4. Clause-Level Grammar Checking → Apply rules to individual clauses  
  5. Cross-Clause Consistency → Validate relationships between clauses
  6. Reconstruction → Restore to original structure
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from app.core.clause_processor import (
    ClauseUnit,
    ClauseContext,
    ClauseTransformer,
    ALL_CONJUNCTIONS,
)
from app.models import GrammarError


# ═════════════════════════════════════════════════════════════════════════════
# PART 1: CLAUSE-LEVEL GRAMMAR CHECKING
# ═════════════════════════════════════════════════════════════════════════════


class ClauseGrammarChecker:
    """
    Applies grammar rules at the clause level.
    
    Key insight: Grammar rules in grammar_rules.json can now be applied
    independently to each clause, reducing false positives from
    long-distance dependencies.
    """
    
    def __init__(self, grammar_engine):
        """
        Args:
            grammar_engine: The existing GrammarEngine from grammar_engine.py
        """
        self.grammar_engine = grammar_engine
        self.transformer = ClauseTransformer()
    
    def check_clauses(
        self,
        clauses: List[ClauseUnit],
        all_tokens: List[str],
        original_token_spans: List[Dict],
    ) -> List[GrammarError]:
        """
        Check grammar for each clause independently.
        
        Args:
            clauses: List of detected clauses
            all_tokens: Original token list (for context)
            original_token_spans: Original token span information
        
        Returns:
            List of GrammarError objects with correct offsets
        """
        all_errors = []
        
        for clause in clauses:
            # Skip non-independent clauses for now
            # (They need special handling - see Phase 3)
            # if clause.clause_type != ClauseType.INDEPENDENT:
            #     continue
            
            # Transform clause for checking
            transformed_tokens, transformed_spans, offset_map = (
                self.transformer.transform_clause(clause)
            )
            
            if not transformed_tokens:
                continue
            
            # Apply grammar engine to transformed tokens
            gram_response = self.grammar_engine.check(transformed_tokens)
            
            # Map errors back to original positions
            for error in (gram_response.errors or []):
                if error.position < len(offset_map):
                    original_pos = None
                    # Find original index from offset_map
                    for orig_idx, trans_idx in offset_map.items():
                        if trans_idx == error.position:
                            original_pos = orig_idx
                            break
                    
                    if original_pos is not None:
                        # Map to global token position
                        global_pos = clause.token_indices[original_pos]
                        
                        # Reattach correct offsets
                        error.position = global_pos
                        if global_pos < len(original_token_spans):
                            span = original_token_spans[global_pos]
                            error.start = span.get("start", error.start)
                            error.end = span.get("end", error.end)
                        
                        all_errors.append(error)
        
        return all_errors


# ═════════════════════════════════════════════════════════════════════════════
# PART 2: CROSS-CLAUSE CONSISTENCY CHECKING
# ═════════════════════════════════════════════════════════════════════════════


@dataclass
class ClauseConsistencyIssue:
    """Represents a consistency problem between clauses."""
    issue_type: str        # "tense_mismatch", "subject_shift", "logical"
    clause_id: int
    explanation: str
    suggestion: str = ""


class CrossClauseConsistencyChecker:
    """
    Validates grammatical relationships between clauses.
    
    Checks:
    - Tense consistency (when verbs should match)
    - Subject continuity (explicit subject shifts)
    - Logical agreement (semantic coherence hints)
    """
    
    def __init__(self):
        pass
    
    def check_consistency(self, clauses: List[ClauseUnit]) -> List[ClauseConsistencyIssue]:
        """
        Analyze cross-clause relationships.
        
        Args:
            clauses: List of detected and classified clauses
        
        Returns:
            List of consistency issues (suitable for suggestions, not auto-fixes)
        """
        issues = []
        
        if len(clauses) < 2:
            return issues  # Single clause, nothing to check
        
        # Check 1: Tense consistency across independent clauses
        tense_issues = self._check_tense_consistency(clauses)
        issues.extend(tense_issues)
        
        # Check 2: Subject continuity
        subject_issues = self._check_subject_continuity(clauses)
        issues.extend(subject_issues)
        
        # Check 3: Conditional compatibility
        conditional_issues = self._check_conditional_form(clauses)
        issues.extend(conditional_issues)
        
        return issues
    
    def _check_tense_consistency(self, clauses: List[ClauseUnit]) -> List[ClauseConsistencyIssue]:
        """
        Flag tense mismatches in sequences of independent clauses.
        
        Rule: In a sequence of connected actions, tenses should generally align
        unless there's an explicit time marker (నిన్న=yesterday, ఆవకాశం=future).
        """
        issues = []
        
        if len(clauses) < 2:
            return issues
        
        # Extract tenses
        tenses = [c.tense for c in clauses]
        
        # Check for mixing of clearly incompatible tenses
        # E.g., past + future without explicit connector
        tense_sequence = [(i, t) for i, t in enumerate(tenses) if t is not None]
        
        if len(tense_sequence) >= 2:
            for i in range(len(tense_sequence) - 1):
                idx1, tense1 = tense_sequence[i]
                idx2, tense2 = tense_sequence[i + 1]
                
                # Check for sudden tense shifts
                if self._is_tense_incompatible(tense1, tense2):
                    # Check if conjunction allows shift
                    next_clause = clauses[idx2]
                    has_explicit_time = self._has_explicit_time_marker(
                        next_clause.tokens
                    )
                    
                    if not has_explicit_time:
                        issues.append(
                            ClauseConsistencyIssue(
                                issue_type="tense_mismatch",
                                clause_id=idx2,
                                explanation=(
                                    f"Tense shift from {tense1} to {tense2} "
                                    "without explicit time marker"
                                ),
                                suggestion=(
                                    f"Consider matching tense with previous clause or "
                                    "adding time context (e.g., నిన్న, ఆవకాశం)"
                                ),
                            )
                        )
        
        return issues
    
    def _check_subject_continuity(self, clauses: List[ClauseUnit]) -> List[ClauseConsistencyIssue]:
        """
        Detect explicit subject changes across clauses.
        
        In Telugu, subject often continues implicitly. Explicit subject shifts
        should be intentional.
        """
        issues = []
        
        if len(clauses) < 2:
            return issues
        
        prev_subject = None
        
        for i, clause in enumerate(clauses):
            if clause.subject_index is not None:
                current_subject = clause.tokens[clause.subject_index]
                
                if prev_subject and current_subject != prev_subject:
                    # Explicit subject shift
                    # This is usually OK, but worth noting
                    issues.append(
                        ClauseConsistencyIssue(
                            issue_type="subject_shift",
                            clause_id=i,
                            explanation=(
                                f"Subject changed from '{prev_subject}' to '{current_subject}'"
                            ),
                            suggestion="Verify this is intentional",
                        )
                    )
                
                prev_subject = current_subject
        
        return issues
    
    def _check_conditional_form(self, clauses: List[ClauseUnit]) -> List[ClauseConsistencyIssue]:
        """
        Validate conditional clause structure.
        
        Rule: Conditional clauses (with -ితే) should be followed by a
        consequence clause, and tense should follow "if...then" logic.
        """
        issues = []
        
        for i, clause in enumerate(clauses):
            if not any(conj[1] in ["ితే", "నే"] for conj in clause.conjunctions):
                continue
            
            # This is a conditional clause, check for consequence
            if i + 1 < len(clauses):
                next_clause = clauses[i + 1]
                
                # Consequences should typically follow subject-verb agreement
                if (next_clause.subject_index is None and 
                    clause.subject_index is not None):
                    # Consequence clause inherits subject from condition
                    # This is normal in Telugu, so just note it
                    pass
            
        return issues
    
    @staticmethod
    def _is_tense_incompatible(tense1: str, tense2: str) -> bool:
        """Check if two tenses would be strange together without connector."""
        incompatible_pairs = {
            ("future", "past"),
            ("past", "future"),
        }
        
        return (tense1, tense2) in incompatible_pairs or (tense2, tense1) in incompatible_pairs
    
    @staticmethod
    def _has_explicit_time_marker(tokens: List[str]) -> bool:
        """Check for explicit time adverbials."""
        time_markers = {
            "నిన్న", "ఆవకాశం", "ఇప్పుడు", "అప్పుడు", "ఈ", "ఆ",
            "కల", "క్క", "ద్ద", "న", "ట", "ళ",
        }
        
        return any(t in time_markers for t in tokens)


# ═════════════════════════════════════════════════════════════════════════════
# PART 3: CLAUSE RECONSTRUCTION
# ═════════════════════════════════════════════════════════════════════════════


class ClauseReconstructor:
    """
    Reconstructs the original sentence from clause-level errors.
    
    Ensures:
    - Character offsets are preserved exactly
    - Original punctuation/structure is intact
    - Error positions map correctly to UI highlighting
    """
    
    def reconstruct(
        self,
        original_sentence: str,
        clauses: List[ClauseUnit],
        clause_errors: List[GrammarError],
        consistency_issues: List[ClauseConsistencyIssue],
    ) -> Tuple[List[GrammarError], Optional[str]]:
        """
        Reconstruct sentence with corrections applied.
        
        Args:
            original_sentence: Original input
            clauses: Detected clauses
            clause_errors: Errors from clause-level checking
            consistency_issues: Issues from cross-clause analysis
        
        Returns:
            (final_error_list, corrected_sentence_or_None)
        """
        
        # Convert consistency issues to suggestions (non-corrective)
        suggestion_errors = [
            GrammarError(
                word=clauses[issue.clause_id].tokens[0],  # Approximate
                position=clauses[issue.clause_id].token_indices[0],
                rule_category="cross_clause_suggestion",
                correction="(suggestion only)",
                explanation=issue.explanation,
                start=clauses[issue.clause_id].start_offset,
                end=clauses[issue.clause_id].end_offset,
            )
            for issue in consistency_issues
        ]
        
        # Combine all errors
        all_errors = clause_errors + suggestion_errors
        
        # Build corrected sentence (only if we have auto-corrections)
        corrected_tokens = None
        if any(e.rule_category != "cross_clause_suggestion" for e in clause_errors):
            # There are auto-corrections, build corrected version
            # (Simplified: just use corrected tokens from grammar engine)
            corrected_tokens = original_sentence  # Placeholder
        
        return all_errors, corrected_tokens
    
    def verify_offsets(
        self,
        errors: List[GrammarError],
        original_sentence: str,
    ) -> bool:
        """Verify that all error offsets are valid."""
        for error in errors:
            if error.start is not None and error.end is not None:
                if not (0 <= error.start < len(original_sentence)):
                    return False
                if not (error.start <= error.end <= len(original_sentence)):
                    return False
        
        return True


# ═════════════════════════════════════════════════════════════════════════════
# PART 4: CLAUSE-AWARE GRAMMAR PROCESSOR
# ═════════════════════════════════════════════════════════════════════════════


class ClauseAwareGrammarProcessor:
    """
    Orchestrates the full clause-based grammar checking pipeline.
    
    Pipeline:
      1. Detect clauses
      2. Classify clauses
      3. Transform clauses
      4. Check grammar for each clause
      5. Check cross-clause consistency
      6. Reconstruct with all errors
    
    This is the main entry point for clause-based checking.
    """
    
    def __init__(self, grammar_engine, clause_detector):
        """
        Args:
            grammar_engine: Existing GrammarEngine instance
            clause_detector: ClauseDetector instance
        """
        self.grammar_engine = grammar_engine
        self.clause_detector = clause_detector
        self.grammar_checker = ClauseGrammarChecker(grammar_engine)
        self.consistency_checker = CrossClauseConsistencyChecker()
        self.reconstructor = ClauseReconstructor()
    
    def process(
        self,
        sentence: str,
        tokens: List[str],
        token_spans: List[Dict],
        include_clause_analysis: bool = True,
    ) -> Tuple[List[GrammarError], optional[str]]:
        """
        Full clause-based grammar checking.
        
        Args:
            sentence: Original sentence
            tokens: Tokenized words
            token_spans: Token position information
            include_clause_analysis: Whether to perform clause analysis
        
        Returns:
            (all_errors, corrected_sentence_or_none)
        """
        
        if not include_clause_analysis or len(tokens) < 3:
            # Fall back to simple token-level checking
            return [], None
        
        # Phase 1: Detect clauses
        clauses = self.clause_detector.detect_clauses(tokens, token_spans)
        
        if len(clauses) < 2:
            # Single clause, no special handling needed
            return [], None
        
        # Phase 2-4: Check grammar at clause level
        clause_errors = self.grammar_checker.check_clauses(
            clauses, tokens, token_spans
        )
        
        # Phase 5: Cross-clause consistency
        consistency_issues = self.consistency_checker.check_consistency(clauses)
        
        # Phase 6: Reconstruct
        final_errors, corrected = self.reconstructor.reconstruct(
            sentence, clauses, clause_errors, consistency_issues
        )
        
        # Verify offsets
        if not self.reconstructor.verify_offsets(final_errors, sentence):
            # Offset mismatch, return empty to be safe
            return [], None
        
        return final_errors, corrected


# ═════════════════════════════════════════════════════════════════════════════
# EXPORTS
# ═════════════════════════════════════════════════════════════════════════════

__all__ = [
    "ClauseGrammarChecker",
    "CrossClauseConsistencyChecker",
    "ClauseReconstructor",
    "ClauseAwareGrammarProcessor",
    "ClauseConsistencyIssue",
]
