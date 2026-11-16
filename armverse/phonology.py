"""Syllable counting for Armenian verse, after Abeghyan (see RULES.md).

For each word this module returns every reading allowed by the rules, each
with a *cost*: 0 = natural pronunciation (or an equally natural alternative),
1 = a light licence, 2 = a heavy ("for the eye only") licence.  Section and
page references in comments are to Abeghyan, Հայոց լեզվի տաղաչափություն
(Երկեր, հ. Ե, 1971).
"""

from __future__ import annotations

import itertools
import re
from dataclasses import dataclass, field

VOWEL_LETTERS = set("աեէըիոօ")
STOPS = set("բգդթկպտփքձծջճչց")  # stops and affricates
CONSONANT_LETTERS = set("բգդզթժլխծկհձղճմյնշչպջռսվտրցւփքֆ")
ARMENIAN_LETTERS = VOWEL_LETTERS | CONSONANT_LETTERS | {"և"}

# §9 p. 31-32: the first of two syllable-final consonants can only be one of
# these (sonorants and continuants; յ as the second half of a diphthong) ...
CODA_FIRST = set("րռլնմղխվզսժշհյւֆ")
# ... and no consonant can be followed by ն ր վ շ at the end of a syllable.
CODA_BANNED_SECOND = set("նրռվշւ")
SONORANTS = set("րռլնմ")
# §9 p. 31, §17: initial clusters taking the prothetic ը (ըստեղծել)
PROTHETIC = {"զբ", "զգ", "զդ", "զմ", "սկ", "սպ", "սք", "ստ", "սթ", "սփ", "շպ",
             "շտ", "շք", "շթ", "շկ"}
# §17 Բ p. 62-63: after these consonants the prothetic ը drops easily
EASY_BEFORE_S = set("նմրռվխղգկք")

PUNCT_PAUSE = set(",.;:!?…—–՝։՞«»()\"")


@dataclass
class Seg:
    kind: str  # "V" or "C"
    start: int  # index into the core string
    end: int
    letter: str = ""


def is_classical(text: str) -> bool:
    """Heuristic: classical (Mashtotsian) orthography, as used for Western
    Armenian and pre-1922 poetry: ւ outside ու, եա, word-internal է, կը/մը."""
    for w in re.findall(r"[Ա-և]+", text.lower()):
        if w in ("կը", "մը"):
            return True
        if w != "եւ" and re.search(r"(?<!ո)ւ", w):
            return True
        if re.search(r"եա(?!կան)", w) or (len(w) > 1 and "է" in w[1:]):
            return True
    return False


def _vowel_at(core: str, j: int) -> bool:
    return j < len(core) and (core[j] in VOWEL_LETTERS or core[j] == "և")


def segment(core: str, classical: bool = False) -> list[Seg]:
    segs: list[Seg] = []
    i, n = 0, len(core)
    while i < n:
        c = core[i]
        nxt = core[i + 1] if i + 1 < n else ""
        if c == "ո" and nxt == "ւ":
            if segs and segs[-1].kind == "C" and _vowel_at(core, i + 2):
                segs.append(Seg("C", i, i + 2, "ւ"))  # Աստուած: ու = v (§16 Ա)
            else:
                segs.append(Seg("V", i, i + 2, "ու"))
            i += 2
        elif c == "ի" and nxt == "ւ":  # classical իւ = յու (§9 p. 33)
            segs.append(Seg("V", i, i + 2, "իւ"))
            i += 2
        elif classical and c == "ե" and nxt in ("ա", "օ"):  # եա = յա
            segs.append(Seg("V", i, i + 2, c + nxt))
            i += 2
        elif c == "և":
            segs.append(Seg("V", i, i + 1, "ե"))
            segs.append(Seg("C", i + 1, i + 1, "վ"))
            i += 1
        elif c in VOWEL_LETTERS:
            segs.append(Seg("V", i, i + 1, c))
            i += 1
        elif c in CONSONANT_LETTERS:
            segs.append(Seg("C", i, i + 1, c))
            i += 1
        else:
            i += 1
    return segs


# ---------------------------------------------------------------- clusters

def _L(segs, R):
    return [segs[k].letter for k in R]


def _valid_onset(segs, R) -> bool:
    return len(R) <= 1 or (len(R) == 2 and segs[R[1]].letter == "յ")


