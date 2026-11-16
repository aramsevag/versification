"""Line-level scansion: candidate divisions of a line into members (RULES.md §5).

A *pattern* is a tuple of member sizes, e.g. (4, 4, 3).  Cuts:
  * after a word whose last syllable is stressed            cost 0
  * inside a word, before its unstressed final ը-syllable    cost 0  (ձեռ|քըդ)
  * after an unstressed ending (enclitic, final ը)           cost `soft_cut_cost`
  * after a proclitic or inside a hyphenated word            never
Each pattern keeps the cheapest reading (licences + cuts) that realises it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache

from .phonology import (PUNCT_PAUSE, WordAnalysis, analyze_word, core_of,
                        end_type, segment)

PROCLITICS = {"մի", "կը", "չը", "ու", "և", "եւ", "ի", "յ", "զ", "առ", "ըստ", "ընդ",
              "կ", "չ"}
# Unstressed words a member may still end on, at the soft-cut cost
# (Չըգիտնալ որ | ...); confirmed by the project author.
UNSTRESSED = {"որ", "թէ", "թե", "եթէ", "եթե"}
ENCLITICS = {"եմ", "է", "ենք", "եք", "են", "էի", "էիր", "էր", "էինք", "էիք", "էին",
             "եմք", "էք", "էլ", "մը", "ալ", "պես"}


def _core(token: str) -> str:
    return core_of(token)[0]


def tokenize(line: str) -> list[tuple[str, bool]]:
    """(token, joined_to_next).  Hyphenated parts and elided clitics
    (կ' ըսէ) are joined to the next word."""
    out: list[tuple[str, bool]] = []
    for chunk in line.split():
        parts = re.split(r"(?<=\S)-(?=\S)", chunk)
        for i, p in enumerate(parts):
            if not _core(p):
                if out:  # pure punctuation: glue to previous token
                    tok, j = out[-1]
                    out[-1] = (tok + (" " if i == 0 else "-") + p, j)
                continue
            joined = i < len(parts) - 1 or bool(re.search(r"[՚'’]$", p))
            out.append((p if i == 0 else "-" + p, joined))
    return out


def _pause_after(token: str) -> bool:
    """Punctuation after the word's last letter marks a pause (§15 Բ)."""
    k = max((i for i, ch in enumerate(token) if "\u0531" <= ch <= "\u0587"), default=-1)
    return any(ch in PUNCT_PAUSE for ch in token[k + 1:])


@dataclass
class Scansion:
    pattern: tuple[int, ...]
    variant: tuple[int, ...]  # chosen reading per word
    cuts: tuple[tuple[int, str], ...]  # (word index, 'after' | 'mid')
    cost: int = 0
    licences: list[str] = field(default_factory=list)


@dataclass
class LineAnalysis:
    text: str
    words: list[WordAnalysis]
    candidates: dict[tuple[int, ...], Scansion] = field(default_factory=dict)

    @property
    def default_syllables(self) -> int:
        return sum(w.variants[0].syllables for w in self.words)

    def render(self, sc: Scansion | None) -> str:
        after = {i for i, t in sc.cuts if t == "after"} if sc else set()
        mid = {i for i, t in sc.cuts if t == "mid"} if sc else set()
        parts = []
        for i, w in enumerate(self.words):
            parts.append(w.render(sc.variant[i] if sc else 0, i in mid))
            if i in after:
                parts.append("|")
        return " ".join(parts).replace(" -", "-")


def analyze_line(line: str, classical: bool = False, min_group: int = 2,
                 max_group: int = 5, max_cost: int = 3,
                 soft_cut_cost: int | None = 1) -> LineAnalysis:
    toks = tokenize(line)
    words: list[WordAnalysis] = []
    for i, (tok, _) in enumerate(toks):
        prev = end_type(toks[i - 1][0], classical) if i else "start"
        nxt = segment(_core(toks[i + 1][0]), classical) if i + 1 < len(toks) else []
        next_vowel = bool(nxt) and nxt[0].kind == "V"
        next_h = bool(nxt) and (nxt[0].letter == "հ" or (
            classical and nxt[0].letter == "յ" and len(nxt) > 1
            and nxt[1].kind == "V"))
        pause = i + 1 == len(toks) or _pause_after(tok)
        words.append(analyze_word(tok, prev, next_vowel, pause, classical,
                                  max_cost, next_h=next_h))
    keep = [i for i, w in enumerate(words) if w.variants]
    words = [words[i] for i in keep]
    toks = [toks[i] for i in keep]
    la = LineAnalysis(line, words)
    n = len(words)
    if not n:
        return la
    cores = [_core(t) for t, _ in toks]
    can_cut = [not j and c not in PROCLITICS for (t, j), c in zip(toks, cores)]
    clitic = [c in ENCLITICS or c in PROCLITICS or c in UNSTRESSED for c in cores]
    lo, hi = min_group, max_group

    @lru_cache(maxsize=None)
    def rec(i: int, acc: int):
        """{pattern_tail: (cost, variants, cuts)} for words i.. with `acc`
        syllables already in the open member."""
        res: dict = {}

        def put(pat, cost, var, cuts):
            if cost <= max_cost and (pat not in res or cost < res[pat][0]):
                res[pat] = (cost, var, cuts)

        for vi, v in enumerate(words[i].variants):
            # ways to place this word: (syllables into open member, closes?, cut cost, cut)
            choices = [(v.syllables, False, 0, None)]
            unstressed = v.final_unstressed or clitic[i]
            if can_cut[i] and i < n - 1:
                cc = 0 if not unstressed else soft_cut_cost
                if cc is not None:
                    choices.append((v.syllables, True, cc, (i, "after")))
            for syl, closes, cc, cut in choices:
                s = acc + syl
                if s > hi:
                    continue
                base = v.cost + cc
                if i == n - 1:
                    if s >= lo:
                        put((s,), base, (vi,), ())
                    continue
                if closes:
                    if s >= lo:
                        for pat, (c, var, cuts) in rec(i + 1, 0).items():
                            put((s,) + pat, c + base, (vi,) + var, (cut,) + cuts)
                else:
                    for pat, (c, var, cuts) in rec(i + 1, s).items():
                        put(pat, c + base, (vi,) + var, cuts)
            # cut inside the word, before its unstressed final syllable
            if v.mid_ci is not None and v.syllables >= 2 and not clitic[i]:
                s = acc + v.syllables - 1
                if lo <= s <= hi:
                    if i == n - 1:
                        continue  # a 1-syllable final member is never wanted
                    for pat, (c, var, cuts) in rec(i + 1, 1).items():
                        put((s,) + pat, c + v.cost, (vi,) + var,
                            ((i, "mid"),) + cuts)
        return res

    for pat, (cost, var, cuts) in rec(0, 0).items():
        lic = [l for w, vi in zip(words, var) for l in w.variants[vi].licences]
        soft = sum(1 for (i, t) in cuts if t == "after"
                   and (words[i].variants[var[i]].final_unstressed or clitic[i]))
        if soft:
            lic.append(f"{soft}× cut after an unstressed ending (§30.3)")
        la.candidates[pat] = Scansion(pat, var, cuts, cost, lic)
    return la
