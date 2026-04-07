import { useState, useRef, useCallback, useMemo } from "react";
import { getCurrentWord } from "../../utils/telugu";
import useAutocomplete from "../../hooks/useAutocomplete";
import useAutocorrect from "../../hooks/useAutocorrect";
import useSpellCheck from "../../hooks/useSpellCheck";
import useGrammarCheck from "../../hooks/useGrammarCheck";
import AutocompleteDropdown from "../Autocomplete/AutocompleteDropdown";
import SuggestionPopover from "./SuggestionPopover";

/**
 * Main Telugu text editor with inline error highlights
 * and live autocomplete / suggestion popovers.
 */
export default function TeluguEditor() {
  const [text, setText] = useState("");
  const [cursorPos, setCursorPos] = useState(0);
  const [selectedError, setSelectedError] = useState(null);
  const [popoverPos, setPopoverPos] = useState(null);
  const textareaRef = useRef(null);

  const {
    suggestions: autoSuggestions,
    search: searchAuto,
    setSuggestions: setAutoSuggestions,
  } = useAutocomplete();
  
  const { setAnalysis, triggerAnalyze } = useAutocorrect();
  const { errors: spellErrors, checkSentence: checkSpelling } = useSpellCheck();
  const { errors: grammarErrors, check: checkGrammar } = useGrammarCheck();
  const spellingFromGrammar = useMemo(() => {
    // Treat "common_error" (e.g., వెల్లాను -> వెళ్లాను) as spelling in UI
    return (grammarErrors || []).filter((e) => e.rule_category === "common_error");
  }, [grammarErrors]);

  const mergedSpans = useMemo(() => {
    const spans = [];
    for (const e of grammarErrors || []) {
      if (typeof e.start !== "number" || typeof e.end !== "number") continue;
      const t = e.rule_category === "common_error" ? "spell" : "grammar";
      spans.push({ ...e, type: t });
    }
    for (const e of spellErrors || []) spans.push(e);

    spans.sort((a, b) => (a.start ?? 0) - (b.start ?? 0));
    // remove overlaps (prefer spelling when overlapping)
    const out = [];
    let lastEnd = -1;
    for (const sp of spans) {
      if (sp.start == null || sp.end == null) continue;
      if (sp.start < lastEnd) continue;
      out.push(sp);
      lastEnd = sp.end;
    }
    return out;
  }, [grammarErrors, spellErrors]);

  // ── Handle text change ───────────────────────────────────────────────
  const handleChange = useCallback(
    (e) => {
      const value = e.target.value;
      if (value.length > 500) return; // max input limit

      setText(value);
      const pos = e.target.selectionStart;
      setCursorPos(pos);

      // Analyze the sentence (do NOT auto-replace while typing)
      triggerAnalyze(value);
      checkSpelling(value);
      checkGrammar(value);

      // Autocomplete — current word prefix
      const { prefix } = getCurrentWord(value, pos);
      if (prefix.length >= 2) {
        searchAuto(prefix);
      } else {
        setAutoSuggestions([]);
      }
    },
    [searchAuto, setAutoSuggestions, triggerAnalyze, checkSpelling, checkGrammar]
  );

  // ── Handle cursor movement (for autocomplete refresh) ────────────────
  const handleSelect = useCallback(
    (e) => {
      const pos = e.target.selectionStart;
      setCursorPos(pos);

      // If cursor is inside an error span, show popover near editor.
      const hit =
        mergedSpans.find((sp) => pos >= sp.start && pos <= sp.end) || null;
      setSelectedError(hit);
      if (hit && textareaRef.current) {
        const r = textareaRef.current.getBoundingClientRect();
        setPopoverPos({ top: r.bottom + 8, left: r.left + 16 });
      } else {
        setPopoverPos(null);
      }
    },
    [mergedSpans]
  );

  // ── Apply autocomplete suggestion ────────────────────────────────────
  const applyAutocomplete = useCallback(
    (word) => {
      const { start, end } = getCurrentWord(text, cursorPos);
      const newText = text.slice(0, start) + word + " " + text.slice(end);
      setText(newText);
      setAutoSuggestions([]);

      // Re-analyze after applying autocomplete
      setAnalysis(null);
      triggerAnalyze(newText);
      checkSpelling(newText);
      checkGrammar(newText);

      // Move cursor
      const newPos = start + word.length + 1;
      setTimeout(() => {
        textareaRef.current?.setSelectionRange(newPos, newPos);
        textareaRef.current?.focus();
      }, 0);
    },
    [text, cursorPos, setAutoSuggestions, setAnalysis, triggerAnalyze, checkSpelling, checkGrammar]
  );

  const hasFixes = Boolean(text.trim() && mergedSpans.length);
  const grammarIssues = (grammarErrors || []).filter(
    (e) =>
      e.rule_category !== "common_error" &&
      typeof e.start === "number" &&
      typeof e.end === "number"
  );
  const spellingIssues = [...(spellErrors || []), ...spellingFromGrammar];

  const previewNodes = useMemo(() => {
    if (!text) return [""];
    if (!mergedSpans.length) return [text];

    const nodes = [];
    let cursor = 0;
    for (let i = 0; i < mergedSpans.length; i++) {
      const sp = mergedSpans[i];
      const start = Math.max(0, Math.min(text.length, sp.start ?? 0));
      const end = Math.max(0, Math.min(text.length, sp.end ?? 0));
      if (start > cursor) nodes.push(text.slice(cursor, start));

      const cls = sp.type === "grammar" ? "error-grammar" : "error-spell";
      nodes.push(
        <span key={`err-${i}`} className={cls}>
          {text.slice(start, end)}
        </span>
      );
      cursor = end;
    }
    if (cursor < text.length) nodes.push(text.slice(cursor));
    return nodes;
  }, [text, mergedSpans]);

  const charCount = text.length;

  return (
    <div className="editor-container">
      {/* Header */}
      <div className="editor-header">
        <h2>తెలుగు రాయండి</h2>
        <span className={`char-count ${charCount > 450 ? "warn" : ""}`}>
          {charCount}/500
        </span>
      </div>

      {/* Editor area */}
      <div className="editor-wrapper">
        {/* Suggestions are rendered inline next to text (preview overlay). */}
        <div className="editor-preview" aria-hidden="true">
          {previewNodes}
        </div>

        <textarea
          ref={textareaRef}
          id="telugu-editor"
          className="editor-textarea"
          value={text}
          onChange={handleChange}
          onSelect={handleSelect}
          placeholder="ఇక్కడ తెలుగులో రాయండి... (Type Telugu here...)"
          spellCheck={false}
          maxLength={500}
        />

        {/* Autocomplete dropdown */}
        {autoSuggestions.length > 0 && (
          <AutocompleteDropdown
            suggestions={autoSuggestions}
            onSelect={applyAutocomplete}
            onDismiss={() => setAutoSuggestions([])}
          />
        )}
      </div>

      {/* Editor status */}
      <div className="error-summary">
        {text.trim() && (
          <>
            <span className="badge badge-grammar">
              Grammar: {grammarIssues.length}
            </span>
            <span className="badge badge-spell">
              Spelling: {spellingIssues.length}
            </span>
          </>
        )}
      </div>

      {/* Separate sections like Grammarly */}
      {text.trim() && (grammarIssues.length > 0 || spellingIssues.length > 0) && (
        <div className="issues-panel">
          <div className="issues-section">
            <div className="issues-title">Grammar</div>
            {grammarIssues.length === 0 ? (
              <div className="issues-empty">No grammar issues detected.</div>
            ) : (
              <ul className="issues-list">
                {grammarIssues.map((e, idx) => (
                  <li key={`g-${idx}`} className="issue-item grammar">
                    <span className="issue-bad">{e.word}</span>
                    <span className="issue-arrow">→</span>
                    <button
                      type="button"
                      className="issue-fix"
                      onClick={() => {
                        const newText =
                          text.slice(0, e.start) + e.correction + text.slice(e.end);
                        setText(newText);
                        setAnalysis(null);
                        triggerAnalyze(newText);
                        checkSpelling(newText);
                        checkGrammar(newText);
                      }}
                    >
                      {e.correction}
                    </button>
                    {e.explanation && (
                      <span className="issue-expl">{e.explanation}</span>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="issues-section">
            <div className="issues-title">Spelling</div>
            {spellingIssues.length === 0 ? (
              <div className="issues-empty">No spelling issues detected.</div>
            ) : (
              <ul className="issues-list">
                {spellingIssues.map((e, idx) => (
                  <li key={`s-${idx}`} className="issue-item spell">
                    <span className="issue-bad">{e.original}</span>
                    <span className="issue-arrow">→</span>
                    <div className="suggestion-options">
                      {(e.suggestions || []).slice(0, 3).map((sug, sidx) => (
                        <button
                          key={sidx}
                          type="button"
                          className="issue-fix"
                          onClick={() => {
                            if (typeof e.start !== "number" || typeof e.end !== "number")
                              return;
                            const newText =
                              text.slice(0, e.start) + sug.word + text.slice(e.end);
                            setText(newText);
                            setAnalysis(null);
                            triggerAnalyze(newText);
                            checkSpelling(newText);
                            checkGrammar(newText);
                          }}
                        >
                          {sug.word}
                        </button>
                      ))}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}

      {selectedError && popoverPos && (
        <SuggestionPopover
          error={selectedError}
          position={popoverPos}
          onApply={(word) => {
            // Apply a single suggestion (simple replacement within span)
            if (selectedError.start == null || selectedError.end == null) return;
            const start = selectedError.start;
            const end = selectedError.end;
            const newText = text.slice(0, start) + word + text.slice(end);
            setText(newText);
            setSelectedError(null);
            setPopoverPos(null);
            setAnalysis(null);
            triggerAnalyze(newText);
            checkSpelling(newText);
            checkGrammar(newText);
          }}
          onDismiss={() => {
            setSelectedError(null);
            setPopoverPos(null);
          }}
        />
      )}
    </div>
  );
}
