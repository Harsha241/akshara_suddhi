"""
Application Configuration
=========================
Centralizes all configuration constants, paths, and tuning parameters.
"""

from pathlib import Path

# ─── Paths ───────────────────────────────────────────────────────────────
BASE_DIR           = Path(__file__).resolve().parent
DATA_DIR           = BASE_DIR / "data"
DICTIONARY_PATH    = DATA_DIR / "dictionary.json"
UNIGRAMS_PATH      = DATA_DIR / "unigrams.json"
BIGRAMS_PATH       = DATA_DIR / "bigrams.json"
GRAMMAR_RULES_PATH = DATA_DIR / "grammar_rules.json"

# ─── API Limits ──────────────────────────────────────────────────────────
MAX_INPUT_LENGTH = 500   # max characters per API call

# ─── Spell Checker ───────────────────────────────────────────────────────
MAX_EDIT_DISTANCE        = 2
TOP_SPELL_SUGGESTIONS    = 3
FREQ_WEIGHT              = 0.6
PHONETIC_WEIGHT          = 0.4

# ─── Autocomplete ────────────────────────────────────────────────────────
TOP_AUTOCOMPLETE          = 5
MIN_PREFIX_LENGTH         = 2

# ─── N-gram ──────────────────────────────────────────────────────────────
LAPLACE_ALPHA = 1.0

# ─── CORS Origins ────────────────────────────────────────────────────────
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
]
