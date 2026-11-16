"""Poem-level meter inference (RULES.md §6).

Each line has candidate patterns, each with a cost (licences + soft cuts).
The poem's meter is found by iterating: score(p) = log(frequency of p in the
poem) + catalogue bonus − penalty × cost, assign every line its best pattern,
re-estimate the frequencies, repeat until stable.  So a line uses a licence
only when it brings it into a meter that is more common in the poem, or that
Abeghyan catalogues.

Remaining ties: fewer members, then no member longer than the one before it
(4|4|3 over 4|3|4), then more balanced members, then larger members first.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field

from .phonology import is_classical
from .scan import LineAnalysis, Scansion, analyze_line


def fmt(pattern: tuple[int, ...] | None) -> str:
    if not pattern:
        return "?"
    return f"{sum(pattern)} ({'|'.join(map(str, pattern))})"


def _pref(p: tuple[int, ...]):
    rises = sum(1 for a, b in zip(p, p[1:]) if b > a)
    return (len(p), rises, max(p) - min(p), tuple(-x for x in p))


@dataclass
class ScannedLine:
    stanza: int
    number: int
    analysis: LineAnalysis
    scansion: Scansion | None
    regular: bool  # matches one of the poem's main meters

    @property
    def text(self):
        return self.analysis.text

    @property
    def pattern(self):
        return self.scansion.pattern if self.scansion else None

    @property
    def natural_pattern(self):
        """The line's own best division of the same syllables, ignoring the
        poem's meter: the cheapest candidate with the same syllable total as
        the chosen pattern (ties as in _pref)."""
        c = self.analysis.candidates
        if not c or not self.pattern:
            return None
        same = [p for p in c if sum(p) == sum(self.pattern)]
        return min(same, key=lambda p: (c[p].cost, _pref(p)))

    @property
    def natural_marked(self):
        p = self.natural_pattern
        return self.analysis.render(self.analysis.candidates[p]) if p else ""

    @property
    def licences(self) -> list[str]:
        return self.scansion.licences if self.scansion else []

    @property
    def marked(self):
        return self.analysis.render(self.scansion)


@dataclass
class PoemResult:
    title: str
    lines: list[ScannedLine]
    meters: list[tuple[tuple[int, ...], int]] = field(default_factory=list)
    classical: bool = False

    @property
    def regularity(self) -> float:
        if not self.lines:
            return 0.0
        return sum(l.regular for l in self.lines) / len(self.lines)

    def stanza_schemes(self) -> list[list[str]]:
        """Per-stanza sequence of line meters labelled A, B, C..."""
        labels = {p: chr(ord("A") + i) for i, (p, _) in enumerate(self.meters)
                  if i < 26}
        out: dict[int, list[str]] = {}
        for l in self.lines:
            out.setdefault(l.stanza, []).append(labels.get(l.pattern, "x"))
        return [out[k] for k in sorted(out)]


# Meters catalogued by Abeghyan, Part 2 (see RULES.md §6).
CATALOGUE = {
    (4, 4), (4, 4, 4), (4, 4, 4, 4),            # §§43-45
    (4, 3), (4, 4, 3), (4, 4, 4, 3),            # §§46-48
    (4, 3, 4, 3), (3, 4, 5), (4, 5), (4, 4, 5),  # §§49-52
    (3, 3), (3, 3, 3), (3, 3, 3, 3),            # §§55-57
    (3, 3, 2, 3), (3, 3, 3, 2), (2, 3, 3),      # §§58, 60, 62
    (5,), (5, 5), (5, 5, 5), (5, 5, 5, 5),      # §§64-67
    (4, 2, 4, 2),                               # 6+6, as the user scans it
}


def choose_patterns(analyses: list[LineAnalysis], licence_penalty: float = 0.4,
                    catalogue_bonus: float = 1.0, main_threshold: float = 0.15,
                    iterations: int = 20):
    """Assign one pattern per line (see module docstring).  Initial
    frequencies: each line supports every pattern it admits, discounted by
    half per unit of cost."""
    freq: Counter = Counter()
    for a in analyses:
        for p, sc in a.candidates.items():
            freq[p] += 0.5 ** sc.cost
    chosen: dict[int, tuple[int, ...]] = {}
    for _ in range(iterations):
        new = {}
        for i, a in enumerate(analyses):
            if not a.candidates:
                continue
            new[i] = min(a.candidates, key=lambda p: (
                -(math.log(freq[p] + 0.1)
                  + (catalogue_bonus if p in CATALOGUE else 0.0)
                  - licence_penalty * a.candidates[p].cost), _pref(p)))
        if new == chosen:
            break
        chosen = new
        freq = Counter(chosen.values())
    counts = Counter(chosen.values())
    order = sorted(counts.items(), key=lambda pc: (-pc[1], _pref(pc[0])))
    n = len(analyses) or 1
    main = {p for p, c in order if c >= 2 and c / n >= main_threshold}
    if not main and order:
        main = {order[0][0]}
    return chosen, order, main


def scan_poem(text: str, title: str = "", orthography: str = "auto",
              min_group: int = 2, max_group: int = 5,
              max_cost: int = 3, soft_cut_cost: int | None = 1,
              licence_penalty: float = 0.4,
              catalogue_bonus: float = 1.0) -> PoemResult:
    classical = (is_classical(text) if orthography == "auto"
                 else orthography == "classical")
    raw: list[tuple[int, int, str]] = []
    stanza, num = 1, 0
    for line in text.splitlines():
        s = line.strip()
        if not s:
            if raw and raw[-1][0] == stanza:
                stanza += 1
            continue
        if s.startswith("#"):
            continue
        num += 1
        raw.append((stanza, num, s))

    analyses = [analyze_line(s, classical, min_group, max_group, max_cost,
                             soft_cut_cost)
                for _, _, s in raw]
    keep = [i for i, a in enumerate(analyses) if a.words]
    analyses = [analyses[i] for i in keep]
    raw = [raw[i] for i in keep]

    chosen, order, main = choose_patterns(analyses, licence_penalty,
                                         catalogue_bonus)
    lines = []
    for i, ((st, nm, _), a) in enumerate(zip(raw, analyses)):
        p = chosen.get(i)
        sc = a.candidates.get(p) if p else None
        lines.append(ScannedLine(st, nm, a, sc, p in main))
    return PoemResult(title, lines, order, classical)
