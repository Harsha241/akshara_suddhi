"""POST /grammar — sentence-level grammar checking."""

from fastapi import APIRouter

from app.core.unicode_utils import tokenize_telugu_with_spans
from app.models import GrammarCheckRequest, GrammarCheckResponse

router = APIRouter()


@router.post("/grammar", response_model=GrammarCheckResponse)
async def grammar_check(req: GrammarCheckRequest):
    """Run suffix-pattern grammar rules on a Telugu sentence."""
    from main import grammar_engine  # deferred import
    from app.core.agreement_postposition import apply_agreement_and_postpositions

    token_spans = tokenize_telugu_with_spans(req.sentence)
    tokens = [t["text"] for t in token_spans]
    tokens2, extra_errors = apply_agreement_and_postpositions(tokens, token_spans=token_spans)
    resp = grammar_engine.check(tokens2)
    # Merge errors from agreement/postposition layer
    resp.errors = [*extra_errors, *(resp.errors or [])]

    # Attach start/end offsets for accurate highlighting in UI
    for err in resp.errors:
        if 0 <= err.position < len(token_spans):
            if err.start is None:
                err.start = token_spans[err.position]["start"]
            if err.end is None:
                err.end = token_spans[err.position]["end"]

    return resp
