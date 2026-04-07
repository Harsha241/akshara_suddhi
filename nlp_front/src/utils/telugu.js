/**
 * Telugu text utility helpers for the frontend.
 */

const TELUGU_RANGE = /[\u0C00-\u0C7F]/;

export function isTeluguChar(ch) {
  return TELUGU_RANGE.test(ch);
}

export function isTeluguWord(word) {
  if (!word) return false;
  const te = [...word].filter((c) => TELUGU_RANGE.test(c)).length;
  const al = [...word].filter((c) => /[a-zA-Z]/.test(c) || TELUGU_RANGE.test(c)).length;
  return al > 0 && te / al > 0.5;
}

/**
 * Get the current word being typed (the word at cursor position).
 */
export function getCurrentWord(text, cursorPos) {
  const before = text.slice(0, cursorPos);
  const after = text.slice(cursorPos);
  const wordBefore = (before.match(/[\u0C00-\u0C7Fa-zA-Z]+$/) || [""])[0];
  const wordAfter = (after.match(/^[\u0C00-\u0C7Fa-zA-Z]+/) || [""])[0];
  return {
    word: wordBefore + wordAfter,
    prefix: wordBefore,
    start: cursorPos - wordBefore.length,
    end: cursorPos + wordAfter.length,
  };
}

/**
 * Split text into tokens with position info.
 */
export function tokenizeWithPositions(text) {
  const regex = /[\u0C00-\u0C7F]+|[a-zA-Z]+|[0-9]+|[^\s\u0C00-\u0C7Fa-zA-Z0-9]/g;
  const tokens = [];
  let match;
  while ((match = regex.exec(text)) !== null) {
    tokens.push({
      text: match[0],
      start: match.index,
      end: match.index + match[0].length,
    });
  }
  return tokens;
}
