from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pipeline.rank import (
    accumulate_lemma_frequencies,
    consolidate_to_best_lemmas,
    load_surface_to_lemma,
    write_lemma_rank_csv,
)


class RankPipelineTests(unittest.TestCase):
    def test_header_row_is_not_treated_as_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            lemma_csv = tmp_path / "lemmas.csv"
            lemma_csv.write_text(
                "surface_form,pos,lemma\n"
                "foo,NOUN,foo_lemma\n",
                encoding="utf-8",
            )
            freq_list = tmp_path / "freq.txt"
            freq_list.write_text("foo 10\nlemma 100\n", encoding="utf-8")

            surface_map, lemmas = load_surface_to_lemma(lemma_csv)
            self.assertIn("foo_lemma", lemmas)
            self.assertNotIn("lemma", lemmas)

            lemma_freq, matched, unmatched, surface_freq_map = accumulate_lemma_frequencies(
                surface_map, freq_list, lemmas
            )
            consolidated = consolidate_to_best_lemmas(lemma_freq, surface_map, surface_freq_map)
            self.assertEqual(matched, 1)
            self.assertEqual(unmatched, 1)
            self.assertEqual(consolidated["foo_lemma"], 10)

    def test_consolidation_prefers_highest_global_lemma(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            lemma_csv = tmp_path / "lemmas.csv"
            lemma_csv.write_text(
                "surface_form,pos,lemma\n"
                "foo,NOUN,alpha\n"
                "foo,NOUN,beta\n"
                "bar,NOUN,beta\n",
                encoding="utf-8",
            )
            freq_list = tmp_path / "freq.txt"
            freq_list.write_text("foo 10\nbar 20\n", encoding="utf-8")

            surface_map, lemmas = load_surface_to_lemma(lemma_csv)
            lemma_freq, _, _, surface_freq_map = accumulate_lemma_frequencies(surface_map, freq_list, lemmas)
            consolidated = consolidate_to_best_lemmas(lemma_freq, surface_map, surface_freq_map)

            self.assertEqual(consolidated["beta"], 30)
            self.assertEqual(consolidated["alpha"], 0)

    def test_write_rank_csv_sorted(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "rank.csv"
            rows = write_lemma_rank_csv({"zeta": 1, "alpha": 3, "beta": 3}, output, include_freq=True)
            self.assertEqual(rows, 3)
            content = output.read_text(encoding="utf-8").splitlines()
            self.assertEqual(content[0], "lemma,freq,rank")
            self.assertEqual(content[1], "alpha,3,1")
            self.assertEqual(content[2], "beta,3,2")
            self.assertEqual(content[3], "zeta,1,3")


if __name__ == "__main__":
    unittest.main()