def _valid_coda(segs, R) -> bool:
    if len(R) <= 1:
        return True
    if len(R) == 2:
        a, b = _L(segs, R)
        return a in CODA_FIRST and b not in CODA_BANNED_SECOND
    return False


@dataclass
class Ins:
    """A natural schwa insertion before segment k."""
    k: int
    drop_cost: int | None  # cost of omitting it; None = cannot be omitted
    why: str


def _medial(segs, R, after_vowel=True) -> list[Ins]:
    """Schwa insertions in a consonant run R that ends before a vowel."""
    if not R or _valid_onset(segs, R):
        return []
    # §14 Գ: C C վ -> ը before վ; when the middle one is ր ռ ղ, before it.
    if len(R) >= 3 and segs[R[-1]].letter in ("վ", "ւ"):
        if segs[R[-2]].letter in ("ր", "ռ", "ղ"):
            k = R[-2]
            return (_medial(segs, R[:-2], after_vowel)
                    + [Ins(k, 2, "§14 Գ p. 46")] + _medial(segs, R[-2:]))
        k = R[-1]
        cost = 0 if _valid_coda(segs, R[-3:-1]) else 2
        return (_medial(segs, R[:-1], after_vowel)
                + [Ins(k, cost, "§14 Գ p. 46")])
    if after_vowel:
        for clen in (2, 1):
            if len(R) > clen and _valid_coda(segs, R[:clen]) \
                    and _valid_onset(segs, R[clen:]):
                return []
        if segs[R[0]].letter not in CODA_FIRST and segs[R[1]].letter in SONORANTS:
            return [Ins(R[1], 2, "§14 p. 42")] + _medial(segs, R[1:])
        clen = 2 if _valid_coda(segs, R[:2]) and len(R) > 2 else 1
        rest = R[clen:]
        return [Ins(rest[1], 2, "§9 p. 32")] + _medial(segs, rest[1:])
    return [Ins(R[1], 2, "§9 p. 31")] + _medial(segs, R[1:])


def _final(segs, F) -> list[int]:
    """Natural schwa insertions in a word-final cluster (§9 p. 32, §15)."""
    if len(F) <= 1:
        return []
    a, b = segs[F[-2]].letter, segs[F[-1]].letter
    if len(F) >= 3:
        if b == "ք" and _valid_coda(segs, F[-3:-1]):
            return _final(segs, F[:-1])
        return _final(segs, F[:-1]) + [F[-1]]
    if b in CODA_BANNED_SECOND and a != "յ":
        return [F[-1]]
    if b == "ղ" and a in STOPS:
        return [F[-1]]
    if b == "ք" or (a == "ք" and b == "ս") or a in CODA_FIRST:
        return []
    return [F[-1]]


# ---------------------------------------------------------------- words

@dataclass
class Opt:
    delta: int
    cost: int
    desc: str
    add: int | None = None  # insert schwa before this segment
    remove: int | None = None  # drop the natural schwa before this segment
    marks: list[tuple[int, str]] = field(default_factory=list)


@dataclass
class WordVariant:
    syllables: int
    cost: int = 0
    marks: list[tuple[int, str]] = field(default_factory=list)
    licences: list[str] = field(default_factory=list)
    final_unstressed: bool = False  # last syllable has ը (stress on the one before)
    mid_ci: int | None = None  # core index where a cut before that syllable goes


@dataclass
class WordAnalysis:
    token: str
    core: str
    core_map: list[int]
    segs: list[Seg]
    variants: list[WordVariant] = field(default_factory=list)

    def _tok_index(self, ci: int) -> int:
        if not self.core_map:
            return len(self.token)
        if ci < len(self.core_map):
            return self.core_map[ci]
        return self.core_map[-1] + 1

    def render(self, v: int = 0, mid_cut: bool = False) -> str:
        """Token with restored ը; dieresis ·, synizesis ‿, inner cut |."""
        var = self.variants[v]
        marks = list(var.marks)
        if mid_cut and var.mid_ci is not None:
            marks.append((var.mid_ci, "|"))
        out = self.token
        order = {"|": 0, "ը": 1, "·": 1, "‿": 1}
        for ci, text in sorted(marks, key=lambda m: (m[0], order.get(m[1], 1)),
                               reverse=True):
            p = self._tok_index(ci)
            if (text == "ը" and ci == 0 and p < len(out) and out[p].isupper()):
                out = out[:p] + "Ը" + out[p].lower() + out[p + 1:]
            else:
                out = out[:p] + text + out[p:]
        return out


