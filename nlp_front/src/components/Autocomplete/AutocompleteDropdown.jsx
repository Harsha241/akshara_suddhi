import { useEffect, useRef } from "react";

/**
 * AutocompleteDropdown — floating dropdown below the editor
 * showing prefix-matched word completions.
 */
export default function AutocompleteDropdown({ suggestions, onSelect, onDismiss }) {
  const ref = useRef(null);

  // Dismiss on outside click
  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) {
        onDismiss();
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [onDismiss]);

  // Dismiss on Escape
  useEffect(() => {
    const handler = (e) => {
      if (e.key === "Escape") onDismiss();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onDismiss]);

  if (!suggestions.length) return null;

  return (
    <div ref={ref} className="autocomplete-dropdown" id="autocomplete-dropdown">
      <div className="autocomplete-header">
        <span>💡 Suggestions</span>
      </div>
      {suggestions.map((s, i) => (
        <button
          key={i}
          className="autocomplete-item"
          onClick={() => onSelect(s.word)}
        >
          <span className="ac-word">{s.word}</span>
          <span className="ac-freq">{s.frequency.toLocaleString()}</span>
        </button>
      ))}
    </div>
  );
}
