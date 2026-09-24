"""Tests for action items to iCalendar exporter.

Pins RFC 5545 compliance, text escaping, timestamp parsing,
line folding, and overwrite protection.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "examples"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from action_items_to_ics import convert, fold, ics_datetime, ics_text


class TestActionItemsToIcs(unittest.TestCase):
    def test_ics_text_escaping(self):
        self.assertEqual(ics_text("hello;world,here\\there\r\nnext"), "hello\\;world\\,here\\\\there\\nnext")
        self.assertEqual(ics_text(None), "")
        self.assertEqual(ics_text(123), "123")

    def test_fold_line(self):
        short = "SUMMARY:Short line"
        self.assertEqual(fold(short), [short])

        long_line = "DESCRIPTION:" + "A" * 100
        folded = fold(long_line)
        self.assertTrue(len(folded) > 1)
        self.assertTrue(all(len(part.encode("utf-8")) <= 75 for part in folded))

    def test_convert_and_overwrite_refusal(self):
        sample = [
            {
                "id": "t1",
                "description": "Team Sync",
                "due_at": "2026-09-25T15:00:00Z",
                "completed": False,
                "conversation_id": "c1",
            },
            {
                "id": "t2",
                "description": "No due date item",
                "due_at": None,
                "completed": True,
            },
        ]
        with tempfile.TemporaryDirectory() as td:
            in_file = Path(td) / "tasks.json"
            out_file = Path(td) / "tasks.ics"
            in_file.write_text(json.dumps(sample), encoding="utf-8")

            written, skipped = convert(str(in_file), str(out_file))
            self.assertEqual(written, 1)
            self.assertEqual(skipped, 1)

            content = out_file.read_text(encoding="utf-8")
            self.assertIn("BEGIN:VCALENDAR", content)
            self.assertIn("SUMMARY:Team Sync", content)
            self.assertIn("UID:omi-action-t1@omi-cli", content)
            self.assertIn("STATUS:CONFIRMED", content)
            self.assertIn("END:VCALENDAR", content)

            # Refuse overwrite
            with self.assertRaises(FileExistsError):
                convert(str(in_file), str(out_file))


if __name__ == "__main__":
    unittest.main()