def core_of(token: str) -> tuple[str, list[int]]:
    low = token.lower()
    chars, cmap = [], []
    for i, ch in enumerate(low):
        if ch in ARMENIAN_LETTERS:
            chars.append(ch)
            cmap.append(i)
    return "".join(chars), cmap


def analyze_word(token: str, prev_end: str = "start", next_vowel: bool = False,
                 pause_after: bool = True, classical: bool = False,
                 max_cost: int = 3, max_options: int = 4) -> WordAnalysis:
    """All readings of one word in context.

    prev_end: 'start' (line start), 'V' (previous word ends in a vowel),
              'ը' (in ը), or the previous word's final consonant letter.
    next_vowel / pause_after: what follows the word.
    """
    core, cmap = core_of(token)
    segs = segment(core, classical)
    wa = WordAnalysis(token, core, cmap, segs)
    if not segs:
        return wa
    L = len(core)

    def pos(k):
        return segs[k].start if k < len(segs) else L

    vidx = [i for i, s in enumerate(segs) if s.kind == "V"]
    if not vidx:
        if re.search(r"[՚'’]", token):  # elided clitic: կ՚, մ՚, 'ւ (§18)
            wa.variants.append(WordVariant(0))
        else:
            k = 1 if len(segs) > 1 else 0
            wa.variants.append(WordVariant(1, marks=[(pos(k), "ը")]))
        return wa
    word = token.strip("".join(PUNCT_PAUSE) + "՛՜՚'’-")

    natural: list[Ins] = []
    options: list[Opt] = []

    # --- initial cluster
    init = list(range(0, vidx[0]))
    proth_choices: list[tuple[bool, int, str]] = [(False, 0, "")]
    if len(init) >= 2:
        l0, l1 = segs[init[0]].letter, segs[init[1]].letter
        if l0 + l1 in PROTHETIC or (l0 in "սզշ" and l1 in STOPS):
            # §9 p. 31, §17: prothetic ը; the rest is an initial cluster again
            rest = init[1:]
            if len(rest) >= 2:
                natural += [Ins(rest[1], None, "§9 p. 31")] + _medial(segs, rest[1:])
            if prev_end == "start":
                proth_choices = [(True, 0, ""), (False, 0, "")]
            elif prev_end in ("V", "ը"):
                proth_choices = [(False, 0, ""), (True, 1, f"{word}: +ը- (§17 Ա)")]
            else:
                c = 1 if prev_end in EASY_BEFORE_S else 2
                proth_choices = [(True, 0, ""), (False, c, f"{word}: −ը- (§17 Բ)")]
        elif l1 == "յ":
            natural += _medial(segs, init[1:])
        else:
            if len(init) == 2:
                if l0 + l1 in ("հր", "խր"):
                    dc = 0  # §9 p. 31: հրեշտակ is said without ը
                else:
                    dc = 1 if l1 == "ր" else 2  # §14 Ա pp. 41-43
                natural.append(Ins(init[1], dc, "§14 Ա"))
            else:
                natural.append(Ins(init[1], None, "§14 Բ"))  # never dropped
                if segs[init[1]].letter == segs[init[2]].letter:
                    options.append(Opt(+1, 1, f"{word}: +ը (§14 Բ)", add=init[2]))
            natural += _medial(segs, init[1:])

    # --- medial clusters
    for a, b in zip(vidx, vidx[1:]):
        R = list(range(a + 1, b))
        ins = _medial(segs, R)
        letters = "".join(_L(segs, R))
        # §14 Դ p. 47: causative ցն/ցր (զարթեցնել / զարթեցընել); after a
        # consonant the ը is natural (հանգցընել), lighter to drop after ր.
        # ձն/ձր after a consonant: both readings (դարձնել / դարձընել).
        if letters[-2:] in ("ցն", "ցր", "ձն", "ձր") and len(R) >= 2:
            k = R[-1]
            if len(R) == 2 or letters[-2] == "ձ":
                if not any(i.k == k for i in ins):
                    options.append(Opt(+1, 0, "", add=k))
            elif not any(i.k == k for i in ins):
                c = 1 if segs[R[-3]].letter == "ր" else 2
                ins.append(Ins(k, c, "§14 Դ p. 47"))
        if len(R) >= 2 and segs[R[-1]].letter == segs[R[-2]].letter:
            options.append(Opt(+1, 1, f"{word}: +ը (§14 Բ)", add=R[-1]))
        natural += ins

    # --- final cluster
    F = list(range(vidx[-1] + 1, len(segs)))
    fins = _final(segs, F)
    for k in fins:
        last = k == F[-1]
        if next_vowel and not pause_after and last:
            b = segs[k].letter
            if b == "ն":
                c = 0 if len(F) <= 3 else 1  # §15 Գ p. 52-53
            elif b in ("ս", "դ"):
                c = 2  # §15 Դ p. 54
            else:
                c = 1 if len(F) == 2 else 2  # §15 Ե p. 55-56
        else:
            c = 2  # §15 Ա-Բ: "for the eye only"
        natural.append(Ins(k, c, "§15"))
    if len(F) == 2 and not fins and segs[F[-1]].letter in ("ս", "դ", "մ"):
        options.append(Opt(+1, 0, "", add=F[-1]))  # սերըս / սերս, այժըմ

    # --- vowels: dieresis and synizesis (§16 Ա)
    for i, sg in enumerate(segs):
        if sg.kind == "V" and sg.end - sg.start == 2 and sg.letter in ("իւ", "եա", "եօ"):
            options.append(Opt(+1, 1, f"{word}: dieresis (§16 Ա)",
                               marks=[(sg.start + 1, "·")]))
        if sg.kind == "C" and sg.end - sg.start == 2:  # ու read as v
            options.append(Opt(+1, 1, f"{word}: dieresis (§16 Ա)",
                               marks=[(sg.end, "·")]))
        if i + 1 < len(segs) and sg.kind == "V" and segs[i + 1].kind == "V":
            c = 1 if sg.letter == "ի" else 2
            options.append(Opt(-1, c, f"{word}: synizesis (§16 Ա)",
                               marks=[(segs[i + 1].start, "‿")]))

    # dropping natural schwas
    seen_k = set()
    nat = []
    for i in natural:
        if i.k not in seen_k:
            seen_k.add(i.k)
            nat.append(i)
    for i in nat:
        if i.drop_cost is not None:
            options.append(Opt(-1, i.drop_cost,
                               f"{word}: −ը ({i.why})" if i.drop_cost else "",
                               remove=i.k))

    lv = vidx[-1]
    best: dict = {}
    for p_on, p_cost, p_desc in proth_choices:
        for r in range(0, max_options + 1):
            for sub in itertools.combinations(range(len(options)), r):
                cost = p_cost + sum(options[j].cost for j in sub)
                if cost > max_cost:
                    continue
                removed = {options[j].remove for j in sub}
                added = [options[j].add for j in sub if options[j].add is not None]
                ks = sorted({i.k for i in nat if i.k not in removed} | set(added))
                syl = len(vidx) + len(ks) + int(p_on) + sum(
                    options[j].delta for j in sub if options[j].add is None
                    and options[j].remove is None)
                if syl < 1:
                    continue
                marks = [(0, "ը")] if p_on else []
                marks += [(pos(k), "ը") for k in ks]
                lic = [p_desc] if p_desc else []
                for j in sub:
                    marks += options[j].marks
                    if options[j].desc:
                        lic.append(options[j].desc)
                after = [k for k in ks if k > lv]
                if after:
                    fu, mid = True, segs[max(after) - 1].start
                elif segs[lv].letter == "ը" and lv > 0:
                    fu = True
                    mid = segs[lv - 1].start if segs[lv - 1].kind == "C" else segs[lv].start
                else:
                    fu, mid = False, None
                if syl < 2:
                    mid = None
                key = (syl, fu, mid)
                if key not in best or cost < best[key].cost:
                    best[key] = WordVariant(syl, cost, marks, lic, fu, mid)
    wa.variants = sorted(best.values(), key=lambda v: v.cost)
    return wa


def end_type(token: str, classical: bool = False) -> str:
    """How a word ends, for the next word's context: 'V', 'ը' or a consonant."""
    core, _ = core_of(token)
    segs = segment(core, classical)
    if not segs:
        return "start"
    s = segs[-1]
    if s.kind == "V":
        return "ը" if s.letter == "ը" else "V"
    return s.letter
