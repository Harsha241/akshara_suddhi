"""POST /transliterate — Romanised Telugu to Telugu script."""

from fastapi import APIRouter

from app.models import TransliterateRequest, TransliterateResponse

router = APIRouter()


@router.post("/transliterate", response_model=TransliterateResponse)
async def transliterate(req: TransliterateRequest):
    """Convert Romanised Telugu to Telugu Unicode script."""
    from main import transliterator  # deferred import

    output, segments = transliterator.convert_with_segments(req.text)

    return TransliterateResponse(
        input_text=req.text,
        output_text=output,
        segments=segments,
    )
