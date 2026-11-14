"""Command-line interface.

    armverse scan poem.txt               # print scanned lines
    armverse line "Ահա սրտիս խոպան դաշտն ուր մի անգամ"
    armverse corpus poems/ --out results/  # batch: CSV + JSON reports
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

from .meter import PoemResult, fmt, scan_poem


def _opts(p: argparse.ArgumentParser):
    p.add_argument("--orthography", choices=["auto", "modern", "classical"],
                   default="auto")
    p.add_argument("--min-group", type=int, default=2)
    p.add_argument("--max-group", type=int, default=5)
    p.add_argument("--prothesis", choices=["both", "always", "never"],
                   default="both",
                   help="prothetic ը in initial ս/շ/զ+stop (ստանալ -> ըստանալ)")


def _kw(a):
    return dict(orthography=a.orthography, min_group=a.min_group,
                max_group=a.max_group, prothesis=a.prothesis)


def print_poem(r: PoemResult, out=sys.stdout):
    if r.title:
        print(f"== {r.title}", file=out)
    stanza = None
    for l in r.lines:
        if stanza is not None and l.stanza != stanza:
            print(file=out)
        stanza = l.stanza
        flag = "" if l.regular else "  *"
        print(f"{l.marked:<60} {fmt(l.pattern)}{flag}", file=out)
    meters = ", ".join(f"{fmt(p)} ×{c}" for p, c in r.meters)
    print(f"-- meters: {meters}; regularity {r.regularity:.0%}"
          f"{'; classical orthography' if r.classical else ''}", file=out)


def split_poems(text: str, sep: str | None):
    if not sep:
        return [text]
    chunks, cur = [], []
    for line in text.splitlines():
        if line.strip() == sep:
            chunks.append("\n".join(cur))
            cur = []
        else:
            cur.append(line)
    chunks.append("\n".join(cur))
    return [c for c in chunks if c.strip()]


def main(argv=None):
    ap = argparse.ArgumentParser(prog="armverse",
                                 description="Armenian verse rhythm analyzer")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("line", help="scan a single line")
    p.add_argument("text")
    _opts(p)

    p = sub.add_parser("scan", help="scan poem file(s) and print")
    p.add_argument("files", nargs="+")
    p.add_argument("--separator", help="line that separates poems in a file, e.g. ***")
    _opts(p)

    p = sub.add_parser("corpus", help="batch-analyze a folder of .txt poems")
    p.add_argument("folder")
    p.add_argument("--out", default="armverse_results")
    p.add_argument("--separator")
    p.add_argument("--glob", default="**/*.txt")
    _opts(p)

    a = ap.parse_args(argv)
    kw = _kw(a)

    if a.cmd == "line":
        r = scan_poem(a.text, **kw)
        l = r.lines[0]
        print(f"{l.marked}  {fmt(l.pattern)}")
        alts = sorted(l.analysis.candidates, key=lambda p: (len(p), p))
        print("other possible segmentations:", ", ".join(
            "|".join(map(str, p)) for p in alts if p != l.pattern) or "none")
        return

    if a.cmd == "scan":
        for f in a.files:
            text = Path(f).read_text(encoding="utf-8")
            for k, chunk in enumerate(split_poems(text, a.separator)):
                title = Path(f).name + (f"#{k + 1}" if a.separator else "")
                print_poem(scan_poem(chunk, title=title, **kw))
                print()
        return

    # corpus
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    files = sorted(Path(a.folder).glob(a.glob))
    line_rows, poem_rows = [], []
    meter_lines, meter_poems = Counter(), Counter()
    poems_json = []
    for f in files:
        text = f.read_text(encoding="utf-8")
        for k, chunk in enumerate(split_poems(text, a.separator)):
            title = str(f.relative_to(a.folder)) + (f"#{k + 1}" if a.separator else "")
            r = scan_poem(chunk, title=title, **kw)
            if not r.lines:
                continue
            for l in r.lines:
                line_rows.append({
                    "poem": title, "stanza": l.stanza, "line": l.number,
                    "text": l.text, "scansion": l.marked,
                    "syllables": sum(l.pattern) if l.pattern else "",
                    "pattern": "|".join(map(str, l.pattern)) if l.pattern else "",
                    "regular": int(l.regular),
                    "alternatives": len(l.analysis.candidates),
                })
                if l.pattern:
                    meter_lines[fmt(l.pattern)] += 1
            dominant = fmt(r.meters[0][0]) if r.meters else "?"
            meter_poems[dominant] += 1
            poem_rows.append({
                "poem": title, "lines": len(r.lines),
                "dominant_meter": dominant,
                "meters": "; ".join(f"{fmt(p)}×{c}" for p, c in r.meters),
                "regularity": round(r.regularity, 3),
                "stanza_schemes": " / ".join("".join(s) for s in r.stanza_schemes()),
                "orthography": "classical" if r.classical else "modern",
            })
            poems_json.append({**poem_rows[-1], "scanned_lines": [
                row for row in line_rows if row["poem"] == title]})

    def write_csv(name, rows):
        if not rows:
            return
        with open(out / name, "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)

    write_csv("lines.csv", line_rows)
    write_csv("poems.csv", poem_rows)
    write_csv("meter_frequency.csv", [
        {"meter": m, "lines": c, "poems_dominant": meter_poems.get(m, 0)}
        for m, c in meter_lines.most_common()])
    (out / "poems.json").write_text(
        json.dumps(poems_json, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(poem_rows)} poems, {len(line_rows)} lines -> {out}/")
    for m, c in meter_lines.most_common(15):
        print(f"  {m:<20} {c:>6} lines   dominant in {meter_poems.get(m, 0)} poems")


if __name__ == "__main__":
    main()
