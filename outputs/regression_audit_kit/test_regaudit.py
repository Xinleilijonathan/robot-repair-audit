"""Unit tests for regaudit (synthetic fixtures only). Run: python -m unittest -v test_regaudit.py"""
import math
import unittest

import regaudit as ra


class RegauditTests(unittest.TestCase):
    def test_directional_identity(self):
        parent = {'a': 1, 'b': 1, 'c': 0, 'd': 0, 'e': 1}
        cand = {'a': 0, 'b': 1, 'c': 1, 'd': 1, 'e': 1}
        d = ra.directional(parent, cand, parent)
        self.assertEqual(d['lost'], ['a'])
        self.assertEqual(d['gained'], ['c', 'd'])
        self.assertEqual(d['net'], sum(cand.values()) - sum(parent.values()))

    def test_wilson_bounds(self):
        p, lo, hi = ra.wilson(0, 10)
        self.assertEqual(p, 0.0)
        self.assertEqual(lo, 0.0)
        self.assertGreater(hi, 0.2)
        self.assertIsNone(ra.wilson(0, 0))

    def test_expected_uniform_detection(self):
        self.assertEqual(ra.expected_uniform_detection(10, 0, 3), 0.0)
        self.assertEqual(ra.expected_uniform_detection(10, 2, 10), 1.0)
        self.assertAlmostEqual(ra.expected_uniform_detection(10, 1, 3), 0.3)
        self.assertAlmostEqual(ra.expected_uniform_detection(73, 4, 8), 1 - math.comb(69, 8) / math.comb(73, 8))

    def test_history_suite_ranks_by_counts(self):
        counts = ra.loss_history([{'x', 'y'}, {'x'}, {'x', 'z'}])
        self.assertEqual(ra.history_suite(counts, ['x', 'y', 'z', 'w'], 1, seed=0), ['x'])
        self.assertEqual(set(ra.history_suite(counts, ['x', 'y', 'z', 'w'], 3, seed=0)), {'x', 'y', 'z'})

    def test_zero_loss_gate(self):
        parent = {'t1': 0, 't2': 0, 'o1': 1, 'o2': 1}
        good = {'t1': 1, 't2': 0, 'o1': 1, 'o2': 1}
        bad = {'t1': 1, 't2': 1, 'o1': 0, 'o2': 1}
        self.assertTrue(ra.zero_loss_gate(parent, good, ['t1', 't2'], ['o1', 'o2'])['admit'])
        self.assertFalse(ra.zero_loss_gate(parent, bad, ['t1', 't2'], ['o1', 'o2'])['admit'])

    def test_null_population_respects_bounds(self):
        bounds = {'a': (0.0, 1.0), 'b': (5.0, 6.0), 'c': (-1.0, 0.0)}
        for edit in ra.null_population(bounds, 200, seed=1):
            self.assertIn(len(edit), (1, 2))
            for k, v in edit.items():
                self.assertTrue(bounds[k][0] <= v <= bounds[k][1])

    def test_replay_check_and_duplicates(self):
        self.assertTrue(ra.replay_check({'a': 1}, {'a': 1})['exact'])
        with self.assertRaises(ValueError):
            ra.outcomes([{'config': 'p', 'scene': 'a', 'success': 1}] * 2, 'p')


if __name__ == '__main__':
    unittest.main()
