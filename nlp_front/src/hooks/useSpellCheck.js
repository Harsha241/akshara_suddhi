import { useState, useCallback } from "react";
import { spellcheck } from "../api/client";
import useDebounce from "./useDebounce";

import { tokenizeWithPositions } from "../utils/telugu";

/**
 * Spell-check every Telugu word in a sentence.
 * Returns { errors, checkSentence(text) }
 */
export default function useSpellCheck() {
  const [errors, setErrors] = useState([]);
  const [loading, setLoading] = useState(false);

  const doCheck = useCallback(async (text) => {
    if (!text.trim()) { setErrors([]); return; }

    setLoading(true);
    try {
      const tokens = tokenizeWithPositions(text);
      const context = [];
      const results = [];

      for (let i = 0; i < tokens.length; i++) {
        const tok = tokens[i];
        const word = tok.text;
        const res = await spellcheck(word, context.length ? [...context] : null);
        if (!res.is_correct && res.is_telugu) {
          results.push({
            ...res,
            type: "spell",
            position: i,
            original: word,
            start: tok.start,
            end: tok.end,
          });
        }
        context.push(word);
        if (context.length > 3) context.shift();
      }
      setErrors(results);
    } catch (err) {
      console.error("SpellCheck error:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  const checkSentence = useDebounce(doCheck, 400);

  return { errors, loading, checkSentence };
}
