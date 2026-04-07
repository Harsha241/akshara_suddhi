"""POST /autocomplete — prefix-based Telugu word completion."""

from fastapi import APIRouter

from app.config import MIN_PREFIX_LENGTH, TOP_AUTOCOMPLETE
from app.models import AutocompleteRequest, AutocompleteResponse, AutocompleteSuggestion

router = APIRouter()


@router.post("/autocomplete", response_model=AutocompleteResponse)
async def autocomplete(req: AutocompleteRequest):
    """Return top-K completions for a Telugu prefix."""
    from main import trie  # deferred import

    prefix = req.prefix

    if len(prefix) < MIN_PREFIX_LENGTH:
        return AutocompleteResponse(prefix=prefix, suggestions=[])

    results = trie.prefix_search(prefix, top_k=TOP_AUTOCOMPLETE)

    return AutocompleteResponse(
        prefix=prefix,
        suggestions=[
            AutocompleteSuggestion(word=w, frequency=f) for w, f in results
        ],
    )
