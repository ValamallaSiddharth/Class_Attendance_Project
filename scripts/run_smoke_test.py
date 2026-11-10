"""
Fast smoke test for app.py:
Tests health, context, dashboard, reports, videos, jobs, and React static index delivery.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import app, EXPORTS_DIR


def main():
    print("Starting smoke test on app.py...")
    failures = 0

    with app.test_client() as client:
        # 1. Health check
        res = client.get("/api/health")
        data = res.get_json() or {}
        if res.status_code == 200 and data.get("success"):
            print("  [PASS] /api/health OK")
        else:
            print(f"  [FAIL] /api/health returned {res.status_code}")
            failures += 1

        # 2. Current context
        res = client.get("/api/current-context")
        data = res.get_json() or {}
        if res.status_code == 200 and "current_day" in data:
            print(f"  [PASS] /api/current-context OK (day={data.get('current_day')}, period={data.get('current_period')})")
        else:
            print(f"  [FAIL] /api/current-context returned {res.status_code}")
            failures += 1

        # 3. Dashboard
        res = client.get("/api/dashboard")
        data = res.get_json() or {}
        if res.status_code == 200 and "total_students" in data:
            print(f"  [PASS] /api/dashboard OK (total_students={data.get('total_students')}, present={data.get('present')})")
        else:
            print(f"  [FAIL] /api/dashboard returned {res.status_code}")
            failures += 1

        # 4. Reports
        res = client.get("/api/reports")
        data = res.get_json()
        if res.status_code == 200 and isinstance(data, list):
            print(f"  [PASS] /api/reports OK ({len(data)} report files listed)")
        else:
            print(f"  [FAIL] /api/reports returned {res.status_code}")
            failures += 1

        # 5. Videos
        res = client.get("/api/videos")
        data = res.get_json()
        if res.status_code == 200 and isinstance(data, list):
            print(f"  [PASS] /api/videos OK ({len(data)} video files found)")
        else:
            print(f"  [FAIL] /api/videos returned {res.status_code}")
            failures += 1

        # 6. Jobs
        res = client.get("/api/jobs")
        data = res.get_json()
        if res.status_code == 200 and isinstance(data, list):
            print(f"  [PASS] /api/jobs OK")
        else:
            print(f"  [FAIL] /api/jobs returned {res.status_code}")
            failures += 1

        # 7. React root
        res = client.get("/")
        if res.status_code == 200 and b"<!doctype html>" in res.data.lower() or b"<html" in res.data.lower():
            print(f"  [PASS] / (React index.html delivery) OK")
        else:
            print(f"  [FAIL] / returned status {res.status_code}")
            failures += 1

    if failures == 0:
        print("\nALL SMOKE TESTS PASSED!")
        return 0
    else:
        print(f"\nSMOKE TESTS FAILED WITH {failures} ERRORS")
        return 1


if __name__ == "__main__":
    sys.exit(main())
