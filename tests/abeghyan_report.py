"""Measure the scanner against example lines from Abeghyan's meter catalogue.
    python3 -m tests.extract_abeghyan OCR.txt lines.tsv
    python3 -m tests.abeghyan_report lines.tsv [section]
Each quoted excerpt (consecutive verse lines) is scanned on its own, as a poem.
Expected values come from the section titles (Part 2):"""
import sys
from collections import defaultdict

from armverse import scan_poem

# section -> (syllables, accepted member patterns or None = count only)
EXPECTED = {
    42: (4, {(4,)}), 43: (8, {(4, 4)}), 44: (12, {(4, 4, 4)}),
    45: (16, {(4, 4, 4, 4)}), 46: (7, {(4, 3), (3, 4)}),
    47: (11, {(4, 4, 3), (3, 4, 4)}), 48: (15, {(4, 4, 4, 3)}),
    49: (14, {(4, 3, 4, 3)}), 50: (12, {(3, 4, 5)}), 51: (9, {(4, 5), (5, 4)}),
    52: (13, {(4, 4, 5), (5, 4, 4)}), 56: (9, {(3, 3, 3)}),
    57: (12, {(3, 3, 3, 3)}), 38: (11, {(3, 3, 2, 3)}), 59: (11, {(5, 3, 3), (2, 3, 3, 3)}),
    53: (11, {(4, 2, 5), (4, 2, 3, 2), (4, 2, 2, 3), (2, 4, 5), (5, 4, 2)}),
    60: (8, {(2, 3, 3)}), 62: (11, {(3, 3, 3, 2), (3, 3, 2, 3)}),
    64: (5, {(5,)}), 65: (10, {(5, 5)}), 66: (15, {(5, 5, 5)}),
    67: (20, {(5, 5, 5, 5)}),
}


def load(path):
    rows = defaultdict(list)
    for line in open(path, encoding="utf-8").read().splitlines()[1:]:
        sec, excerpt, author, text = line.split("\t")
        sec = int(sec)
        if sec not in EXPECTED:
            continue
        n = EXPECTED[sec][0]
        if not (n * 2 <= len(text) <= n * 5 + 10):  # prose / wrapped lines
            continue
        rows[sec].append((excerpt, text))
    return rows


def main(path, only=None):
    tot = good_syl = good_pat = 0
    for sec, texts in sorted(load(path).items()):
        if only and sec != int(only):
            continue
        n, pats = EXPECTED[sec]
        groups = defaultdict(list)
        for ex, t in texts:
            groups[ex].append(t)
        scanned = [l for g in groups.values() for l in scan_poem("\n".join(g)).lines]
        s_ok = sum(1 for l in scanned if l.pattern and sum(l.pattern) == n)
        p_ok = sum(1 for l in scanned if l.pattern in pats)
        tot += len(scanned); good_syl += s_ok; good_pat += p_ok
        print(f"§{sec:<3} {n:>2} syl  lines {len(scanned):>3}  "
              f"count ok {s_ok:>3}  scheme ok {p_ok:>3}")
        if only:
            for l in scanned:
                mark = "✓" if l.pattern in pats else ("~" if l.pattern and sum(l.pattern) == n else "✗")
                print(f"  {mark} {l.marked:<55} {'/'.join(map(str, l.pattern or ()))}"
                      + (f"  [{'; '.join(l.licences)}]" if l.licences else ""))
    print(f"\nall: {tot} lines, syllable count ok {good_syl} ({good_syl/tot:.0%}), "
          f"scheme ok {good_pat} ({good_pat/tot:.0%})")


if __name__ == "__main__":
    main(*sys.argv[1:])
