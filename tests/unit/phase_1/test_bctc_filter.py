"""Unit tests for E_bctc_filter module."""

from pathlib import Path
import tempfile
import unittest

from E_bctc_filter import (
    get_universe_symbols,
    get_collected_symbols,
    get_remaining_symbols,
    select_diverse_batch,
    create_batch_file,
)


class TestBCTCFilter(unittest.TestCase):
    def test_01_get_universe_symbols(self):
        universe = get_universe_symbols()
        self.assertGreater(len(universe), 1500)
        self.assertIn("VNM", universe)
        self.assertIn("FPT", universe)

    def test_02_get_collected_and_remaining_symbols(self):
        collected = get_collected_symbols()
        self.assertGreaterEqual(len(collected), 50)
        self.assertIn("VNM", collected)

        remaining = get_remaining_symbols()
        self.assertEqual(len(remaining) + len(collected), len(get_universe_symbols()))
        self.assertNotIn("VNM", remaining)

    def test_03_select_diverse_batch_has_no_overlap(self):
        collected = get_collected_symbols()
        batch = select_diverse_batch(count=100)
        self.assertEqual(len(batch), 100)
        self.assertEqual(len(set(batch)), 100)

        # Ensure no overlap with collected symbols
        overlap = set(batch).intersection(collected)
        self.assertEqual(len(overlap), 0)


if __name__ == "__main__":
    unittest.main()
