"""POST /spellcheck — spell-check a single Telugu word."""

from fastapi import APIRouter, HTTPException

from app.core.unicode_utils import is_english_word, is_punctuation_or_number, is_telugu_word
from app.models import SpellCheckRequest, SpellCheckResponse

router = APIRouter()


@router.post("/spellcheck", response_model=SpellCheckResponse)
async def spellcheck(req: SpellCheckRequest):
    """
    Spell-check a word with optional context for bigram re-ranking.
    Skips English words, punctuation, and numbers.
    """
    from main import spell_checker  # deferred import to avoid circular

    word = req.word

    # Skip non-Telugu tokens
    if is_english_word(word) or is_punctuation_or_number(word):
        return SpellCheckResponse(
            original=word, is_correct=True, suggestions=[], is_telugu=False,
        )

    if not is_telugu_word(word):
        return SpellCheckResponse(
            original=word, is_correct=True, suggestions=[], is_telugu=False,
        )

    return spell_checker.check(word, context=req.context)
