"""Diagnostic fixtures only. These are not robot experiments."""
import csv
import tempfile
import unittest
from pathlib import Path
from audit import admit, audit_csv, paired_metrics


class AuditTest(unittest.TestCase):
    def test_compensating_gain_does_not_erase_loss(self):
        result = admit([1, 1, 0, 0], [1, 0, 1, 0], [0, 0], [1, 0])
        self.assertTrue(result["aggregate"])
        self.assertFalse(result["preservation"])
        self.assertEqual(result["old"]["net_change"], 0)
        self.assertEqual(result["old"]["conditional_loss"], 0.5)
        self.assertEqual(result["logical_rollouts"], 12)

    def test_useful_preserving_repair_is_admitted(self):
        result = admit([1, 0, 1], [1, 1, 1], [0, 0], [1, 0])
        self.assertTrue(result["aggregate"])
        self.assertTrue(result["preservation"])

    def test_no_old_success_is_not_perfect_retention(self):
        result = admit([0, 0], [1, 1], [0], [1])
        self.assertIsNone(result["old"]["conditional_loss"])
        self.assertFalse(result["evaluable"])
        self.assertFalse(result["preservation"])

    def test_identity_exhaustive_two_scene_outcomes(self):
        import itertools
        for values in itertools.product((0, 1), repeat=4):
            m = paired_metrics(list(values[:2]), list(values[2:]))
            self.assertAlmostEqual(m["net_change"],
                                   m["candidate_success_rate"] - m["parent_success_rate"])

    def test_validation_is_excluded_and_duplicates_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "fixture.csv"
            fields = ["context_id", "candidate_id", "split", "regime", "scene_id", "parent", "candidate"]
            rows = [["c", "p", "validation", "old", "v", 1, 0],
                    ["c", "p", "audit", "old", "a", 1, 1]]
            with p.open("w", newline="") as f:
                w = csv.writer(f); w.writerow(fields); w.writerows(rows)
            self.assertEqual(audit_csv(p)[0]["lost"], 0)
            with p.open("a", newline="") as f:
                csv.writer(f).writerow(rows[1])
            with self.assertRaises(ValueError):
                audit_csv(p)

    def test_bad_inputs_are_not_silently_scored(self):
        for a, b in [([], []), ([1], [1, 0]), ([1], [2])]:
            with self.assertRaises(ValueError):
                paired_metrics(a, b)


if __name__ == "__main__":
    unittest.main()
