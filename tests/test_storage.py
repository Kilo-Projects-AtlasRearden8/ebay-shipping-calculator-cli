"""Tests for local JSON storage and CSV export."""

import json
import os
import tempfile
import unittest

from ebay_shipping_calculator.storage import DEFAULT_STORAGE_PATH, Storage


class StorageTests(unittest.TestCase):
    def test_default_path(self):
        self.assertEqual(DEFAULT_STORAGE_PATH, "shipments.json")

    def test_add_and_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "shipments.json")
            storage = Storage(path)
            entry = storage.add(
                {
                    "item": "Test Book",
                    "tier": "ground_advantage",
                    "estimated_cost_usd": 7.85,
                }
            )
            self.assertEqual(len(storage.list()), 1)
            self.assertEqual(entry["item"], "Test Book")
            self.assertIn("id", entry)
            self.assertIn("timestamp", entry)
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            self.assertEqual(len(data), 1)

    def test_missing_file_starts_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "nonexistent.json")
            storage = Storage(path)
            self.assertEqual(storage.list(), [])

    def test_export_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "shipments.json")
            out = os.path.join(tmp, "quotes.csv")
            storage = Storage(path)
            storage.add({"item": "Book", "estimated_cost_usd": 7.85})
            storage.add({"item": "Game", "estimated_cost_usd": 12.05})
            count = storage.export_csv(out)
            self.assertEqual(count, 2)
            with open(out, encoding="utf-8") as fh:
                lines = fh.read().strip().splitlines()
            self.assertEqual(len(lines), 3)  # header + 2 rows
            self.assertTrue(lines[0].startswith("id,timestamp"))


if __name__ == "__main__":
    unittest.main()
