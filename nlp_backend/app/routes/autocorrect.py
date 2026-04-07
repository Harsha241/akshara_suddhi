"""POST /autocorrect — Full autocorrect pipeline."""

from fastapi import APIRouter
import re
from app.models import AutocorrectRequest, AutocorrectResponse, AutocorrectSpan

router = APIRouter()

@router.post("/autocorrect", response_model=AutocorrectResponse)
async def autocorrect_sentence(req: AutocorrectRequest):
    """
    Run the full text-correction pipeline:
    Input sentence -> Tokenize -> Detect subject -> Apply grammar rules -> Then apply spell correction -> Then use bigram ranking
    """
    from main import grammar_engine, spell_checker, dictionary
    from app.core.unicode_utils import is_english_word, is_punctuation_or_number, is_telugu_word
    from app.core.boundary_recovery import recover_word_boundaries
    from app.core.agreement_postposition import apply_agreement_and_postpositions

    sentence = req.sentence
    
    # Tokenize keeping spaces and punctuation intact for reconstruction
    # The regex chunks the text into: Telugu words, English words, Numbers, individual punctuation, or whitespace blocks.
    regex = re.compile(r'([\u0C00-\u0C7F]+|[a-zA-Z]+|[0-9]+|[^\s\u0C00-\u0C7Fa-zA-Z0-9]+|\s+)')
    parts = []
    part_spans = []
    for m in regex.finditer(sentence):
        parts.append(m.group(0))
        part_spans.append((m.start(), m.end()))

    token_indices = []
    tokens = []
    
    for i, part in enumerate(parts):
        # Skip if whitespace or punctuation
        if not part.strip() or re.match(r'^[^\s\u0C00-\u0C7Fa-zA-Z0-9]+$', part):
            continue
        token_indices.append(i)
        tokens.append(part)

    if not tokens:
        return AutocorrectResponse(
            original_sentence=sentence,
            corrected_sentence=sentence,
            spans=[],
        )

    # NEW: Word boundary recovery / decomposition (before grammar/spell)
    # Note: if a token splits into multiple tokens, original offsets no longer map 1:1.
    did_recover = False
    recovered_tokens = []
    for t in tokens:
        if is_telugu_word(t) and t not in dictionary:
            rec = recover_word_boundaries(t)
            if len(rec) > 1:
                did_recover = True
            recovered_tokens.extend(rec)
        else:
            recovered_tokens.append(t)

    tokens = recovered_tokens

    # NEW: Subject–verb agreement + postposition insertion (before grammar rules)
    tokens, agree_errors = apply_agreement_and_postpositions(tokens, token_spans=None)

    # Step: Detect subject & Apply grammar rules
    # This automatically updates Telugu suffixes based on subject detection from grammar_engine
    grammar_resp = grammar_engine.check(tokens)

    gram_tokens = list(tokens)
    stages_by_idx = {i: [] for i in range(len(tokens))}

    # Track agreement/postposition changes as grammar stage
    for err in agree_errors:
        if 0 <= err.position < len(gram_tokens) and gram_tokens[err.position] == err.word:
            gram_tokens[err.position] = err.correction
            stages_by_idx[err.position].append("grammar")

    # Apply grammar corrections deterministically using the returned error positions
    for err in getattr(grammar_resp, "errors", []) or []:
        if 0 <= err.position < len(gram_tokens) and gram_tokens[err.position] == err.word:
            gram_tokens[err.position] = err.correction
            stages_by_idx[err.position].append("grammar")

    # Step: Apply spell correction & Bigram ranking
    context = []
    final_tokens = []
    spans = []

    for i, word in enumerate(gram_tokens):
        if is_english_word(word) or is_punctuation_or_number(word) or not is_telugu_word(word):
            final_tokens.append(word)
            context.append(word)
            if len(context) > 3: context.pop(0)
            continue
        
        # spell_checker applies bigram ranking internally if context is passed
        spell_resp = spell_checker.check(word, context=context if context else None)
        
        if not spell_resp.is_correct and spell_resp.suggestions:
            best_suggestion = spell_resp.suggestions[0].word
            final_tokens.append(best_suggestion)
            context.append(best_suggestion)
            if best_suggestion != word:
                stages_by_idx[i].append("spell")
        else:
            final_tokens.append(word)
            context.append(word)
            
        if len(context) > 3: context.pop(0)

    # Build spans relative to the original sentence only when we did not split tokens.
    if not did_recover:
        for idx_in_list, part_index in enumerate(token_indices):
            original_word = tokens[idx_in_list]
            corrected_word = final_tokens[idx_in_list]
            if corrected_word == original_word:
                continue
            start, end = part_spans[part_index]
            stages = stages_by_idx.get(idx_in_list, [])
            span_type = "spell" if "spell" in stages else "grammar"
            spans.append(
                AutocorrectSpan(
                    start=start,
                    end=end,
                    original=original_word,
                    correction=corrected_word,
                    type=span_type,
                    stages=stages,
                )
            )

    # Reconstruct the string
    if not did_recover:
        for idx_in_list, part_index in enumerate(token_indices):
            parts[part_index] = final_tokens[idx_in_list]
        corrected_sentence = "".join(parts)
    else:
        # Whitespace-normalized reconstruction when boundary recovery changed token count
        corrected_sentence = " ".join(final_tokens)

    return AutocorrectResponse(
        original_sentence=sentence,
        corrected_sentence=corrected_sentence,
        spans=spans,
    )
