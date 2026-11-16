# Scansion rules used by armverse

Every rule cites Manuk Abeghyan, *Հայոց լեզվի տաղաչափություն* (Երկեր, հ. Ե, 1971).
Page numbers are those printed in that edition. Where the program departs from
Abeghyan, or where he leaves the question open, this is marked **[choice]**:
these are the places to check.

## 1. Syllables in natural pronunciation (cost 0)

One syllable per vowel: ա ե է ը ի ո օ ու; և = եվ. Diphthongs with the glide յ count as
one syllable, including classical եա, եօ, իւ = յա, յո, յու (§9, p. 33).
ու before a vowel is the consonant v (լեզվի, Աստուած) (§16 Ա, p. 59).

The unwritten ը is restored as follows.

| Position | Rule | Examples | Ref |
|---|---|---|---|
| Word start, 2 consonants | ը between them | ճըրագ, վըրեժ, դըրոշ, նըման | §9 p. 31; §14 Ա p. 41 |
| Word start, 3+ consonants | ը after the 1st, then as medial | տըրտում, մըկըրտիչ, քըրթմընջյուն | §9 p. 31; §14 Բ p. 44 |
| Word start, C + յ | no ը | գյուղ, բյուր | §9 p. 33 |
| Word start, զբ զգ զմ սկ սպ սք ստ սթ շպ շտ | prothetic ը (+1 syllable) after a consonant; none after a vowel (նա-ս-պասում) | ըստեղծել, ըսկըսել | §9 p. 31; §17 p. 61 |
| Inside a word | A syllable begins with at most 1 consonant (or C+յ) and ends with at most 2. If 2, the first must be ր ռ ն մ ղ խ վ զ ս ժ շ հ (or յ), and the second must not be ն ր ռ վ շ. Otherwise ը is inserted. | զարթ-նել, անձ-նական, ամպ-րոպ, ընկ-նել, դարձ-նել | §9 pp. 31–32 |
| C C վ | ը before վ | զըսպըվել, Աստըված | §14 Գ p. 45 |
| Word end | ը before a final ն ր ռ վ շ that follows a consonant (not յ); before ղ after a stop; in any 3-consonant cluster unless it ends in ք; when 2 consonants can't close a syllable | դառըն, բարձըր, աստըղ, կոճըղ, սիրտըս, ձեռքըդ, հացըս | §5 p. 20; §9 p. 32; §15 p. 48 |
| Word end, 3 consonants ending in ք | allowed | պարտք, կուրծք | §9 p. 32 |

Written ը is always pronounced (§14, p. 41: «Ոտանավորի մեջ չսղված Ը ձայնավորը գրվում է»).

## 2. Equally natural alternatives (cost 0)

Abeghyan accepts both readings in these cases, so the poem's meter decides:

- **Line-initial prothesis**: ըստանալ / ստանալ (§17, p. 61: «խոսքի սկզբում միշտ կարելի է և՛ սղել, և՛ չսղել»).
- **ը before վ after a valid coda**: Աստված / Աստըված, ջարդված / ջարդըված. The elision is "always possible" when the first two consonants can close a syllable (§14 Գ, p. 46).
- **ցն, ցր, ձն between vowels**: զարթեցնել / զարթեցընել (§14 Դ, p. 47).
- **Final ն article before a vowel, linked**: աղջիկն ասաց = աղջի-կնասաց (§15 Գ, p. 52).
- **Final ս, դ, մ after a consonant that can close a syllable with them**: սերս / սերըս, այժմ / այժըմ. **[choice]** Abeghyan treats the article -ս/-դ as a separate ը-syllable (սերըս, p. 51), but lexical words like ներս, մարդ, բերդ are one syllable. The program can't tell an article from a word ending, so it leaves both readings open.

## 3. Licences: light (cost 1) and heavy (cost 2)

Abeghyan describes many elisions as poets' licences. He calls some easy and others
"unnatural" or "for the eye only". The program allows all of them, at a cost, and lists
every licence used next to the line.

