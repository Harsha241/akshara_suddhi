"""
Clause-Based Grammar System
============================

Transforms the grammar checker from token-level to structure-aware clause-based analysis.

Pipeline: Break → Understand → Normalize → Validate → Reconstruct

Key Insight:
Telugu is a free word order language with morphological markers.
Clause boundaries are indicated by:
  - Verb forms and tense markers
  - Conjunctions (కానీ, మరియు, ఎందుకంటే, etc.)
  - Particles and morphological endings
  
NOT by word position.

Author: Grammar Enhancement Layer
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Sequence, Tuple


# ═════════════════════════════════════════════════════════════════════════════
# PART 1: DATA STRUCTURES & TYPE DEFINITIONS
# ═════════════════════════════════════════════════════════════════════════════


class ClauseType(Enum):
    """Classification of clause grammatical functions."""
    INDEPENDENT = "independent"              # Complete meaning, can stand alone
    NON_FINITE_PARTICIPIAL = "non_finite"    # Participial forms, no tense
    INFINITIVAL = "infinitival"              # Purpose/intent expressions
    CONDITIONAL = "conditional"              # "If then" type meaning
    SEQUENTIAL = "sequential"                # Explanatory or continuation
    RELATIVE = "relative"                    # Relative clause (who/which)
    TEMPORAL = "temporal"                    # When/time-based clauses


@dataclass
class TokenSpanInfo:
    """Information about a token's location in the original sentence."""
    index: int                 # Position in token list
    text: str                  # Token text
    start: int                 # Character offset start
    end: int                   # Character offset end
    is_verb: bool = False      # Is this a verbal form?
    is_conjunction: bool = False  # Is this a conjunction?
    is_subject: bool = False   # Is this a subject pronoun?


@dataclass
class ClauseUnit:
    """Represents a single clause with complete metadata."""
    # Identity
    clause_id: int
    clause_type: ClauseType
    
    # Token composition
    token_indices: List[int]        # Positions in original token list
    tokens: List[str]               # Actual token texts
    token_spans: List[TokenSpanInfo]  # Full token info with offsets
    
    # Linguistic properties
    subject_index: Optional[int] = None     # Token index of subject (if present)
    main_verb_index: Optional[int] = None   # Token index of main verb
    conjunctions: List[Tuple[int, str]] = field(default_factory=list)  # (idx, text)
    
    # Character-level offsets
    start_offset: int = 0     # First character of clause
    end_offset: int = 0       # Last character of clause
    
    # Metadata
    is_subject_implicit: bool = False  # Subject inferred from context?
    tense: Optional[str] = None        # Detected tense
    confidence: float = 1.0             # Clause boundary confidence


@dataclass
class ClauseContext:
    """Cross-clause context for consistency checks."""
    clauses: List[ClauseUnit]
    sentence: str
    all_tokens: List[str]
    all_token_spans: List[TokenSpanInfo]
    
    tenses: Dict[int, str] = field(default_factory=dict)      # clause_id -> tense
    subjects: Dict[int, str] = field(default_factory=dict)    # clause_id -> subject
    

# ═════════════════════════════════════════════════════════════════════════════
# PART 2: CONJUNCTION & MARKER DETECTION
# ═════════════════════════════════════════════════════════════════════════════

# Telugu narrative conjunctions that split independent clauses
INDEPENDENT_CONJUNCTIONS = {
    "కానీ": "but/however",
    "అయితే": "but/however",
    "కాని": "but",
    "మరియు": "and",
    "పక్కా": "but/definitely",
    "లేదా": "or",
}

# Dependent/sequential conjunctions that may keep clauses together
DEPENDENT_CONJUNCTIONS = {
    "ఎందుకంటే": "because",
    "ఎందుకన": "because",
    "కాబట్టి": "therefore/so",
    "అందువల్ల": "therefore",
    "అందువలన": "therefore",
    "అందుకే": "that's why",
}

# All conjunctions (for faster lookup)
ALL_CONJUNCTIONS = {**INDEPENDENT_CONJUNCTIONS, **DEPENDENT_CONJUNCTIONS}

