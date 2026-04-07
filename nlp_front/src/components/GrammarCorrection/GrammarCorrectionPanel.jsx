import { useState, useRef, useCallback } from "react";
import useGrammarCheck from "../../hooks/useGrammarCheck";

/**
 * Grammar Correction Panel — focused on grammar corrections
 */
export default function GrammarCorrectionPanel() {
  const [text, setText] = useState("");
  const textareaRef = useRef(null);

  const { errors: grammarErrors, check: checkGrammar } = useGrammarCheck();

  // ── Handle text change ───────────────────────────────────────────────
  const handleChange = useCallback(
    (e) => {
      const value = e.target.value;
      if (value.length > 500) return; // max input limit

      setText(value);
      checkGrammar(value);
    },
    [checkGrammar]
  );

  const charCount = text.length;
  const grammarIssues = (grammarErrors || []).filter(
    (e) => typeof e.start === "number" && typeof e.end === "number"
  );

  return (
    <div className="correction-panel">
      {/* Header */}
      <div className="panel-header">
        <h2>తెలుగు గ్రామర్ చెక్</h2>
        <span className={`char-count ${charCount > 450 ? "warn" : ""}`}>
          {charCount}/500
        </span>
      </div>

      {/* Text input */}
      <div className="panel-input">
        <textarea
          ref={textareaRef}
          className="correction-textarea"
          value={text}
          onChange={handleChange}
          placeholder="ఇక్కడ తెలుగులో రాయండి... (Type Telugu here...)"
          spellCheck={false}
          maxLength={500}
        />
      </div>

      {/* Grammar corrections section */}
      {text.trim() && (
        <div className="corrections-section">
          <div className="corrections-title">
            Grammar Corrections ({grammarIssues.length})
          </div>
          {grammarIssues.length === 0 ? (
            <div className="corrections-empty">
              No grammar issues detected. Excellent grammar! 🎉
            </div>
          ) : (
            <ul className="corrections-list">
              {grammarIssues.map((e, idx) => (
                <li key={`g-${idx}`} className="correction-item">
                  <div className="correction-content">
                    <span className="correction-bad">{e.word}</span>
                    <span className="correction-arrow">→</span>
                    <button
                      type="button"
                      className="correction-fix"
                      onClick={() => {
                        const newText =
                          text.slice(0, e.start) + e.correction + text.slice(e.end);
                        setText(newText);
                        checkGrammar(newText);
                      }}
                    >
                      {e.correction}
                    </button>
                    {e.explanation && (
                      <span className="correction-expl">{e.explanation}</span>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}