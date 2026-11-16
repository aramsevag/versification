import unittest
from pathlib import Path

from armverse import analyze_word, scan_poem
from tests import gold_report

EX = Path(__file__).resolve().parent.parent / "examples"


def nat(word, **ctx):
    """Natural (cost-0, first) reading: (rendered, syllables)."""
    a = analyze_word(word, **ctx)
    return a.render(0), a.variants[0].syllables


class TestAbeghyanSyllables(unittest.TestCase):
    """Examples given by Abeghyan himself (page refs in RULES.md)."""

    def test_initial_clusters(self):  # §14 Ա-Բ
        for w, shown, n in [("ճրագ", "ճըրագ", 2), ("դրոշ", "դըրոշ", 2),
                            ("գլորել", "գըլորել", 3), ("տրտում", "տըրտում", 2),
                            ("մկրտիչ", "մըկըրտիչ", 3),
                            ("քրթմնջյուն", "քըրթմընջյուն", 3), ("գյուղ", "գյուղ", 1)]:
            self.assertEqual(nat(w), (shown, n), w)

    def test_medial_clusters(self):  # §9 pp. 31-32
        for w, n in [("զարթնել", 2), ("անձնական", 3), ("ամպրոպ", 2),
                     ("ընկնել", 2), ("Հայրենիք", 3)]:
            self.assertEqual(nat(w)[1], n, w)

    def test_final_clusters(self):  # §5 p. 20, §9 p. 32, §15
        for w, n in [("աստղ", 2), ("դառն", 2), ("մեղր", 2), ("թանձր", 2),
                     ("սիրտս", 2), ("պարտք", 1), ("կուրծք", 1), ("մեղմ", 1)]:
            self.assertEqual(nat(w)[1], n, w)

    def test_prothesis_depends_on_previous_word(self):  # §9 p. 31, §17
        self.assertEqual(nat("սկսել"), ("ըսկըսել", 3))
        self.assertEqual(nat("սկսել", prev_end="V"), ("սկըսել", 2))
        self.assertEqual(nat("ստրուկ", prev_end="V"), ("ստըրուկ", 2))

    def test_licences_have_costs(self):
        a = analyze_word("նման")
        self.assertEqual([(v.syllables, v.cost) for v in a.variants], [(2, 0), (1, 2)])
        a = analyze_word("Ովկեանի", classical=True)
        self.assertIn((4, 1), [(v.syllables, v.cost) for v in a.variants])

    def test_article_before_h(self):  # RULES.md §2
        a = analyze_word("ափերն", next_h=True, pause_after=False)
        self.assertIn((2, 0), [(v.syllables, v.cost) for v in a.variants])
        a = analyze_word("ափերն,", next_h=True, pause_after=True)
        self.assertNotIn((2, 0), [(v.syllables, v.cost) for v in a.variants])

    def test_lexicon(self):  # armverse/data/lexicon.txt
        self.assertEqual(nat("Ուխտագնաց,"), ("Ուխտագընաց,", 4))

    def test_linking_n(self):  # §15 Գ
        a = analyze_word("դաշտն", next_vowel=True, pause_after=False)
        self.assertIn((1, 0), [(v.syllables, v.cost) for v in a.variants])
        a = analyze_word("դաշտն")
        self.assertEqual(min(v.cost for v in a.variants if v.syllables == 1), 2)


class TestScansion(unittest.TestCase):
    def test_user_example(self):
        l = scan_poem("Ահա սրտիս խոպան դաշտն ուր մի անգամ").lines[0]
        self.assertEqual(l.marked, "Ահա սըրտիս | խոպան դաշտն ուր | մի անգամ")

    def test_mid_word_cut(self):  # §30.3
        l = scan_poem("Զոյգ երթալ, ձեռքըդ քոյր ձեռքի մէջ դըրած").lines[0]
        self.assertEqual(l.marked, "Զոյգ երթալ, ձեռ|քըդ քոյր ձեռքի | մէջ դըրած")

    def test_licences_from_poem_context(self):
        r = scan_poem("Զոյգ երթալ, ձեռքըդ քոյր ձեռքի մէջ դըրած\n"
                      "Լանջն է յուզեալ Ովկեանի մը նըման\n"
                      "Աստղերու նման գիշեր սիրէ՝ փողփողի՜լ\n"
                      "Ահա սրտիս խոպան դաշտն ուր մի անգամ")
        # with only the first three lines, the heavy licence on նման is not
        # yet justified and line 3 stays 3/4/5 (also a catalogued meter)
        self.assertEqual([l.pattern for l in r.lines], [(4, 4, 3)] * 4)
        self.assertIn("dieresis", r.lines[1].licences[0])

    def test_gold_set_baseline(self):
        ok, total = gold_report.run(verbose=False)
        self.assertGreaterEqual(ok, 32, "regression on tests/data/gold.txt")


if __name__ == "__main__":
    unittest.main()
