"""
Weighted Levenshtein Edit Distance
===================================
Grapheme-cluster-aware, phonetic-weighted implementation.
Wagner–Fischer DP — O(m·n) where m,n = cluster counts.
"""

from typing import List, Optional

from app.core.unicode_utils import split_grapheme_clusters
from app.core.phonetic import substitution_cost


def weighted_levenshtein(
    source: str,
    target: str,
    source_clusters: Optional[List[str]] = None,
    target_clusters: Optional[List[str]] = None,
) -> float:
    """
    Weighted edit distance between two Telugu strings.

    Returns float — substitutions between confused pairs cost 0.5.
    Same-base-but-different-matra costs 0.3.
    """
    sc = source_clusters or split_grapheme_clusters(source)
    tc = target_clusters or split_grapheme_clusters(target)

    m, n = len(sc), len(tc)
    if m == 0:
        return float(n)
    if n == 0:
        return float(m)

    # DP table
    dp = [[0.0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = float(i)
    for j in range(n + 1):
        dp[0][j] = float(j)

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            s_cl, t_cl = sc[i - 1], tc[j - 1]

            if s_cl == t_cl:
                cost = 0.0
            else:
                cost = substitution_cost(s_cl[0], t_cl[0])
                # Same base consonant, different matra → small cost
                if cost == 0.0 and s_cl != t_cl:
                    cost = 0.3

            dp[i][j] = min(
                dp[i - 1][j] + 1.0,          # delete
                dp[i][j - 1] + 1.0,           # insert
                dp[i - 1][j - 1] + cost,      # substitute
            )

    return dp[m][n]


def generate_candidates(
    word: str,
    dictionary: dict,
    max_distance: float = 2.0,
) -> List[tuple]:
    """
    Return [(candidate, distance, frequency)] within max_distance,
    sorted by (distance ASC, frequency DESC).
    """
    w_cl = split_grapheme_clusters(word)
    w_len = len(w_cl)
    results = []

    for dw, freq in dictionary.items():
        d_cl = split_grapheme_clusters(dw)
        # Length-based prune
        if abs(len(d_cl) - w_len) > max_distance:
            continue

        dist = weighted_levenshtein(word, dw, w_cl, d_cl)
        if dist <= max_distance:
            results.append((dw, dist, freq))

    results.sort(key=lambda x: (x[1], -x[2]))
    return results
