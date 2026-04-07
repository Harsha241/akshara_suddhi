import { useState, useRef, useCallback } from "react";
import useSpellCheck from "../../hooks/useSpellCheck";

/**
 * Spell Correction Panel — focused on spelling corrections
 */
export default function SpellCorrectionPanel() {
  const [text, setText] = useState("");
  const textareaRef = useRef(null);

  const { errors: spellErrors, checkSentence: checkSpelling } = useSpellCheck();

  // ── Handle text change ───────────────────────────────────────────────
  const handleChange = useCallback(
    (e) => {
      const value = e.target.value;
      if (value.length > 500) return; // max input limit

      setText(value);
      checkSpelling(value);
    },
    [checkSpelling]
  );

  const charCount = text.length;
  const spellingIssues = spellErrors || [];

  return (
    <div className="correction-panel">
      {/* Header */}
      <div className="panel-header">
        <h2>తెలుగు స్పెల్ చెక్</h2>
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

      {/* Spelling corrections section */}
      {text.trim() && (
        <div className="corrections-section">
          <div className="corrections-title">
            Spelling Corrections ({spellingIssues.length})
          </div>
          {spellingIssues.length === 0 ? (
            <div className="corrections-empty">
              No spelling issues detected. Great job! ✨
            </div>
          ) : (
            <ul className="corrections-list">
              {spellingIssues.map((e, idx) => (
                <li key={`s-${idx}`} className="correction-item">
                  <div className="correction-content">
                    <span className="correction-bad">{e.original}</span>
                    <span className="correction-arrow">→</span>
                    <div className="correction-suggestions">
                      {(e.suggestions || []).slice(0, 3).map((sug, sidx) => (
                        <button
                          key={sidx}
                          type="button"
                          className="correction-fix"
                          onClick={() => {
                            if (typeof e.start !== "number" || typeof e.end !== "number")
                              return;
                            const newText =
                              text.slice(0, e.start) + sug.word + text.slice(e.end);
                            setText(newText);
                            checkSpelling(newText);
                          }}
                        >
                          {sug.word}
                        </button>
                      ))}
                    </div>
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