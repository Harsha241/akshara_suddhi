import { useState, useCallback } from "react";
import { autocorrect as autocorrectApi } from "../api/client";
import useDebounce from "./useDebounce";

export default function useAutocorrect() {
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState(null);

  const doAnalyze = useCallback(async (sentence) => {
    if (!sentence.trim()) return;
    setLoading(true);
    try {
      const res = await autocorrectApi(sentence);
      setAnalysis(res);
    } catch (err) {
      console.error("Autocorrect error:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  const triggerAnalyze = useDebounce(doAnalyze, 500);

  const correctNow = useCallback(async (sentence) => {
    if (!sentence.trim()) return null;
    setLoading(true);
    try {
      const res = await autocorrectApi(sentence);
      setAnalysis(res);
      return res?.corrected_sentence ?? null;
    } catch (err) {
      console.error("Autocorrect error:", err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { loading, analysis, setAnalysis, triggerAnalyze, correctNow };
}
