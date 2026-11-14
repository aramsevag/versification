"""Poem-level meter inference.

A single line is often ambiguous ("Ահա սըրտիս խոպան դաշտն ուր մի անգամ" fits
both 4|4|3 and 4|3|4).  Poems are usually metrically consistent, so we choose,
greedily, the pattern admitted by the largest number of lines, assign those
lines to it, and repeat with the remaining lines.

Tie-breaks between equally supported patterns: fewer groups, then fewer places
where a group is longer than the previous one (Armenian lines tend to end with
the shorter group: 4|4|3, 4|3), then more balanced groups (4|4 over 5|3),
then larger groups first.
"""

from __future__ import annotations

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


def choose_patterns(analyses: list[LineAnalysis], main_threshold: float = 0.15):
    remaining = set(range(len(analyses)))
    chosen: dict[int, tuple[int, ...]] = {}
    order: list[tuple[tuple[int, ...], int]] = []
    while remaining:
        support = Counter()
        for i in remaining:
            support.update(analyses[i].candidates.keys())
        if not support:
            break
        best = min(support, key=lambda p: (-support[p], _pref(p)))
        members = [i for i in remaining if best in analyses[i].candidates]
        for i in members:
            chosen[i] = best
        remaining -= set(members)
        order.append((best, len(members)))
    n = len(analyses) or 1
    main = {p for p, c in order if c >= 2 and c / n >= main_threshold}
    if not main and order:
        main = {order[0][0]}
    return chosen, order, main


def scan_poem(text: str, title: str = "", orthography: str = "auto",
              min_group: int = 2, max_group: int = 5,
              prothesis: str = "both") -> PoemResult:
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

    analyses = [analyze_line(s, classical, min_group, max_group, prothesis)
                for _, _, s in raw]
    keep = [i for i, a in enumerate(analyses) if a.words]
    analyses = [analyses[i] for i in keep]
    raw = [raw[i] for i in keep]

    chosen, order, main = choose_patterns(analyses)
    lines = []
    for i, ((st, nm, _), a) in enumerate(zip(raw, analyses)):
        p = chosen.get(i)
        sc = a.candidates.get(p) if p else None
        lines.append(ScannedLine(st, nm, a, sc, p in main))
    return PoemResult(title, lines, order, classical)
