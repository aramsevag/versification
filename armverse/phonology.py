"""Armenian grapheme -> phonological segments, and syllable counting.

The main difficulty of counting syllables in Armenian is the *unwritten schwa*
(ը).  Orthography omits it inside consonant clusters, but it is pronounced and
counts as a syllable in verse:

    սրտիս  -> սըրտիս   (2)     դրոշ    -> դըրոշ     (2)
    մկրտել -> մըկըրտել (3)     բարձր   -> բարձըր    (2)
    դարձնել -> դարձընել (3)    անձրև   -> անձըրև    (3)

Rules implemented (Eastern Armenian pronunciation, which also matches most
classical-orthography poetry):

1. Word-initial cluster C1C2...: schwa after C1 (սըրտիս), except
   - C1 + յ (գյուղ) -> no schwa;
   - ս/շ/զ + stop (ստանալ): a *prothetic* schwa before the word (ըստանալ).
     This one is optional in verse, so both variants are produced and the
     poem-level meter fit chooses.
2. Medial clusters of 3+ consonants: schwa between an obstruent and a
   following sonorant (դարձընել, անձըրև); otherwise a cluster is allowed
   if it splits into a coda of <=2 non-rising consonants + 1 onset
   (Աստված, մարդկային).
3. Word-final clusters: schwa before a final sonorant preceded by a less
   sonorous consonant (բարձըր, դաշտըն) -- unless the next word begins with
   a vowel, in which case the consonant links to it (դաշտն ուր).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

VOWEL_LETTERS = set("աեէըիոօ")
STOPS = set("բգդթկպտփքձծջճչց")
FRICATIVES = set("վֆսզշժխղհւ")
NASALS = set("մն")
LIQUIDS = set("րռլ")
GLIDES = set("յ")
CONSONANT_LETTERS = STOPS | FRICATIVES | NASALS | LIQUIDS | GLIDES
ARMENIAN_LETTERS = VOWEL_LETTERS | CONSONANT_LETTERS | {"և"}

SONORITY = {"O": 1, "N": 2, "L": 3, "G": 4}


def _cclass(ch: str) -> str:
    if ch in NASALS:
        return "N"
    if ch in LIQUIDS:
        return "L"
    if ch in GLIDES:
        return "G"
    return "O"  # obstruent: stops, affricates, fricatives


@dataclass
class Seg:
    kind: str  # "V" or "C"
    start: int  # index into the core string
    end: int
    cls: str = ""  # for consonants: O/N/L/G
    letter: str = ""


def is_classical(text: str) -> bool:
    """Heuristic: classical (Mashtotsian) orthography uses ւ outside of ու."""
    for w in re.findall(r"[Ա-և]+", text.lower()):
        if w == "եւ":
            continue  # also used in reformed spelling
        if re.search(r"(?<!ո)ւ", w):
            return True
    return False


def _vowel_starts_at(core: str, j: int) -> bool:
    return j < len(core) and (core[j] in VOWEL_LETTERS or core[j] == "և")


def segment(core: str, classical: bool = False) -> list[Seg]:
    segs: list[Seg] = []
    i, n = 0, len(core)
    while i < n:
        c = core[i]
        nxt = core[i + 1] if i + 1 < n else ""
        if c == "ո" and nxt == "ւ":
            prev_is_cons = bool(segs) and segs[-1].kind == "C"
            if prev_is_cons and _vowel_starts_at(core, i + 2):
                segs.append(Seg("C", i, i + 2, "O", "վ"))  # Աստուած: ու = v
            else:
                segs.append(Seg("V", i, i + 2, letter="ու"))
            i += 2
        elif c == "ի" and nxt == "ւ":  # classical իւ = yu
            segs.append(Seg("V", i, i + 2, letter="իւ"))
            i += 2
        elif classical and c == "ե" and nxt in ("ա", "օ"):  # classical եա = ya
            segs.append(Seg("V", i, i + 2, letter=c + nxt))
            i += 2
        elif c == "և":
            segs.append(Seg("V", i, i + 1, letter="ե"))
            segs.append(Seg("C", i + 1, i + 1, "O", "վ"))
            i += 1
        elif c in VOWEL_LETTERS:
            segs.append(Seg("V", i, i + 1, letter=c))
            i += 1
        elif c in CONSONANT_LETTERS:
            segs.append(Seg("C", i, i + 1, _cclass(c), c))
            i += 1
        else:
            i += 1
    return segs


def _son(s: Seg) -> int:
    return SONORITY[s.cls]


def _medial(run: list[int], segs: list[Seg]) -> list[int]:
    """Schwa insertion points (segment indices to insert *before*) in a
    consonant run that sits between two vowels."""
    if len(run) <= 2:
        return []
    for a, b in zip(run, run[1:]):
        if segs[a].cls == "O" and segs[b].cls in "NL":
            k = run.index(b)
            return [b] + _medial(run[:k], segs) + _medial(run[k:], segs)
    if len(run) == 3 and _son(segs[run[0]]) >= _son(segs[run[1]]):
        return []  # coda of 2 falling/level + onset of 1: Աստված, մարդկային
    return [run[1]] + _medial(run[1:], segs)


def _final(run: list[int], segs: list[Seg], link: bool) -> list[int]:
    """Insertion points in a word-final cluster."""
    if len(run) < 2:
        return []
    last, prev = segs[run[-1]], segs[run[-2]]
    if last.cls in "NL" and _son(last) > _son(prev):
        if link:  # final consonant becomes onset of next word: դաշտն ուր
            return _final(run[:-1], segs, False)
        return [run[-1]] + _final(run[:-1], segs, False)
    return []


@dataclass
class WordVariant:
    insertions: list[int]  # segment indices; len(segs) means "at the end"
    syllables: int
    prothesis: bool = False


@dataclass
class WordAnalysis:
    token: str
    core: str
    core_map: list[int]  # core index -> token index
    segs: list[Seg]
    variants: list[WordVariant] = field(default_factory=list)

    def render(self, v: int = 0) -> str:
        """Token with inserted ը made visible."""
        var = self.variants[v]
        pos_in_token = []
        for k in var.insertions:
            if k < len(self.segs):
                ci = self.segs[k].start
                pos_in_token.append(self.core_map[ci] if ci < len(self.core_map)
                                    else self.core_map[-1] + 1)
            else:
                pos_in_token.append(self.core_map[-1] + 1 if self.core_map else len(self.token))
        out = self.token
        for p in sorted(pos_in_token, reverse=True):
            schwa = "ը"
            if p < len(out) and out[p].isupper() and p == (self.core_map[0] if self.core_map else 0):
                out = out[:p] + "Ը" + out[p].lower() + out[p + 1:]
                continue
            out = out[:p] + schwa + out[p:]
        return out


def analyze_word(token: str, next_vowel: bool = False, classical: bool = False,
                 prothesis: str = "both") -> WordAnalysis:
    """prothesis: 'both' (ambiguous, default), 'always', 'never'."""
    low = token.lower()
    core_chars, core_map = [], []
    for i, ch in enumerate(low):
        if ch in ARMENIAN_LETTERS:
            core_chars.append(ch)
            core_map.append(i)
    core = "".join(core_chars)
    segs = segment(core, classical)
    wa = WordAnalysis(token, core, core_map, segs)
    if not segs:
        return wa

    nv = sum(1 for s in segs if s.kind == "V")
    vidx = [i for i, s in enumerate(segs) if s.kind == "V"]

    if nv == 0:  # consonant-only token (rare): give it one schwa
        wa.variants.append(WordVariant([1 if len(segs) > 1 else 0], 1))
        return wa

    base: list[int] = []
    # medial runs
    for a, b in zip(vidx, vidx[1:]):
        base += _medial(list(range(a + 1, b)), segs)
    # final run
    base += _final(list(range(vidx[-1] + 1, len(segs))), segs, next_vowel)

    # initial run
    init = list(range(0, vidx[0]))
    variants: list[tuple[list[int], bool]] = []
    if len(init) >= 2:
        c1, c2 = segs[init[0]], segs[init[1]]
        if c1.letter in ("ս", "շ", "զ") and c2.letter in STOPS:
            rest = _medial(init[1:], segs) if len(init) > 2 else []
            with_p = ([0] + rest, True)
            without = (rest, False)
            if prothesis == "always":
                variants = [with_p]
            elif prothesis == "never":
                variants = [without]
            else:
                variants = [with_p, without]
        elif c2.cls == "G":
            variants = [(_medial(init[1:], segs), False)]
        else:
            variants = [([init[1]] + _medial(init[1:], segs), False)]
    else:
        variants = [([], False)]

    for ins, p in variants:
        allins = sorted(set(ins + base))
        wa.variants.append(WordVariant(allins, nv + len(allins), p))
    return wa
