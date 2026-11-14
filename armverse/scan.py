"""Line-level scansion: words -> syllable counts -> candidate rhythmic patterns.

A *pattern* is a tuple of rhythmic-group sizes, e.g. (4, 4, 3).  Groups are cut
only at word boundaries and never right after a proclitic (մի, կը, ի, ...),
since a rhythmic group ends on a stressed syllable.  An enclitic may start the
next group (Ովկեանի | մը նըման).

Each candidate pattern keeps the cheapest way (fewest poetic licences) the line
can realise it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache

from .phonology import WordAnalysis, analyze_word, segment, ARMENIAN_LETTERS

# Words that lean on the FOLLOWING word (no cut after them).
PROCLITICS = {"մի", "ի", "յ", "զ", "առ", "ըստ", "չ", "կը", "կ", "չը"}
# Unstressed words leaning on the preceding word.  Informational only:
# cuts before them are allowed (Ովկեանի | մը նըման).
ENCLITICS = {"եմ", "է", "ենք", "եք", "են", "էի", "էիր", "էր", "էինք", "էիք",
             "էին", "էլ", "մը", "ալ"}


def _core(token: str) -> str:
    return "".join(ch for ch in token.lower() if ch in ARMENIAN_LETTERS)


def tokenize(line: str) -> list[tuple[str, bool]]:
    """Return (token, joined_to_next) pairs.  Hyphenated parts and elided
    clitics (կ՚ըսէ / կ' ըսէ) are joined to the next word."""
    out: list[tuple[str, bool]] = []
    for chunk in line.split():
        parts = re.split(r"(?<=\S)-(?=\S)", chunk)
        for i, p in enumerate(parts):
            if not _core(p):
                if out:  # pure punctuation: glue to previous token for display
                    tok, j = out[-1]
                    out[-1] = (tok + (" " if i == 0 else "-") + p, j)
                continue
            joined = i < len(parts) - 1 or bool(re.search(r"[՚'’]$", p))
            out.append((p if i == 0 else "-" + p, joined))
    return out


@dataclass
class Scansion:
    pattern: tuple[int, ...]
    variant: tuple[int, ...]  # chosen variant per word
    cuts: tuple[int, ...]  # word indices after which a cut falls
    cost: int = 0
    licences: list[str] = field(default_factory=list)


@dataclass
class LineAnalysis:
    text: str
    words: list[WordAnalysis]
    cut_allowed: list[bool]
    candidates: dict[tuple[int, ...], Scansion] = field(default_factory=dict)

    @property
    def default_syllables(self) -> int:
        return sum(w.variants[0].syllables for w in self.words if w.variants)

    def render(self, sc: Scansion | None) -> str:
        parts = []
        for i, w in enumerate(self.words):
            parts.append(w.render(sc.variant[i] if sc else 0))
            if sc and i in sc.cuts:
                parts.append("|")
        return " ".join(parts).replace(" -", "-")


def analyze_line(line: str, classical: bool = False, min_group: int = 2,
                 max_group: int = 5, prothesis: str = "both",
                 max_licences: int = 2) -> LineAnalysis:
    toks = tokenize(line)
    words: list[WordAnalysis] = []
    for i, (tok, _) in enumerate(toks):
        next_vowel = False
        if i + 1 < len(toks):
            segs = segment(_core(toks[i + 1][0]), classical)
            next_vowel = bool(segs) and segs[0].kind == "V"
        words.append(analyze_word(tok, next_vowel, classical, prothesis,
                                  max_licences))

    allowed = [not joined and _core(tok) not in PROCLITICS
               for tok, joined in toks]
    la = LineAnalysis(line, words, allowed)
    words_v = [w for w in words if w.variants]
    if not words_v:
        la.words = []
        return la
    la.words = words_v
    allowed = [a for a, w in zip(allowed, words) if w.variants]
    la.cut_allowed = allowed
    n = len(words_v)
    lo, hi = min_group, max_group

    @lru_cache(maxsize=None)
    def rec(i: int, acc: int):
        """Best ways to finish the line from word i with `acc` syllables
        already in the open group.  -> {pattern_tail: (cost, variants, cuts)}"""
        res: dict = {}

        def put(pat, cost, var, cuts):
            if cost > max_licences:
                return
            old = res.get(pat)
            if old is None or cost < old[0]:
                res[pat] = (cost, var, cuts)

        for vi, v in enumerate(words_v[i].variants):
            s = acc + v.syllables
            if s > hi:
                continue
            if i == n - 1:
                if s >= lo:
                    put((s,), v.cost, (vi,), ())
                continue
            for pat, (c, var, cuts) in rec(i + 1, s).items():
                put(pat, c + v.cost, (vi,) + var, cuts)
            if s >= lo and allowed[i]:
                for pat, (c, var, cuts) in rec(i + 1, 0).items():
                    put((s,) + pat, c + v.cost, (vi,) + var, (i,) + cuts)
        return res

    for pat, (cost, var, cuts) in rec(0, 0).items():
        lic = [l for w, vi in zip(words_v, var) for l in w.variants[vi].licences]
        la.candidates[pat] = Scansion(pat, var, cuts, cost, lic)
    return la
