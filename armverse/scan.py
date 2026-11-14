"""Line-level scansion: words -> syllable counts -> candidate rhythmic patterns.

A *pattern* is a tuple of rhythmic-group sizes, e.g. (4, 4, 3).  Groups are cut
only at word boundaries, and never right after a proclitic (մի, ի, ...) or right
before an enclitic (է, եմ, էլ, ...).
"""

from __future__ import annotations

import itertools
import re
from dataclasses import dataclass, field

from .phonology import WordAnalysis, analyze_word, segment, ARMENIAN_LETTERS

# Words that lean on the FOLLOWING word (no cut after them).
PROCLITICS = {"մի", "ի", "յ", "զ", "առ", "ըստ", "չ"}
# Words that lean on the PRECEDING word (no cut before them).
ENCLITICS = {
    "եմ", "է",  # "ես" omitted: usually the pronoun "I"
    "ենք", "եք", "են",
    "էի", "էիր", "էր", "էինք", "էիք", "էին",
    "էլ", "եմք", "էք", "էաք",
}

MAX_VARIANT_COMBOS = 64


def _core(token: str) -> str:
    return "".join(ch for ch in token.lower() if ch in ARMENIAN_LETTERS)


def tokenize(line: str) -> list[tuple[str, bool]]:
    """Return (token, joined_to_next) pairs.  Hyphenated parts are joined."""
    out: list[tuple[str, bool]] = []
    for chunk in line.split():
        parts = [p for p in re.split(r"(?<=\S)-(?=\S)", chunk)]
        for i, p in enumerate(parts):
            if not _core(p):
                # pure punctuation: glue to previous token for display
                if out:
                    tok, j = out[-1]
                    out[-1] = (tok + (" " if i == 0 else "-") + p, j)
                continue
            out.append((p if i == 0 else "-" + p, i < len(parts) - 1))
    return out


@dataclass
class Scansion:
    pattern: tuple[int, ...]
    variant: tuple[int, ...]  # chosen variant per word
    cuts: tuple[int, ...]  # word indices after which a cut falls


@dataclass
class LineAnalysis:
    text: str
    words: list[WordAnalysis]
    cut_allowed: list[bool]  # after word i
    candidates: dict[tuple[int, ...], Scansion] = field(default_factory=dict)
    syllable_options: set[int] = field(default_factory=set)

    def render(self, sc: Scansion | None) -> str:
        if sc is None:
            return " ".join(w.render(0) for w in self.words)
        parts = []
        for i, w in enumerate(self.words):
            parts.append(w.render(sc.variant[i]))
            if i in sc.cuts:
                parts.append("|")
        return " ".join(parts).replace(" -", "-")


def _segmentations(sizes: list[int], allowed: list[bool], lo: int, hi: int):
    """Yield (pattern, cuts) for every way to cut the word sequence."""
    n = len(sizes)

    def rec(start: int):
        acc = 0
        for end in range(start, n):
            acc += sizes[end]
            if acc > hi:
                return
            if end == n - 1:
                if acc >= lo:
                    yield (acc,), ()
                return
            if acc >= lo and allowed[end]:
                for pat, cuts in rec(end + 1):
                    yield (acc,) + pat, (end,) + cuts

    yield from rec(0)


def analyze_line(line: str, classical: bool = False, min_group: int = 2,
                 max_group: int = 5, prothesis: str = "both") -> LineAnalysis:
    toks = tokenize(line)
    words: list[WordAnalysis] = []
    for i, (tok, _) in enumerate(toks):
        next_vowel = False
        if i + 1 < len(toks):
            segs = segment(_core(toks[i + 1][0]), classical)
            next_vowel = bool(segs) and segs[0].kind == "V"
        words.append(analyze_word(tok, next_vowel, classical, prothesis))

    allowed = []
    for i in range(len(toks)):
        ok = not toks[i][1]
        if ok and _core(toks[i][0]) in PROCLITICS:
            ok = False
        if ok and i + 1 < len(toks) and _core(toks[i + 1][0]) in ENCLITICS:
            ok = False
        allowed.append(ok)

    la = LineAnalysis(line, words, allowed)
    if not words:
        return la
    choices = [range(len(w.variants)) for w in words]
    for k, combo in enumerate(itertools.product(*choices)):
        if k >= MAX_VARIANT_COMBOS:
            break
        sizes = [w.variants[v].syllables for w, v in zip(words, combo)]
        la.syllable_options.add(sum(sizes))
        for pat, cuts in _segmentations(sizes, allowed, min_group, max_group):
            if pat not in la.candidates:  # first combo = preferred variant
                la.candidates[pat] = Scansion(pat, combo, cuts)
    return la
