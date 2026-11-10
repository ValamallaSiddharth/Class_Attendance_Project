import unittest
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import TIMETABLE, PERIOD_TIMINGS


class TestTimetableLogic(unittest.TestCase):
    def test_csv_file_exists(self):
        """Ensure class timetable CSV exists and has data."""
        csv_path = ROOT / "timetable" / "class_timetable.csv"
        self.assertTrue(csv_path.exists())
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        self.assertGreater(len(rows), 0)
        self.assertIn("day", rows[0])
        self.assertIn("period", rows[0])
        self.assertIn("subject", rows[0])

    def test_timetable_days(self):
        """Ensure all working days Monday-Friday are configured."""
        expected_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        for day in expected_days:
            self.assertIn(day, TIMETABLE)
            self.assertGreater(len(TIMETABLE[day]), 0)

    def test_period_timings(self):
        """Ensure period start and end timings are formatted properly."""
        for period, timings in PERIOD_TIMINGS.items():
            self.assertIn("start", timings)
            self.assertIn("end", timings)
            if period != "Lunch":
                self.assertIn("process_time", timings)


if __name__ == "__main__":
    unittest.main()
