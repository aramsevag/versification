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
(group size limits, default 2–5), `--prothesis both|always|never` (ստանալ = ըստանալ?).

## How it works

1. **Syllabification** (`armverse/phonology.py`). One syllable per vowel (ա ե է ը ի ո օ ու, և = եվ),
   plus the **unwritten schwa** restored by rule:
   initial clusters (սրտիս → սըրտիս, դրոշ → դըրոշ), medial obstruent+sonorant in 3+ clusters
   (դարձնել → դարձընել, անձրև → անձըրև), final rising clusters (բարձր → բարձըր).
   The linking article ն takes no schwa before a vowel (դաշտն ուր). Classical orthography:
   իւ, եա = one vowel; ու before a vowel = v (Աստուած). The prothetic ը of ստ-/սպ-/շտ-… is
   treated as optional and resolved per poem.
2. **Candidate segmentations** (`armverse/scan.py`). Each line is cut into rhythmic groups at
   word boundaries — never after a proclitic (մի, ի…) or before an enclitic (է, եմ, էլ…).
3. **Poem-level choice** (`armverse/meter.py`). A line alone is often ambiguous (the example
   also fits 4|3|4), so the pattern admitted by the most lines in the poem wins; ties prefer
   fewer groups, no group longer than the one before it (4|4|3), and balanced groups.
   Lines outside the poem's main meters are marked `*`.

## Limitations / ideas
- Syllable rules follow standard Eastern Armenian pronunciation; poets' licences
  (elisions marked with ՚, archaisms) may need extra rules — add failing words to `tests/`.
- Only group *sizes* are detected; stress-foot (iamb/trochee/anapest) analysis and rhyme
  detection would be natural next steps.

Run tests: `python3 -m unittest`
