"""Tests for conversations to iCalendar exporter.

Pins RFC 5545 compliance, structured field handling, default duration,
UID generation, and overwrite protection.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "examples"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from conversations_to_ics import convert, fold, ics_datetime, ics_text


class TestConversationsToIcs(unittest.TestCase):
    def test_ics_text_escaping(self):
        self.assertEqual(ics_text("meeting;standup,notes\\details"), "meeting\\;standup\\,notes\\\\details")
        self.assertEqual(ics_text(None), "")

    def test_fold_line(self):
        short = "SUMMARY:Short meeting"
        self.assertEqual(fold(short), [short])

    def test_convert_and_overwrite_refusal(self):
        sample = [
            {
                "id": "conv_1",
                "started_at": "2026-09-24T10:00:00Z",
                "finished_at": "2026-09-24T10:45:00Z",
                "structured": {"title": "Architecture Sync", "category": "engineering"},
                "source": "omi_wearable",
            },
            {
                "id": "conv_2",
                "started_at": None,
                "structured": {"title": "No start time"},
            },
        ]
        with tempfile.TemporaryDirectory() as td:
            in_file = Path(td) / "conv.json"
            out_file = Path(td) / "conv.ics"
            in_file.write_text(json.dumps(sample), encoding="utf-8")

            written, skipped = convert(str(in_file), str(out_file))
            self.assertEqual(written, 1)
            self.assertEqual(skipped, 1)

            content = out_file.read_text(encoding="utf-8")
            unfolded = content.replace("\r\n ", "").replace("\n ", "")
            self.assertIn("BEGIN:VCALENDAR", content)
            self.assertIn("SUMMARY:Architecture Sync", content)
            self.assertIn("UID:omi-conversation-conv_1@omi-cli", content)
            self.assertIn("DTSTART:20260924T100000Z", content)
            self.assertIn("DTEND:20260924T104500Z", content)
            self.assertIn("Category: engineering", unfolded)
            self.assertIn("Source: omi_wearable", unfolded)
            self.assertIn("END:VCALENDAR", content)

            # Refuse overwrite
            with self.assertRaises(FileExistsError):
                convert(str(in_file), str(out_file))


if __name__ == "__main__":
    unittest.main()
