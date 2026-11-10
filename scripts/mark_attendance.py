"""
CLI entry point to mark attendance based on the timetable schedule.
Delegates to timetable_attendance.py.
"""
import sys
from pathlib import Path

# Add scripts directory to path if needed
sys.path.insert(0, str(Path(__file__).resolve().parent))

from timetable_attendance import main

if __name__ == "__main__":
    main()
