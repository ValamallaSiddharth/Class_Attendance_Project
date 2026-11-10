"""
Comprehensive verification script for Class Attendance Project.
Validates all project components:
1. Syntax of all Python files
2. Key imports and dependencies
3. ONNX models and labels existence
4. Timetable CSV formatting
5. HTML template rendering (Jinja2)
6. Backend Flask endpoints
7. Frontend React build
"""
import os
import sys
import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def run_checks():
    print("=" * 60)
    print("RUNNING COMPREHENSIVE PROJECT VERIFICATION")
    print("=" * 60)
    passed = 0
    failed = 0

    # 1. Check Python syntax
    print("\n[1/7] Checking Python syntax...")
    py_files = [
        ROOT / "app.py",
        ROOT / "api_server.py",
        ROOT / "scripts" / "crop_dataset_faces.py",
        ROOT / "scripts" / "create_sface_embeddings.py",
        ROOT / "scripts" / "timetable_attendance.py",
        ROOT / "scripts" / "augment_dataset.py",
        ROOT / "scripts" / "mark_attendance.py",
        ROOT / "scripts" / "run_smoke_test.py",
    ]
    for pf in py_files:
        try:
            py_compile.compile(str(pf), doraise=True)
            print(f"  ✓ Syntax valid: {pf.name}")
            passed += 1
        except Exception as e:
            print(f"  ✗ Syntax error in {pf.name}: {e}")
            failed += 1

    # 2. Check Models
    print("\n[2/7] Checking model files...")
    models = [
        ROOT / "models" / "face_detection_yunet_2023mar.onnx",
        ROOT / "models" / "face_recognition_sface_2021dec.onnx",
        ROOT / "models" / "labels.txt",
    ]
    for m in models:
        if m.exists() and m.stat().st_size > 0:
            print(f"  ✓ Model file exists ({m.stat().st_size / 1024:.1f} KB): {m.name}")
            passed += 1
        else:
            print(f"  ✗ Missing or empty model file: {m.name}")
            failed += 1

    # 3. Check Timetable CSV
    print("\n[3/7] Checking timetable CSV...")
    timetable_csv = ROOT / "timetable" / "class_timetable.csv"
    if timetable_csv.exists():
        with open(timetable_csv, "r", encoding="utf-8") as f:
            header = f.readline().strip()
            rows = len(f.readlines())
        expected_cols = ["day", "period", "subject", "start_time", "end_time", "room"]
        if all(col in header for col in expected_cols):
            print(f"  ✓ Timetable valid ({rows} rows, headers: {header[:40]}...)")
            passed += 1
        else:
            print(f"  ✗ Timetable missing expected columns: {header}")
            failed += 1
    else:
        print("  ✗ Timetable CSV not found")
        failed += 1

    # 4. Check HTML Templates
    print("\n[4/7] Checking Jinja2 templates...")
    try:
        import jinja2
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(ROOT / "templates")))
        for t in ["attendance_template.html", "student_detail_template.html", "teacher_dashboard_template.html"]:
            template_path = ROOT / "templates" / t
            if template_path.exists():
                env.get_template(t)
                print(f"  ✓ Template compiles: {t}")
                passed += 1
            else:
                print(f"  ✗ Template missing: {t}")
                failed += 1
    except Exception as e:
        print(f"  ✗ Jinja2 template check failed: {e}")
        failed += 1

    # 5. Check Flask API endpoints
    print("\n[5/7] Testing Flask App endpoints...")
    try:
        from app import app
        with app.test_client() as client:
            endpoints = [
                ("/api/health", 200),
                ("/api/dashboard", 200),
                ("/api/attendance/latest", 200),
                ("/api/current-context", 200),
                ("/api/videos", 200),
                ("/api/jobs", 200),
                ("/api/reports", 200),
                ("/", 200),
            ]
            for ep, expected_status in endpoints:
                res = client.get(ep)
                if res.status_code == expected_status:
                    print(f"  ✓ Endpoint {ep} -> {res.status_code}")
                    passed += 1
                else:
                    print(f"  ✗ Endpoint {ep} returned {res.status_code} (expected {expected_status})")
                    failed += 1
    except Exception as e:
        print(f"  ✗ Flask app verification failed: {e}")
        failed += 1

    # 6. Check React Build
    print("\n[6/7] Checking React frontend dist...")
    dist_index = ROOT / "my-react-website" / "dist" / "index.html"
    if dist_index.exists():
        print(f"  ✓ React dist index.html exists ({dist_index.stat().st_size} bytes)")
        passed += 1
    else:
        print("  ✗ React dist not found; run 'npm run build'")
        failed += 1

    # 7. Check requirements.txt and .gitignore
    print("\n[7/7] Checking project configuration files...")
    req_file = ROOT / "requirements.txt"
    git_file = ROOT / ".gitignore"
    if req_file.exists() and req_file.stat().st_size > 0:
        print("  ✓ requirements.txt exists")
        passed += 1
    else:
        print("  ✗ requirements.txt missing")
        failed += 1

    if git_file.exists() and git_file.stat().st_size > 0:
        print("  ✓ .gitignore exists")
        passed += 1
    else:
        print("  ✗ .gitignore missing")
        failed += 1

    print("\n" + "=" * 60)
    print(f"SUMMARY: {passed} checks passed, {failed} checks failed.")
    print("=" * 60)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_checks())
