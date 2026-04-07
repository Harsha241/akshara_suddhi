import { useState, useCallback } from "react";
import { autocomplete } from "../api/client";
import useDebounce from "./useDebounce";

/**
 * Autocomplete hook — triggers after 2+ characters.
 */
export default function useAutocomplete() {
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);

  const doSearch = useCallback(async (prefix) => {
    if (!prefix || prefix.length < 2) { setSuggestions([]); return; }
    setLoading(true);
    try {
      const res = await autocomplete(prefix);
      setSuggestions(res.suggestions || []);
    } catch (err) {
      console.error("Autocomplete error:", err);
      setSuggestions([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const search = useDebounce(doSearch, 400);

  return { suggestions, loading, search, setSuggestions };
}
