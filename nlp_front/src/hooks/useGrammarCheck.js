import { useState, useCallback } from "react";
import { grammarCheck } from "../api/client";
import useDebounce from "./useDebounce";

/**
 * Grammar check hook — sends full sentence.
 */
export default function useGrammarCheck() {
  const [errors, setErrors] = useState([]);
  const [corrected, setCorrected] = useState(null);
  const [loading, setLoading] = useState(false);

  const doCheck = useCallback(async (sentence) => {
    if (!sentence.trim()) { setErrors([]); setCorrected(null); return; }
    setLoading(true);
    try {
      const res = await grammarCheck(sentence);
      setErrors(res.errors || []);
      setCorrected(res.corrected_sentence || null);
    } catch (err) {
      console.error("Grammar error:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  const check = useDebounce(doCheck, 400);

  return { errors, corrected, loading, check };
}