# Verbal markers that often indicate clause boundaries
VERB_ENDING_PATTERNS = {
    # Past tense
    "past": re.compile(r"(ాడు|ింది|ారు|ాను|ాము|ావు)$"),
    # Present continuous
    "present_cont": re.compile(r"(తున్నాడు|తున్నది|తున్నారు|తున్నాను|తున్నాము|తున్నావు|తోంది)$"),
    # Future
    "future": re.compile(r"(తాడు|తుంది|తారు|తాను|తాము|తావు)$"),
    # Conditional (-ితే, -నే type)
    "conditional": re.compile(r"(ితే|నే)$"),
    # Infinitive / non-finite forms
    "infinitive": re.compile(r"(ట|టమని|టానికి|టకు)$"),
}

# Participial forms (non-finite, indicate dependent clauses)
PARTICIPIAL_PATTERNS = {
    "past_participle": re.compile(r"(ిన|చిన|సిన)$"),  # -ina form
    "present_participle": re.compile(r"(ుతూ|తూ|గా)$"),    # -utu form
    "verbal_noun": re.compile(r"(టం|టము|దం)$"),          # -tam form
}

# Subject pronouns that establish clause subjects
SUBJECT_PRONOUNS = {
    "నేను", "నీవు", "నువ్వు", "అతను", "ఆమె", "ఇది", "అది",
    "వారు", "వాళ్లు", "మీర", "మీరు", "మనం", "మనము", "మీకు",
}


# ═════════════════════════════════════════════════════════════════════════════
# PART 3: CLAUSE DETECTION ENGINE
# ═════════════════════════════════════════════════════════════════════════════

