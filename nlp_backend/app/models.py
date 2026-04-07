"""
Pydantic Models — Request / Response Schemas
=============================================
Typed interfaces for all API endpoints with built-in NFC normalization.
"""

import unicodedata
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# ─── Helpers ─────────────────────────────────────────────────────────────

def _nfc(value: str) -> str:
    """Apply Unicode NFC normalization."""
    return unicodedata.normalize("NFC", value.strip())


# ─── Request Models ─────────────────────────────────────────────────────

class SpellCheckRequest(BaseModel):
    word: str = Field(..., max_length=100)
    context: Optional[List[str]] = Field(
        default=None,
        description="Surrounding words for bigram re-ranking",
    )

    @field_validator("word", mode="before")
    @classmethod
    def _norm(cls, v: str) -> str:
        return _nfc(v)


class AutocompleteRequest(BaseModel):
    prefix: str = Field(..., min_length=1, max_length=100)

    @field_validator("prefix", mode="before")
    @classmethod
    def _norm(cls, v: str) -> str:
        return _nfc(v)


class GrammarCheckRequest(BaseModel):
    sentence: str = Field(..., max_length=500)

    @field_validator("sentence", mode="before")
    @classmethod
    def _norm(cls, v: str) -> str:
        return _nfc(v)


class TransliterateRequest(BaseModel):
    text: str = Field(..., max_length=500)

    @field_validator("text", mode="before")
    @classmethod
    def _norm(cls, v: str) -> str:
        return v.strip()


class AutocorrectRequest(BaseModel):
    sentence: str = Field(..., max_length=500)

    @field_validator("sentence", mode="before")
    @classmethod
    def _norm(cls, v: str) -> str:
        return _nfc(v)


# ─── Response Models ────────────────────────────────────────────────────

class SpellSuggestion(BaseModel):
    word: str
    score: float
    frequency: int
    edit_distance: float


class SpellCheckResponse(BaseModel):
    original: str
    is_correct: bool
    suggestions: List[SpellSuggestion]
    is_telugu: bool = True


class AutocompleteSuggestion(BaseModel):
    word: str
    frequency: int


class AutocompleteResponse(BaseModel):
    prefix: str
    suggestions: List[AutocompleteSuggestion]


class GrammarError(BaseModel):
    word: str
    position: int
    rule_category: str
    correction: str
    explanation: str
    start: Optional[int] = None
    end: Optional[int] = None


class GrammarCheckResponse(BaseModel):
    sentence: str
    errors: List[GrammarError]
    corrected_sentence: Optional[str] = None


class TransliterateResponse(BaseModel):
    input_text: str
    output_text: str
    segments: List[dict] = Field(default_factory=list)


class AutocorrectSpan(BaseModel):
    start: int
    end: int
    original: str
    correction: str
    type: str  # "grammar" | "spell"
    stages: List[str] = Field(default_factory=list)


class AutocorrectResponse(BaseModel):
    original_sentence: str
    corrected_sentence: str
    spans: List[AutocorrectSpan] = Field(default_factory=list)
