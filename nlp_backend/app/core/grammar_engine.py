"""
Grammar Rule Engine (rule-based, safe + extensible)
==================================================
This engine applies `app/data/grammar_rules.json` deterministically.

Supported rule features:
- **token_suffix rules** (default): pattern is applied as a suffix (pattern + "$")
- **sentence rules**: patterns containing whitespace OR explicit anchors (^ or $)
- **preceding** / **following** constraints (token-level only)
- **condition**: currently supports `contains('...')` / `contains("...")`
- **priority**: optional integer; lower runs earlier (default 100)

Important:
- Subject–verb agreement + postposition insertion is handled *before* this engine
  by `app.core.agreement_postposition` in the API routes.
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple

from app.models import GrammarCheckResponse, GrammarError


class GrammarEngine:
    # Suffix patterns that signal a particular tense (diagnostic only)
    _TENSE_SUFFIXES = {
        "past": re.compile(r"(ాడు|ింది|ారు|ాను|ాము|ావు|ిన|చ్చి)$"),
        "present": re.compile(
            r"(తున్నాడు|తున్నది|తున్నారు|తున్నాను|తున్నాము|తున్నావు|తోంది)$"
        ),
        "future": re.compile(r"(తాడు|తుంది|తారు|తాను|తాము|తావు)$"),
    }

    def __init__(self, rules: List[Dict]):
        self.rules: List[Dict] = []
        for r in rules:
            rr = dict(r)
            pat_src = str(rr.get("pattern", "")).strip()
            rr["_priority"] = int(rr.get("priority", 100))

            # Scope selection
            is_sentence = bool(re.search(r"\s", pat_src)) or pat_src.startswith("^") or pat_src.endswith("$")
            rr["_scope"] = "sentence" if is_sentence else "token_suffix"
            rr["_pat"] = re.compile(pat_src) if is_sentence else re.compile(pat_src + "$")

            if rr.get("preceding"):
                rr["_pre"] = re.compile(str(rr["preceding"]) + "$")
            if rr.get("following"):
                rr["_fol"] = re.compile("^" + str(rr["following"]))

            rr["_cond_contains"] = None
            if rr.get("condition"):
                m = re.fullmatch(
                    r"contains\((['\"])(.+)\1\)", str(rr["condition"]).strip()
                )
                rr["_cond_contains"] = m.group(2) if m else None

            self.rules.append(rr)

        # Lower priority first
        self.rules.sort(key=lambda x: x["_priority"])

    def check(self, tokens: List[str]) -> GrammarCheckResponse:
        errors: List[GrammarError] = []
        corrected = list(tokens)
        sentence = " ".join(corrected)

        # Pass 1: conservative sentence-level rewrites
        corrected, sentence, e1 = self._apply_sentence_rules(corrected, sentence)
        errors.extend(e1)

        # Pass 2: token-level suffix rules
        e2 = self._apply_token_suffix_rules(corrected, sentence)
        errors.extend(e2)

        # Pass 3: tense consistency diagnostics (no auto-fix)
        errors.extend(self._check_tense_consistency(corrected))

        return GrammarCheckResponse(
            sentence=" ".join(tokens),
            errors=errors,
            corrected_sentence=" ".join(corrected) if errors else None,
        )

    def _rule_category(self, rule: Dict) -> str:
        return str(rule.get("context") or rule.get("type") or "rule")

    def _apply_sentence_rules(
        self, tokens: List[str], sentence: str
    ) -> Tuple[List[str], str, List[GrammarError]]:
        out = list(tokens)
        s = sentence
        errors: List[GrammarError] = []

        for rule in self.rules:
            if rule["_scope"] != "sentence":
                continue

            cond = rule.get("_cond_contains")
            if cond and cond not in s:
                continue

            if not rule["_pat"].search(s):
                continue

            new_s = rule["_pat"].sub(str(rule.get("correction", "")), s)
            if new_s == s:
                continue

            # Keep token indices stable for downstream offset mapping
            old_parts = s.split()
            new_parts = new_s.split()
            if len(old_parts) != len(new_parts):
                continue

            for i, (a, b) in enumerate(zip(old_parts, new_parts)):
                if a == b:
                    continue
                out[i] = b
                errors.append(
                    GrammarError(
                        word=a,
                        position=i,
                        rule_category=self._rule_category(rule),
                        correction=b,
                        explanation=str(rule.get("explanation", "")),
                    )
                )

            s = " ".join(out)

        return out, s, errors

    def _apply_token_suffix_rules(self, tokens: List[str], sentence: str) -> List[GrammarError]:
        errors: List[GrammarError] = []

        for idx, word in enumerate(tokens):
            for rule in self.rules:
                if rule["_scope"] != "token_suffix":
                    continue

                cond = rule.get("_cond_contains")
                if cond and cond not in sentence:
                    continue

                if not rule["_pat"].search(word):
                    continue

                if "_pre" in rule:
                    if idx == 0 or not rule["_pre"].search(tokens[idx - 1]):
                        continue
                if "_fol" in rule:
                    if idx + 1 >= len(tokens) or not rule["_fol"].search(tokens[idx + 1]):
                        continue

                new_word = rule["_pat"].sub(str(rule.get("correction", "")), word)
                if new_word == word:
                    continue

                tokens[idx] = new_word
                errors.append(
                    GrammarError(
                        word=word,
                        position=idx,
                        rule_category=self._rule_category(rule),
                        correction=new_word,
                        explanation=str(rule.get("explanation", "")),
                    )
                )
                break  # one rule per token

        return errors

    def _check_tense_consistency(self, tokens: List[str]) -> List[GrammarError]:
        tense_map: Dict[int, str] = {}
        for idx, tok in enumerate(tokens):
            for tense, pat in self._TENSE_SUFFIXES.items():
                if pat.search(tok):
                    tense_map[idx] = tense
                    break

        if len(tense_map) < 2:
            return []

        counts: Dict[str, int] = {}
        for t in tense_map.values():
            counts[t] = counts.get(t, 0) + 1
        majority = max(counts, key=counts.get)

        errors: List[GrammarError] = []
        for idx, tense in tense_map.items():
            if tense == majority:
                continue
            errors.append(
                GrammarError(
                    word=tokens[idx],
                    position=idx,
                    rule_category="tense_consistency",
                    correction=tokens[idx],
                    explanation=(
                        f"This word appears to be {tense} tense, "
                        f"but the sentence is mostly {majority} tense."
                    ),
                )
            )
        return errors