class ClauseDetector:
    """Detects clause boundaries in Telugu sentences."""
    
    def __init__(self):
        self.conjunctions = ALL_CONJUNCTIONS
        self.verb_patterns = VERB_ENDING_PATTERNS
        self.participial_patterns = PARTICIPIAL_PATTERNS
        self.subjects = SUBJECT_PRONOUNS
        
    def detect_clauses(
        self, 
        tokens: List[str], 
        token_spans: List[Dict],
    ) -> List[ClauseUnit]:
        """
        Detect and segment clauses from a token sequence.
        
        Args:
            tokens: List of tokenized words
            token_spans: List of dicts with {'text', 'start', 'end'} for each token
        
        Returns:
            List of ClauseUnit objects representing detected clauses
        """
        
        if not tokens:
            return []
        
        # Enrich token info with linguistic properties
        Token_infos = self._enrich_token_info(tokens, token_spans)
        
        # Detect conjunction positions (primary clause boundaries)
        conjunction_positions = self._find_conjunctions(tokens)
        
        # Detect verbal boundaries (secondary boundaries)
        verb_positions = self._find_verbs(tokens)
        
        # Detect subject positions
        subject_positions = self._find_subjects(tokens)
        
        # Build clause boundaries
        boundaries = self._compute_boundaries(
            tokens, 
            conjunction_positions, 
            verb_positions,
            subject_positions
        )
        
        # Create clause units
        clauses = self._build_clause_units(
            tokens,
            Token_infos,
            boundaries,
            conjunction_positions,
            verb_positions,
            subject_positions
        )
        
        return clauses
    
    def _enrich_token_info(
        self, 
        tokens: List[str], 
        token_spans: List[Dict]
    ) -> List[TokenSpanInfo]:
        """Add linguistic properties to each token."""
        infos = []
        for i, (token, span) in enumerate(zip(tokens, token_spans)):
            info = TokenSpanInfo(
                index=i,
                text=token,
                start=span.get("start", 0),
                end=span.get("end", len(token)),
            )
            # Check if verb
            for pattern in self.verb_patterns.values():
                if pattern.search(token):
                    info.is_verb = True
                    break
            
            # Check if conjunction
            if token in self.conjunctions:
                info.is_conjunction = True
            
            # Check if subject
            if token in self.subjects:
                info.is_subject = True
            
            infos.append(info)
        
        return infos
    
    def _find_conjunctions(self, tokens: List[str]) -> List[int]:
        """Find positions of conjunctions in token list."""
        positions = []
        for i, token in enumerate(tokens):
            if token in self.conjunctions:
                positions.append(i)
        return positions
    
    def _find_verbs(self, tokens: List[str]) -> Dict[int, str]:
        """Map token positions to detected tense/verb type."""
        verb_map = {}
        for i, token in enumerate(tokens):
            for tense_name, pattern in self.verb_patterns.items():
                if pattern.search(token):
                    verb_map[i] = tense_name
                    break
            # Also check participial forms
            for ptype, pattern in self.participial_patterns.items():
                if pattern.search(token):
                    verb_map[i] = ptype  # non-finite
                    break
        return verb_map
    
    def _find_subjects(self, tokens: List[str]) -> List[int]:
        """Find positions of subject pronouns."""
        positions = []
        for i, token in enumerate(tokens):
            if token in self.subjects:
                positions.append(i)
        return positions
    
    def _compute_boundaries(
        self,
        tokens: List[str],
        conjunction_positions: List[int],
        verb_positions: Dict[int, str],
        subject_positions: List[int],
    ) -> List[Tuple[int, int]]:
        """
        Compute clause boundaries as (start_idx, end_idx) pairs.
        
        Strategy:
        1. Primary: Split on independent conjunctions
        2. Secondary: Split on consecutive main verbs (when no conjunction)
        3. Constraint: Preserve participial forms within their parent clause
        """
        if not tokens:
            return []
        
        # Start with conjunction-based splitting (most reliable)
        split_points = [0] + [i + 1 for i in conjunction_positions] + [len(tokens)]
        split_points = sorted(set(split_points))
        
        boundaries = []
        for i in range(len(split_points) - 1):
            start = split_points[i]
            end = split_points[i + 1]
            if start < end:
                boundaries.append((start, end))
        
        # Post-process: Check if we have multiple main verbs in one segment
        # If so, and no conjunction separates them, keep them together
        # (Let cross-clause analysis handle it later)
        
        return boundaries
    
    def _build_clause_units(
        self,
        tokens: List[str],
        token_infos: List[TokenSpanInfo],
        boundaries: List[Tuple[int, int]],
        conjunction_positions: List[int],
        verb_positions: Dict[int, str],
        subject_positions: List[int],
    ) -> List[ClauseUnit]:
        """Construct ClauseUnit objects from detected boundaries."""
        clauses = []
        
        for clause_id, (start_idx, end_idx) in enumerate(boundaries):
            clause_tokens = tokens[start_idx:end_idx]
            clause_spans = token_infos[start_idx:end_idx]
            clause_token_indices = list(range(start_idx, end_idx))
            
            # Determine clause type
            clause_type = self._classify_clause(
                clause_tokens,
                clause_spans,
                verb_positions,
                conjunction_positions,
                start_idx,
                end_idx,
            )
            
            # Find subject in this clause
            subject_idx = None
            for pos in subject_positions:
                if start_idx <= pos < end_idx:
                    subject_idx = pos - start_idx
                    break
            
            # Find main verb in this clause
            main_verb_idx = None
            for i, idx in enumerate(clause_token_indices):
                if idx in verb_positions:
                    main_verb_idx = i
                    break
            
            # Extract conjunctions in this clause
            conjunctions = []
            for i, idx in enumerate(clause_token_indices):
                if idx in conjunction_positions:
                    conjunctions.append((i, tokens[idx]))
            
            # Character offsets
            start_offset = clause_spans[0].start if clause_spans else 0
            end_offset = clause_spans[-1].end if clause_spans else 0
            
            # Detect tense
            tense = self._detect_tense(clause_tokens, verb_positions)
            
            clause = ClauseUnit(
                clause_id=clause_id,
                clause_type=clause_type,
                token_indices=clause_token_indices,
                tokens=clause_tokens,
                token_spans=clause_spans,
                subject_index=subject_idx,
                main_verb_index=main_verb_idx,
                conjunctions=conjunctions,
                start_offset=start_offset,
                end_offset=end_offset,
                tense=tense,
            )
            
            clauses.append(clause)
        
        return clauses
    
    def _classify_clause(
        self,
        tokens: List[str],
        token_spans: List[TokenSpanInfo],
        verb_positions: Dict[int, str],
        conjunction_positions: List[int],
        start_idx: int,
        end_idx: int,
    ) -> ClauseType:
        """Determine the grammatical type of a clause."""
        
        # Check for participial/non-finite forms
        has_finite_verb = False
        has_participle = False
        
        for idx in range(start_idx, end_idx):
            if idx in verb_positions:
                verb_type = verb_positions[idx]
                if verb_type in ["past", "present_cont", "future"]:
                    has_finite_verb = True
                elif "participle" in verb_type or "infinitive" in verb_type or "noun" in verb_type:
                    has_participle = True
        
        # Check for relative clause markers
        has_relative_marker = any(
            t in tokens for t in ["ఎవరు", "ఏది", "ఎక్కడ", "ఎప్పుడు"]
        )
        
        # Check for conditional markers (-ితే, -నే)
        has_conditional = any("-ితే" in t or "-నే" in t for t in tokens)
        
        # Classify
        if has_conditional:
            return ClauseType.CONDITIONAL
        elif has_relative_marker:
            return ClauseType.RELATIVE
        elif not has_finite_verb and has_participle:
            return ClauseType.NON_FINITE_PARTICIPIAL
        elif has_finite_verb:
            return ClauseType.INDEPENDENT
        else:
            return ClauseType.SEQUENTIAL
    
    def _detect_tense(
        self, 
        tokens: List[str],
        verb_positions: Dict[int, str],
    ) -> Optional[str]:
        """Determine predominant tense in clause."""
        tenses = []
        for token in tokens:
            for tense_name, pattern in self.verb_patterns.items():
                if pattern.search(token):
                    tenses.append(tense_name)
                    break
        
        if tenses:
            # Return most common tense
            from collections import Counter
            return Counter(tenses).most_common(1)[0][0]
        
        return None


