"""
Trie for Telugu Autocomplete
=============================
Each path stores a Telugu word; leaf nodes carry frequency.
prefix_search returns top-K completions ranked by frequency.
"""

from typing import Dict, List, Optional, Tuple


class TrieNode:
    """Single node in the Trie."""
    __slots__ = ("children", "is_end", "frequency", "word")

    def __init__(self):
        self.children: Dict[str, "TrieNode"] = {}
        self.is_end: bool = False
        self.frequency: int = 0
        self.word: Optional[str] = None


class Trie:
    """
    Trie built from a {word: frequency} dictionary.

    Usage
    -----
    >>> t = Trie()
    >>> t.build({"నేను": 5000, "నేర్చు": 200, "నీవు": 3200})
    >>> t.prefix_search("నే", top_k=5)
    [("నేను", 5000), ("నేర్చు", 200)]
    """

    def __init__(self):
        self.root = TrieNode()

    # ── Build ────────────────────────────────────────────────────────────

    def build(self, dictionary: Dict[str, int]) -> None:
        """Insert every word from the dictionary."""
        for word, freq in dictionary.items():
            self.insert(word, freq)

    def insert(self, word: str, frequency: int) -> None:
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.is_end = True
        node.frequency = frequency
        node.word = word

    # ── Search ───────────────────────────────────────────────────────────

    def _walk_prefix(self, prefix: str) -> Optional[TrieNode]:
        """Walk down the trie following *prefix*; return end node or None."""
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return None
            node = node.children[ch]
        return node

    def search(self, word: str) -> bool:
        """Return True if *word* is in the trie."""
        node = self._walk_prefix(word)
        return node is not None and node.is_end

    def prefix_search(
        self, prefix: str, top_k: int = 5
    ) -> List[Tuple[str, int]]:
        """
        Return up to *top_k* completions for *prefix*,
        sorted by frequency DESC.
        """
        node = self._walk_prefix(prefix)
        if node is None:
            return []

        # DFS to collect all words below this node
        results: List[Tuple[str, int]] = []
        stack = [node]
        while stack:
            cur = stack.pop()
            if cur.is_end and cur.word is not None:
                results.append((cur.word, cur.frequency))
            for child in cur.children.values():
                stack.append(child)

        # Sort by frequency descending, take top_k
        results.sort(key=lambda x: -x[1])
        return results[:top_k]
