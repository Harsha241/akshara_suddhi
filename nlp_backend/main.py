"""
Telugu Smart Writing Assistant — FastAPI Entry Point
=====================================================
Loads all data into memory at startup, constructs NLP engines,
and mounts the four API routers.
"""

import json
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import (
    ALLOWED_ORIGINS,
    BIGRAMS_PATH,
    DICTIONARY_PATH,
    GRAMMAR_RULES_PATH,
    UNIGRAMS_PATH,
)
from app.core.grammar_engine import GrammarEngine
from app.core.ngram import NgramModel
from app.core.spellchecker import SpellChecker
from app.core.transliterator import Transliterator
from app.core.trie import Trie

# ─── Logging ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("telugu-assistant")

# ─── Module-level singletons (populated in lifespan) ─────────────────────
dictionary: dict = {}
trie = Trie()
ngram_model: NgramModel = None  # type: ignore[assignment]
spell_checker: SpellChecker = None  # type: ignore[assignment]
grammar_engine: GrammarEngine = None  # type: ignore[assignment]
transliterator = Transliterator()


def _load_json(path):
    """Load a JSON file and return parsed data."""
    logger.info("Loading %s …", path)
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load all data once at startup; release on shutdown."""
    global dictionary, ngram_model, spell_checker, grammar_engine

    # 1. Dictionary
    dictionary = _load_json(DICTIONARY_PATH)
    logger.info("Dictionary loaded — %d words", len(dictionary))

    # 2. Trie
    trie.build(dictionary)
    logger.info("Trie built")

    # 3. N-gram model
    unigrams = _load_json(UNIGRAMS_PATH)
    bigrams = _load_json(BIGRAMS_PATH)
    ngram_model = NgramModel(unigrams, bigrams)
    logger.info("N-gram model loaded — %d unigrams, %d bigram keys",
                len(unigrams), len(bigrams))

    # 4. Spell checker
    spell_checker = SpellChecker(dictionary, ngram_model)
    logger.info("SpellChecker ready")

    # 5. Grammar engine
    rules = _load_json(GRAMMAR_RULES_PATH)
    grammar_engine = GrammarEngine(rules)
    logger.info("GrammarEngine ready — %d rules", len(rules))

    logger.info("✅  All engines initialised — server ready")
    yield
    logger.info("Shutting down")


# ─── FastAPI application ─────────────────────────────────────────────────
app = FastAPI(
    title="Telugu Smart Writing Assistant",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Mount routers ───────────────────────────────────────────────────────
from app.routes.spellcheck import router as spell_router
from app.routes.autocomplete import router as auto_router
from app.routes.grammar import router as grammar_router
from app.routes.transliterate import router as trans_router
from app.routes.autocorrect import router as autocorrect_router

app.include_router(spell_router, tags=["Spell Check"])
app.include_router(auto_router, tags=["Autocomplete"])
app.include_router(grammar_router, tags=["Grammar"])
app.include_router(trans_router, tags=["Transliteration"])
app.include_router(autocorrect_router, tags=["Autocorrect"])


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "dictionary_size": len(dictionary),
    }