# ═════════════════════════════════════════════════════════════════════════════
# PART 4: CLAUSE TRANSFORMER
# ═════════════════════════════════════════════════════════════════════════════

class ClauseTransformer:
    """
    Normalizes clauses into forms suitable for grammar rule application.
    
    Strategy: Remove morphological/structural elements that prevent rule matching,
    while maintaining accurate offset mapping back to original.
    """
    
    def transform_clause(
        self,
        clause: ClauseUnit,
    ) -> Tuple[List[str], List[TokenSpanInfo], Dict[int, int]]:
        """
        Transform a clause for grammar checking.
        
        Returns:
            (transformed_tokens, transformed_spans, offset_map)
            where offset_map[original_idx] = transformed_idx (or -1 if removed)
        """
        transformed_tokens = []
        transformed_spans = []
        offset_map = {}
        
        for orig_idx, token in enumerate(clause.tokens):
            # Skip pure conjunctions at clause start (already handled by segmentation)
            if orig_idx == 0 and token in ALL_CONJUNCTIONS:
                offset_map[orig_idx] = -1
                continue
            
            # Keep everything else
            transformed_tokens.append(token)
            transformed_spans.append(clause.token_spans[orig_idx])
            offset_map[orig_idx] = len(transformed_tokens) - 1
        
        return transformed_tokens, transformed_spans, offset_map
    
    def infer_subject(
        self,
        clause: ClauseUnit,
        previous_clause: Optional[ClauseUnit] = None,
    ) -> Optional[str]:
        """
        Infer subject if the clause lacks one (common in Tamil, Telugu).
        
        Uses simple heuristic: copy subject from previous clause.
        """
        if clause.subject_index is not None:
            # Has explicit subject
            return clause.tokens[clause.subject_index]
        
        if previous_clause and previous_clause.subject_index is not None:
            # Copy from previous clause
            subject = previous_clause.tokens[previous_clause.subject_index]
            return subject
        
        return None


# ═════════════════════════════════════════════════════════════════════════════
# PART 5: EXPORTS
# ═════════════════════════════════════════════════════════════════════════════

__all__ = [
    "ClauseType",
    "TokenSpanInfo",
    "ClauseUnit",
    "ClauseContext",
    "ClauseDetector",
    "ClauseTransformer",
    "ALL_CONJUNCTIONS",
    "SUBJECT_PRONOUNS",
    "VERB_ENDING_PATTERNS",
    "PARTICIPIAL_PATTERNS",
]
