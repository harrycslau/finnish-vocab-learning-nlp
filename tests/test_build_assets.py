from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pipeline.build_lemma_assets import main as build_main


class BuildAssetsTests(unittest.TestCase):
    def test_skip_lemma_generates_rank_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            freq = root / "freq.txt"
            freq.write_text("foo 10\nbar 5\n", encoding="utf-8")

            lemma_csv = root / "lemmas.csv"
            lemma_csv.write_text(
                "surface_form,pos,lemma\n"
                "foo,NOUN,foo_lemma\n"
                "bar,NOUN,bar_lemma\n",
                encoding="utf-8",
            )
            rank_csv = root / "rank.csv"
            config = root / "test.yaml"
            config.write_text(
                "language:\n"
                "  short_code: xx\n"
                "  locale: xx_XX\n"
                "  lookup_table: xx_XX_lemma_lookup\n"
                "  rank_table: xx_XX_lemma_rank\n"
                "analyzer:\n"
                "  module: lang.template.analyzer\n"
                "  class: TemplateAnalyzer\n"
                "  settings: {}\n"
                "paths:\n"
                f"  freq_list: {freq}\n"
                f"  output_dir: {root}\n"
                "output_names:\n"
                "  lemma_with_limit: \"{short_code}_{limit}_lemmas.csv\"\n"
                "  lemma_default: \"{short_code}_lemmas.csv\"\n"
                "  rank_with_limit: \"{short_code}_{limit}_lemmas_rank.csv\"\n"
                "  rank_default: \"{short_code}_lemmas_rank.csv\"\n"
                "  sqlite_default: \"dictionary.sqlite\"\n"
                "defaults: {}\n",
                encoding="utf-8",
            )

            build_main(
                [
                    "--config",
                    str(config),
                    "--skip-lemma",
                    "--lemma-output",
                    str(lemma_csv),
                    "--rank-output",
                    str(rank_csv),
                ]
            )

            self.assertTrue(rank_csv.exists())
            lines = rank_csv.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines[0], "lemma,rank")
            self.assertEqual(lines[1], "foo_lemma,1")
            self.assertEqual(lines[2], "bar_lemma,2")


if __name__ == "__main__":
    unittest.main()

