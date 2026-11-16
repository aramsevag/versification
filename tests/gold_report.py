"""Score the scanner against tests/data/gold.txt.  Run: python3 -m tests.gold_report"""
from pathlib import Path

from armverse import scan_poem
from armverse.meter import CATALOGUE

GOLD = Path(__file__).parent / "data" / "gold.txt"


def load():
    poems, cur = [], []
    for line in GOLD.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        if line.strip() == "***":
            poems.append(cur); cur = []
            continue
        text, exp = line.rsplit(" = ", 1)
        cur.append((text, tuple(int(x) for x in exp.split("/"))))
    poems.append(cur)
    return [p for p in poems if p]


def run(verbose=True, **kw):
    ok = total = 0
    for poem in load():
        r = scan_poem("\n".join(t for t, _ in poem), **kw)
        for line, (_, exp) in zip(r.lines, poem):
            total += 1
            good = line.pattern == exp
            ok += good
            if verbose:
                got = "/".join(map(str, line.pattern or ()))
                print(f"{'✓' if good else '✗'} {line.marked:<70} {got:<9} "
                      f"(expected {'/'.join(map(str, exp))})"
                      + (f"  [{'; '.join(line.licences)}]" if line.licences else ""))
    if verbose:
        print(f"\n{ok}/{total} lines correct")
    return ok, total


if __name__ == "__main__":
    run()
