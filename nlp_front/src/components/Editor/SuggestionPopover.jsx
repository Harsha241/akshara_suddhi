/**
 * SuggestionPopover — shows spell/grammar correction suggestions
 * on click/hover of an error-highlighted word.
 */
export default function SuggestionPopover({ error, position, onApply, onDismiss }) {
  const isSpell = error.type === "spell";

  const suggestions = isSpell
    ? (error.suggestions || [])
    : [{ word: error.correction, score: 1 }];

  return (
    <div
      className="suggestion-popover"
      style={{
        position: "fixed",
        top: position.top,
        left: position.left,
        zIndex: 1000,
      }}
    >
      <div className="popover-header">
        <span className={`popover-type ${isSpell ? "spell" : "grammar"}`}>
          {isSpell ? "📝 Spelling" : "📖 Grammar"}
        </span>
        <button className="popover-close" onClick={onDismiss}>
          ✕
        </button>
      </div>

      {error.explanation && (
        <p className="popover-explanation">{error.explanation}</p>
      )}

      <div className="popover-suggestions">
        {suggestions.map((s, i) => (
          <button
            key={i}
            className="suggestion-btn"
            onClick={() => onApply(s.word)}
          >
            <span className="suggestion-word">{s.word}</span>
            {s.score !== undefined && (
              <span className="suggestion-score">
                {(s.score * 100).toFixed(0)}%
              </span>
            )}
          </button>
        ))}
      </div>

      {isSpell && error.original && (
        <p className="popover-original">
          Original: <strong>{error.original}</strong>
        </p>
      )}
    </div>
  );
}
