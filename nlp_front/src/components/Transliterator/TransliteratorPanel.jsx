import { useState, useCallback } from "react";
import { transliterate } from "../../api/client";

/**
 * Transliterator Panel — converts Romanised Telugu to Telugu script.
 */
export default function TransliteratorPanel() {
  const [romanText, setRomanText] = useState("");
  const [teluguText, setTeluguText] = useState("");
  const [segments, setSegments] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleConvert = useCallback(async () => {
    if (!romanText.trim()) return;
    setLoading(true);
    try {
      const res = await transliterate(romanText);
      setTeluguText(res.output_text);
      setSegments(res.segments || []);
    } catch (err) {
      console.error("Transliteration error:", err);
    } finally {
      setLoading(false);
    }
  }, [romanText]);

  const handleInputChange = useCallback((e) => {
    setRomanText(e.target.value);
  }, []);

  const handleKeyDown = useCallback(
    (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleConvert();
      }
    },
    [handleConvert]
  );

  const copyToClipboard = useCallback(() => {
    navigator.clipboard.writeText(teluguText);
  }, [teluguText]);

  return (
    <div className="transliterator-panel">
      <h3>🔤 Transliterator</h3>
      <p className="panel-desc">
        Type in Romanised Telugu (e.g., &quot;nenu baagunnanu&quot;) and convert to
        Telugu script.
      </p>

      <div className="translit-input-group">
        <input
          id="translit-input"
          type="text"
          className="translit-input"
          value={romanText}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder='e.g. "nenu baagunnanu"'
          maxLength={500}
        />
        <button
          className="translit-btn"
          onClick={handleConvert}
          disabled={loading || !romanText.trim()}
        >
          {loading ? "..." : "Convert →"}
        </button>
      </div>

      {teluguText && (
        <div className="translit-result">
          <div className="translit-output">
            <span className="telugu-output-text">{teluguText}</span>
            <button
              className="copy-btn"
              onClick={copyToClipboard}
              title="Copy to clipboard"
            >
              📋
            </button>
          </div>

          {segments.length > 0 && (
            <div className="segment-breakdown">
              <p className="segment-title">Mapping breakdown:</p>
              <div className="segment-chips">
                {segments.slice(0, 20).map((seg, i) => (
                  <span key={i} className="segment-chip">
                    <span className="seg-roman">{seg.roman}</span>
                    <span className="seg-arrow">→</span>
                    <span className="seg-telugu">{seg.telugu}</span>
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
