# armverse — Armenian versification analyzer

Feed it Armenian poems and it outputs the rhythm (syllable-group pattern) of every line,
e.g. `Ահա սըրտիս | խոպան դաշտն ուր | մի անգամ  11 (4|4|3)`, plus the poem's
dominant meter(s), regularity, and per-stanza schemes. Pure Python, no dependencies.

## Usage

```bash
pip install -e .            # or run as: python3 -m armverse.cli ...

armverse line "Ահա սրտիս խոպան դաշտն ուր մի անգամ"
armverse scan examples/mer_hayrenik.txt
armverse corpus my_poems/ --out results/     # batch over **/*.txt
```

`corpus` writes:
- `lines.csv` – every line: text, scansion with restored ը, syllables, pattern, regular?
- `poems.csv` – per poem: dominant meter, all meters with counts, regularity, stanza schemes (e.g. `ABAB / ABAB`)
- `meter_frequency.csv` – how often each meter occurs across the corpus
- `poems.json` – everything above, nested

Input: one poem per `.txt` file (UTF-8), stanzas separated by blank lines, lines starting
with `#` ignored (titles, authors). Several poems in one file: `--separator "***"`.

Options: `--orthography auto|modern|classical` (auto-detected), `--min-group/--max-group`
(member size limits, default 2–5), `--max-cost` (licence budget per line), `--strict-members`.

## How it works

The rules follow Manuk Abeghyan, *Հայոց լեզվի տաղաչափություն* (1971 edition). They are
listed with page references in **[RULES.md](RULES.md)**, which also marks every place where
the program makes its own choice.

1. **Syllables** (`armverse/phonology.py`). Each word gets every reading the rules allow, each
   with a cost: 0 for natural pronunciation (the unwritten ը restored: ճըրագ, մըկըրտիչ, աստըղ,
   սիրտըս), 1 for a light licence, 2 for a heavy one. Licences are dropping or adding ը,
   dieresis and synizesis, as graded by Abeghyan (§§14–18).
2. **Members** (`armverse/scan.py`). A line is cut into members of 2–5 syllables. A member
   ends on a stressed syllable, so a cut can fall inside a word before its unstressed final
   syllable (ձեռ|քըդ, §30.3). Cuts after an unstressed ending (Ու փչում է | աշնան) cost 1;
   `--strict-members` forbids them.
3. **Meter** (`armverse/meter.py`). The poem's meter is the pattern its lines share, with a bonus
   for meters Abeghyan catalogues (8 = 4+4, 11 = 4+4+3, 20 = 5+5+5+5 …). A line uses a licence
   only if that brings it into the poem's meter. Every licence used is printed next to the line.

## Testing

- `python3 -m unittest` runs Abeghyan's own word examples and the hand-scanned lines.
- `python3 -m tests.gold_report` prints the line-by-line comparison with
  `tests/data/gold.txt`. Add your own hand scansions there to measure accuracy.

Not yet handled: «Հայրենի կարգ», ashugh meters, purely stress-based and free verse (see
RULES.md §6).
