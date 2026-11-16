"""Extract example verse lines from the meter catalogue (Part 2) of the OCR of
Abeghyan's Տաղաչափություն.  Usage:
    python3 -m tests.extract_abeghyan OCR.txt OUT.tsv
Output columns: section, excerpt (consecutive verse lines), author, line.
The OCR's stress (՛) and division marks (] [ / |) are removed; they are not
reliable enough to use as expected divisions."""
import re
import sys

SECTION = re.compile(r"^(\d{1,3})\. (.*?)(\d+)-[:]?վա[նճ]կանի")
OCR_SECTION_FIX = {538: 53}  # «538. Յամբական երկանդամ 11-վաճկանի»
SCHEME = re.compile(r"Սքեման(?: է)?՝?\s*([\d+=() ]+)")
AUTHOR = re.compile(r"\(([^()]{2,40}?)\.?\)\s*[։.]?\s*$")
ARM = re.compile(r"[Ա-և]")


def clean(line):
    line = AUTHOR.sub("", line)
    line = re.sub(r"[\]\[/|1Ո]+(?=\s|$)|(?<=\s)[\]\[/|1]+", " ", line)
    line = line.replace("՛", "").replace("]", " ").replace("[", " ").replace("/", " ")
    line = re.sub(r"\s+", " ", line).strip(" -")
    return line


def is_verse(line, prev):
    s = line.strip()
    if not s or not ARM.search(s) or s.startswith("=====") or re.match(r"^- ?\d+ ?-?$", s):
        return False
    if s.endswith("-") or len(s) > 75 or len(s) < 12:
        return False
    if not re.match(r"^[«(]?[Ա-Ֆ]", s):  # verse lines start with a capital
        return False
    if re.search(r"\d", AUTHOR.sub("", s)) or "§" in s:
        return False
    # prose paragraphs: previous line is a hyphen-broken or long prose line
    p = prev.strip()
    if p.endswith("-") and len(p) > 55:
        return False
    return True


def main(src, dst):
    lines = open(src, encoding="utf-8").read().splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("40. Յամբական"))
    end = next(i for i, l in enumerate(lines) if l.startswith("79. Աշուղական"))
    sec = syl = scheme = None
    out = []
    excerpt, was_verse = 0, False
    for i in range(start, end):
        l = lines[i]
        m = SECTION.match(l)
        if m:
            sec, syl, scheme = int(m.group(1)), int(m.group(3)), ""
            sec = OCR_SECTION_FIX.get(sec, sec)
            excerpt += 1
            continue
        m = SCHEME.search(l + " " + (lines[i + 1] if i + 1 < len(lines) else ""))
        if m and not scheme:
            scheme = re.sub(r"\s", "", m.group(1)).split("=")[0]
        if l.startswith("=====") or not l.strip() or re.match(r"^- ?\d+ ?-?$", l.strip()):
            continue  # page breaks don't end an excerpt
        v = bool(sec) and is_verse(l, lines[i - 1])
        if v:
            if not was_verse:
                excerpt += 1  # consecutive verse lines = one quoted excerpt
            a = AUTHOR.search(l)
            out.append((sec, excerpt, a.group(1) if a else "", clean(l)))
        was_verse = v
    with open(dst, "w", encoding="utf-8") as f:
        f.write("section\texcerpt\tauthor\tline\n")
        for r in out:
            f.write("\t".join(map(str, r)) + "\n")
    print(f"{len(out)} lines")


if __name__ == "__main__":
    main(*sys.argv[1:3])