| Licence | Cost | Ref |
|---|---|---|
| Drop the initial ը, when the second consonant is ր (դրոշ, հրաշք) | 1 | §14 Ա p. 43 |
| Drop the initial ը, otherwise (նման = 1 syllable, զվարթ, խլել) | 2 | §14 Ա pp. 41–42 |
| Drop the prothetic ը after ն մ ր ռ վ խ ղ գ կ ք | 1 | §17 Բ pp. 62–63 |
| Drop the prothetic ը after other consonants | 2 | §17 Բ p. 62 |
| Drop the ը in ցն/ցր after ր (կորցրի) | 1 | §14 Դ p. 47 |
| Drop the ը in ցն/ցր after other consonants (հանգցնել) | 2 | §14 Դ p. 47 |
| Drop the ը before վ when the two preceding consonants can't close a syllable (զարնվել) | 2 | §14 Գ p. 46 |
| Final ըս/ըդ elided before a vowel, joining easily | 1 | §15 Դ p. 53 |
| Final ըս/ըդ elided before a vowel, otherwise (սիրածս էլ) | 2 | §15 Դ p. 54 |
| Final ըր/ըղ/ըմ elided before a vowel (ծանր է) | 1 | §15 Ե p. 55 |
| Final ըր/ըղ/ըմ elided before a vowel, after 2+ consonants (աստղ ու, քաղցր ու) | 2 | §15 Ե p. 56 |
| Any final ը-syllable elided before a consonant, a pause or the line end ("for the eye only") | 2 | §15 Ա–Բ pp. 48–51 |
| Synizesis of ի + vowel (միայն = մյայն) | 1 | §16 Ա p. 60 |
| Synizesis of other vowel pairs | 2 | §16 Ա **[choice]** |
| Dieresis: classical եա/իւ, or ու before a vowel, read as two syllables (Ովկեանի = Ով-կե-ա-նի) | 1 | §16 Ա p. 60 (միուս) **[choice]** |
| Extra ը in a geminate (փըթըթին, զընընել) | 1 | §14 Բ p. 44 |

A clitic written with an apostrophe (կ'ասե, մ'արունիկ, 'ւ) has no syllable of its own (§18, pp. 64–65).

## 4. Stress

Word stress falls on the last syllable; if that syllable's vowel is ը, it falls on the one
before (§5, p. 20; §22, p. 77). Clitics are unstressed:
- **proclitics** (lean on the next word): մի, կը, չը, ու, և, ի, առ, ըստ.
- **enclitics** (lean on the previous word): the forms of եմ (է, են, էր...), էլ, մը, ալ, and the
  articles.

## 5. Members (rhythmic groups) and where they are cut

A line is divided into members (անդամ) of 2–6 syllables. Each member must end on a stressed
syllable (§31, p. 105). Unstressed final syllables and enclitics "must pass" to the next
member (§30.3, p. 101: «Գերեզմաննե|րըն լուռ էին»). So the cuts are:

| Cut | Cost | Example |
|---|---|---|
| After a stressed word-final syllable | 0 | Ահա սըրտիս \| խոպան… |
| Inside a word, before its unstressed final ը-syllable | 0 | ձեռ\|քըդ, սիր\|տըս, քարավա\|նը |
| After an unstressed ending (enclitic, final ը) | 1 **[choice]** | Ու փչում է \| աշնան, Եվ քարավանը \| |
| After a proclitic, or inside a hyphenated word | never | |

**[choice]** Abeghyan's rule would forbid the third kind of cut. Your own scansions use it
(Ու փչում է | աշնան), and he himself notes that Isahakyan often breaks it (§67, p. 225). So the
program allows it at a small cost; `--strict-members` forbids it.

## 6. Choosing the meter

The poem's meter is the pattern most of its lines support, weighed against the licences each
line needs to reach it. The meters catalogued by Abeghyan (Part 2, §§40–92) get a bonus. A
line takes a licence only when it brings the line into a meter that is more common in the
poem or is catalogued.

Catalogue used (members, Part 2):

| Syllables | Scheme | § |
|---|---|---|
| 8 | 4+4 | 43 |
| 12 | 4+4+4 | 44 |
| 16 | 4+4+4+4 | 45 |
| 7 | 4+3 | 46 |
| 11 | 4+4+3 | 47 |
| 15 | 4+4+4+3 | 48 |
| 14 | 4+3+4+3 | 49 |
| 12 | 3+4+5 | 50 |
| 9 | 4+5 | 51 |
| 13 | 4+4+5 | 52 |
| 6, 9, 12 | 3+3, 3+3+3, 3+3+3+3 | 55–57 |
| 11 | 3+3+2+3, 3+3+3+2 | 58, 62 |
| 8 | 2+3+3 | 60 |
| 10, 15, 20 | 5+5, 5+5+5, 5+5+5+5 | 65–67 |
| 12 | 4+2+4+2 (6+6 with 6 = 4+2) | **[choice]**, from your scansions |

Not yet handled: the «Հայրենի կարգ» (§68), the ashugh meters (§§79–80), purely stress-based
(համաշեշտ, §§70–73) and free verse (§§81–91). Lines in these meters will get a scansion, but
it won't match a catalogue entry.
