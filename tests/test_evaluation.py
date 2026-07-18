# evaluation scoring tests
import tempfile
import unittest
from pathlib import Path

from pii_redactor.evaluation_matcher import ExactEntityMatcher
from pii_redactor.evaluation_models import GoldCase, GoldEntity
from pii_redactor.gold_loader import GoldLabelLoader
from pii_redactor.metric_calculator import MetricCalculator
from pii_redactor.models import EntitySpan


class GoldLabelLoaderTests(unittest.TestCase):
    # check that the loader can parse gold labels and figure out the char offsets
    def test_loads_gold_label_and_resolves_span(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "gold.json"
            path.write_text(
                '{"cases":[{"name":"c1","text":"Email: user@example.com","labels":[{"type":"email","text":"user@example.com"}]}]}',
                encoding="utf-8",
            )

            cases = GoldLabelLoader().load(path)

        self.assertEqual(cases[0].labels[0].start, 7)
        self.assertEqual(cases[0].labels[0].end, 23)


class ExactEntityMatcherTests(unittest.TestCase):
    # perfect match should be a TP, pretty straightforward
    def test_exact_type_and_text_match_is_true_positive(self):
        case = GoldCase("c1", "Contact Person: Mira Kapoor", [GoldEntity("person", "Mira Kapoor", 16, 27)])
        prediction = EntitySpan("person", "Mira Kapoor", 16, 27, 0.9, "test")

        result = ExactEntityMatcher().evaluate_case(case, [prediction])

        self.assertEqual(len(result.true_positives), 1)
        self.assertEqual(result.false_positives, [])
        self.assertEqual(result.false_negatives, [])

    # if we only detect part of the name it's technically both an FP and FN
    def test_boundary_error_counts_as_fp_and_fn(self):
        case = GoldCase("c1", "Contact Person: Mira Kapoor", [GoldEntity("person", "Mira Kapoor", 16, 27)])
        prediction = EntitySpan("person", "Mira", 16, 20, 0.9, "test")

        result = ExactEntityMatcher().evaluate_case(case, [prediction])

        self.assertEqual(len(result.true_positives), 0)
        self.assertEqual(len(result.false_positives), 1)
        self.assertEqual(len(result.false_negatives), 1)
        self.assertEqual(len(result.boundary_errors), 1)

    # wrong entity type = still counts as error even if text matches
    def test_type_mismatch_counts_as_fp_and_fn(self):
        case = GoldCase("c1", "Greenfield Capital Private Limited", [GoldEntity("company", "Greenfield Capital Private Limited", 0, 34)])
        prediction = EntitySpan("person", "Greenfield Capital Private Limited", 0, 34, 0.9, "test")

        result = ExactEntityMatcher().evaluate_case(case, [prediction])

        self.assertEqual(len(result.false_positives), 1)
        self.assertEqual(len(result.false_negatives), 1)
        self.assertEqual(len(result.type_mismatches), 1)


class MetricCalculatorTests(unittest.TestCase):
    # make sure boundary errors show up in the metrics properly
    def test_boundary_errors_are_reported_with_strict_metrics(self):
        case = GoldCase("c1", "Contact Person: Mira Kapoor", [GoldEntity("person", "Mira Kapoor", 16, 27)])
        prediction = EntitySpan("person", "Mira", 16, 20, 0.9, "test")
        result = ExactEntityMatcher().evaluate_case(case, [prediction])

        metrics = {metric.entity_type: metric for metric in MetricCalculator().calculate([result])}

        self.assertEqual(metrics["person"].tp, 0)
        self.assertEqual(metrics["person"].fp, 1)
        self.assertEqual(metrics["person"].fn, 1)
        self.assertEqual(metrics["person"].boundary_errors, 1)


# just making sure we don't accidentally pull in Pillow or something heavy
class DependencyHygieneTests(unittest.TestCase):
    def test_assignment_path_does_not_require_pillow(self):
        root = Path(__file__).resolve().parents[1]
        self.assertNotIn("Pillow", (root / "requirements.txt").read_text(encoding="utf-8"))
        self.assertNotIn("import PIL", (root / "run_redaction.sh").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
