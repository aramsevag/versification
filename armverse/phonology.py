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

import itertools
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
    """Heuristic: does the text use classical (Mashtotsian) orthography, as in
    Western Armenian and pre-1922 poetry?  Markers: ւ outside ու (իւ, աւ, եւ+),
    եա (except modern -եական), word-internal է (սիրէ), Western կը / մը."""
    for w in re.findall(r"[\u0531-\u0587]+", text.lower()):
        if w in ("կը", "մը"):
            return True
        if w != "եւ" and re.search(r"(?<!ո)ւ", w):
            return True
        if re.search(r"եա(?!կան)", w) or (len(w) > 1 and "է" in w[1:]):
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
    syllables: int
    cost: int = 0  # number of poetic licences used
    marks: list[tuple[int, str]] = field(default_factory=list)  # (core idx, text)
    licences: list[str] = field(default_factory=list)
    prothesis: bool = False


@dataclass
class WordAnalysis:
    token: str
    core: str
    core_map: list[int]  # core index -> token index
    segs: list[Seg]
    variants: list[WordVariant] = field(default_factory=list)

    def _tok_index(self, ci: int) -> int:
        if not self.core_map:
            return len(self.token)
        if ci < len(self.core_map):
            return self.core_map[ci]
        return self.core_map[-1] + 1

    def render(self, v: int = 0) -> str:
        """Token with restored ը visible; dieresis shown as ·, syneresis as ‿."""
        var = self.variants[v]
        out = self.token
        for ci, text in sorted(var.marks, key=lambda m: m[0], reverse=True):
            p = self._tok_index(ci)
            if (text == "ը" and ci == 0 and p < len(out) and out[p].isupper()):
                out = out[:p] + "Ը" + out[p].lower() + out[p + 1:]
            else:
                out = out[:p] + text + out[p:]
        return out


def _ins_pos(segs: list[Seg], k: int, core_len: int) -> int:
    return segs[k].start if k < len(segs) else core_len


def analyze_word(token: str, next_vowel: bool = False, classical: bool = False,
                 prothesis: str = "both", max_licences: int = 2) -> WordAnalysis:
    """Analyze one word.

    Returns all pronunciation variants: variant 0 is the default reading; the
    others use up to ``max_licences`` poetic licences:
      * dropping an unwritten schwa      (նման = 1 syllable instead of նըման)
      * adding a schwa in a cluster      (Աստղերու -> Աստըղերու)
      * dieresis of a diphthong          (classical Ովկեանի = Ով-կե-ա-նի)
      * syneresis of a hiatus            (միայն = մյայն)
    The prothetic ը (ստանալ / ըստանալ) is free in both directions
    (prothesis='both'), or forced with 'always' / 'never'.
    Written ը is always pronounced.
    """
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
    L = len(core)
    vidx = [i for i, s in enumerate(segs) if s.kind == "V"]
    nv = len(vidx)

    if nv == 0:
        # consonant-only token: elided clitic (կ՚, մ՚) -> 0 syllables if
        # marked with an apostrophe, otherwise give it one schwa.
        if re.search(r"[՚'’]", token):
            wa.variants.append(WordVariant(0))
        else:
            k = 1 if len(segs) > 1 else 0
            wa.variants.append(WordVariant(1, marks=[(_ins_pos(segs, k, L), "ը")]))
        return wa

    default: list[int] = []
    optional_add: list[int] = []
    for a, b in zip(vidx, vidx[1:]):
        run = list(range(a + 1, b))
        ins = _medial(run, segs)
        default += ins
        if len(run) >= 3 and not ins:
            optional_add.append(run[-1])
    frun = list(range(vidx[-1] + 1, len(segs)))
    fins = _final(frun, segs, next_vowel)
    default += fins
    if (len(frun) >= 2 and not fins and segs[frun[-1]].letter == "ղ"
            and segs[frun[-2]].cls == "O"):
        optional_add.append(frun[-1])  # աստղ -> աստըղ

    init = list(range(0, vidx[0]))
    proth_choices: list[tuple[list[int], bool]] = [([], False)]
    if len(init) >= 2:
        c1, c2 = segs[init[0]], segs[init[1]]
        if c1.letter in ("ս", "շ", "զ") and c2.letter in STOPS:
            rest = _medial(init[1:], segs) if len(init) > 2 else []
            default += rest
            opts = {"always": [([0], True)], "never": [([], False)]}
            proth_choices = opts.get(prothesis, [([0], True), ([], False)])
        elif c2.cls == "G":
            default += _medial(init[1:], segs)
        else:
            default += [init[1]] + _medial(init[1:], segs)
    default = sorted(set(default))

    # optional licences: (cost, delta, marks_add, schwa_removed, description)
    options: list[tuple[int, list[tuple[int, str]], int | None, str]] = []
    for k in default:
        options.append((-1, [], k, "−ը"))
    for k in optional_add:
        options.append((+1, [(_ins_pos(segs, k, L), "ը")], None, "+ը"))
    for i, sg in enumerate(segs):
        if sg.kind == "V" and sg.end - sg.start == 2 and sg.letter in ("իւ", "եա", "եօ"):
            options.append((+1, [(sg.start + 1, "·")], None, "dieresis"))
        if sg.kind == "C" and sg.end - sg.start == 2:  # ու read as v
            options.append((+1, [(sg.end, "·")], None, "dieresis"))
        if i + 1 < len(segs) and sg.kind == "V" and segs[i + 1].kind == "V":
            options.append((-1, [(segs[i + 1].start, "‿")], None, "syneresis"))

    subsets: list[tuple[int, ...]] = [()]
    for r in range(1, max_licences + 1):
        subsets += list(itertools.combinations(range(len(options)), r))

    seen = set()
    for pins, is_p in proth_choices:
        for sub in subsets:
            removed = {options[j][2] for j in sub if options[j][2] is not None}
            ins = [k for k in default if k not in removed]
            marks = [(0, "ը")] if pins else []
            marks += [(_ins_pos(segs, k, L), "ը") for k in ins]
            delta = 0
            lic = []
            for j in sub:
                d, m, _, desc = options[j]
                delta += d
                marks += m
                lic.append(f"{token.strip(PUNCT)}: {desc}")
            syl = nv + len(ins) + len(pins) + delta
            key = (syl, len(sub))
            if syl < 1 or key in seen:
                continue  # keep the first (simplest) way to reach a count
            seen.add(key)
            wa.variants.append(WordVariant(syl, len(sub), marks, lic, is_p))
    return wa


PUNCT = "\u055A\u055B\u055C\u055D\u055E\u055F\u0589,.;:!?«»\"'’()—–-…"
