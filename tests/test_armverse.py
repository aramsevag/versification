import unittest
from pathlib import Path

from armverse import analyze_word, scan_poem

EX = Path(__file__).resolve().parent.parent / "examples"


class TestSyllables(unittest.TestCase):
    CASES = {
        "սրտիս": ("սըրտիս", 2), "դրոշ": ("դըրոշ", 2),
        "մկրտել": ("մըկըրտել", 3), "գրգռել": ("գըրգըռել", 3),
        "դարձնել": ("դարձընել", 3), "բարձր": ("բարձըր", 2),
        "անձրև": ("անձըրև", 3), "Աստված": ("Աստված", 2),
        "մարդկային": ("մարդկային", 3), "լվացի": ("լըվացի", 3),
        "Հայրենիք": ("Հայրենիք", 3), "գյուղ": ("գյուղ", 1),
        "ծղրիդ": ("ծըղրիդ", 2), "Երևան": ("Երևան", 3),
        "երգս": ("երգս", 1), "եղբայր": ("եղբայր", 2),
        "Աստուած": ("Աստուած", 2), "արիւն": ("արիւն", 2),
        "սըրտիս": ("սըրտիս", 2),
    }

    def test_words(self):
        for w, (shown, n) in self.CASES.items():
            a = analyze_word(w)
            self.assertEqual((a.render(0), a.variants[0].syllables), (shown, n), w)

    def test_prothesis_is_ambiguous(self):
        a = analyze_word("ստանալ")
        self.assertEqual([v.syllables for v in a.variants], [3, 2])
        self.assertEqual(a.render(0), "ըստանալ")

    def test_linking_n(self):
        self.assertEqual(analyze_word("դաշտն", next_vowel=True).variants[0].syllables, 1)
        self.assertEqual(analyze_word("դաշտն").variants[0].syllables, 2)

    def test_classical_ea(self):
        self.assertEqual(analyze_word("մատեան", classical=True).variants[0].syllables, 2)
        self.assertEqual(analyze_word("մատեան").variants[0].syllables, 3)


class TestScansion(unittest.TestCase):
    def test_user_example(self):
        l = scan_poem("Ահա սրտիս խոպան դաշտն ուր մի անգամ").lines[0]
        self.assertEqual(l.pattern, (4, 4, 3))
        self.assertEqual(l.marked, "Ահա սըրտիս | խոպան դաշտն ուր | մի անգամ")

    def test_anthem(self):
        r = scan_poem((EX / "mer_hayrenik.txt").read_text(encoding="utf-8"))
        self.assertEqual([l.pattern for l in r.lines], [(4, 4), (4, 3)] * 4)
        self.assertEqual(r.regularity, 1.0)
        self.assertEqual(r.stanza_schemes(), [list("ABAB"), list("ABAB")])
        self.assertIn("քեզ մի դըրոշ", r.lines[4].marked)

    def test_enclitic_not_cut(self):
        l = scan_poem("Որ ապրել է դարեդար").lines[0]
        self.assertEqual(l.marked, "Որ ապրել է | դարեդար")


if __name__ == "__main__":
    unittest.main()
