#!/usr/bin/env python3
"""
Full end-to-end validation of attendance system.
Starts a fresh job, polls for completion, validates JSON, and tests export/edit APIs.
"""

import time
import requests
import json
import os
from pathlib import Path

BASE = 'http://127.0.0.1:5000'
TIMEOUT_SECONDS = 600  # 10 minutes
POLL_INTERVAL = 4

def reset_runs():
    """Clear attendance_runs.json to start fresh."""
    runs_path = Path(__file__).parent.parent / 'data' / 'attendance_runs.json'
    with open(runs_path, 'w') as f:
        json.dump({}, f, indent=2)
    print("[SETUP] Cleared attendance_runs.json")

def start_job(day='Tuesday', period='P1'):
    """Start a new attendance processing job."""
    try:
        r = requests.post(
            f"{BASE}/api/process",
            json={"day": day, "period": period},
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            job_id = data.get('job_id')
            print(f"[JOB START] Job {job_id} started for {day} {period}")
            return job_id
        else:
            print(f"[ERROR] Failed to start job: {r.status_code}")
            print(r.text[:200])
            return None
    except Exception as e:
        print(f"[ERROR] Exception starting job: {e}")
        return None


def poll_job_with_timeout(job_id, timeout=TIMEOUT_SECONDS):
    """Poll job until completion or timeout."""
    start = time.time()
    last_status = None
    poll_count = 0
    
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{BASE}/api/status/{job_id}", timeout=5)
            if r.status_code == 200:
                job = r.json()
                status = job.get('status')
                elapsed = time.time() - start
                poll_count += 1
                
                if status != last_status:
                    print(f"  [{elapsed:.0f}s] Status: {status}")
                    last_status = status
                
                if status in ('Completed', 'Failed'):
                    print(f"\n✓ Job finished after {elapsed:.1f}s ({poll_count} polls)")
                    return job
            else:
                print(f"  Poll error: HTTP {r.status_code}")
        except Exception as e:
            print(f"  Poll exception: {e}")
        
        time.sleep(POLL_INTERVAL)
    
    raise TimeoutError(f'Job timeout after {timeout}s ({poll_count} polls)')


def validate_runs_json(day, period):
    """Check attendance_runs.json for the run entry."""
    runs_path = Path(__file__).parent.parent / 'data' / 'attendance_runs.json'
    if not runs_path.exists():
        return None
    
    with open(runs_path) as f:
        runs = json.load(f)
    
    key = f"{day}_{period}"
    return runs.get(key)


def check_html_generation():
    """Verify no HTML files were auto-generated."""
    att_website = Path(__file__).parent.parent / 'attendance_website'
    html_files = list(att_website.glob('*.html'))
    return len(html_files) == 0


def test_manual_edit(day='Tuesday', period='P1'):
    """Test manual edit endpoint."""
    print(f"\n[MANUAL EDIT TEST] Editing {day} {period}")
    try:
        # Get student list first from runs
        run = validate_runs_json(day, period)
        if not run or 'students' not in run:
            print("  ✗ No student list found in runs.json")
            return False
        
        students = run['students']
        if not students:
            print("  ✗ No students in list")
            return False
        
        # Pick first student and flip their status
        student = students[0]
        roll = student['roll_number']
        # Map status format: "Present" -> "Absent", "Absent" -> "Present"
        current_status = student['status']
        new_status = 'Absent' if current_status == 'Present' else 'Present'
        
        # Build changes array as expected by API
        payload = {
            'changes': [
                {
                    'roll': roll,
                    'status': new_status,
                    'reason': 'TEST: Manual edit validation'
                }
            ]
        }
        
        r = requests.post(
            f"{BASE}/api/attendance/{day}/{period}/edit",
            json=payload,
            timeout=10
        )
        
        print(f"  Edit response: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            if data.get('success'):
                print(f"  ✓ Manual edit applied for {roll}")
                
                # Check overrides file
                overrides_path = Path(__file__).parent.parent / 'data' / 'manual_overrides.json'
                if overrides_path.exists():
                    with open(overrides_path) as f:
                        overrides = json.load(f)
                    key = f"{day}_{period}"
                    if key in overrides and roll in overrides[key]:
                        print(f"  ✓ Overrides file updated")
                        return True
            else:
                print(f"  ✗ Edit failed: {data.get('error')}")
        else:
            print(f"  ✗ HTTP error: {r.text[:300]}")
        return False
    except Exception as e:
        print(f"  ✗ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_export(day='Tuesday', period='P1', fmt='csv'):
    """Test export endpoint."""
    print(f"\n[EXPORT TEST] Testing {fmt.upper()} export")
    try:
        r = requests.get(f"{BASE}/api/export/{day}/{period}?format={fmt}", timeout=10)
        print(f"  HTTP status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            if data.get('success'):
                url = data.get('url') or data.get('file')
                print(f"  ✓ Export successful: {url}")
                return True
            else:
                print(f"  ✗ Export failed: {data.get('error')}")
        else:
            print(f"  ✗ Error: {r.text[:200]}")
        return False
    except Exception as e:
        print(f"  ✗ Exception: {e}")
        return False


def main():
    print("=" * 70)
    print("FULL END-TO-END VALIDATION")
    print("=" * 70)
    
    day = 'Tuesday'
    period = 'P1'
    
    # Reset and start fresh
    reset_runs()
    job_id = start_job(day, period)
    if not job_id:
        print("[FATAL] Could not start job")
        return 1
    
    # Poll for completion
    print(f"\n[POLLING] Waiting for job completion (timeout: {TIMEOUT_SECONDS}s)")
    try:
        job = poll_job_with_timeout(job_id, timeout=TIMEOUT_SECONDS)
    except TimeoutError as e:
        print(f"[FATAL] {e}")
        return 1
    
    # Validation phase
    print("\n" + "=" * 70)
    print("VALIDATION PHASE")
    print("=" * 70)
    
    # 1. Check final job status
    print(f"\n[1] Job completion status: {job.get('status')}")
    if job.get('status') == 'Failed':
        print(f"    Error: {job.get('error')}")
        return 1
    elif job.get('status') != 'Completed':
        print(f"    ✗ Unexpected status: {job.get('status')}")
        return 1
    print(f"    ✓ Job completed successfully")
    
    # 2. Check attendance_runs.json
    print(f"\n[2] Checking data/attendance_runs.json")
    run = validate_runs_json(day, period)
    if not run:
        print(f"    ✗ No run entry found for {day} {period}")
        return 1
    
    print(f"    ✓ Run entry found")
    print(f"      Status: {run.get('status')}")
    print(f"      Total: {run.get('total_students')} students")
    print(f"      Present: {run.get('present_count')}, Absent: {run.get('absent_count')}")
    print(f"      Attendance: {run.get('attendance_percentage')}%")
    
    # Check no HTML auto-generation
    if 'class_report_file' in run or 'teacher_dashboard_file' in run:
        print(f"    ✗ HTML files were auto-generated (should be optional)")
        return 1
    print(f"    ✓ No auto-generated HTML files in run entry")
    
    # 3. Check attendance_website/ directory
    print(f"\n[3] Checking attendance_website/ directory")
    if check_html_generation():
        print(f"    ✓ No new HTML files generated (expected)")
    else:
        print(f"    ✗ HTML files found (should not auto-generate)")
        return 1
    
    # 4. Test manual edit
    print(f"\n[4] Testing manual edit API")
    if test_manual_edit(day, period):
        print(f"    ✓ Manual edit validation passed")
    else:
        print(f"    ✗ Manual edit validation failed")
        return 1
    
    # 5. Test exports
    print(f"\n[5] Testing export functionality")
    results = []
    for fmt in ['csv', 'excel', 'pdf']:
        results.append(test_export(day, period, fmt))
    
    if all(results):
        print(f"    ✓ All exports successful")
    else:
        print(f"    ✗ Some exports failed")
        return 1
    
    # Final summary
    print("\n" + "=" * 70)
    print("✓ ALL VALIDATIONS PASSED")
    print("=" * 70)
    print("\nKey findings:")
    print(f"  • Job completed in reasonable time")
    print(f"  • Results stored in data/attendance_runs.json")
    print(f"  • No auto-generated HTML files")
    print(f"  • Manual edit API working")
    print(f"  • Export functionality working (CSV, Excel, PDF)")
    print(f"\nSmartAttendance refactor is COMPLETE ✓")
    
    return 0


if __name__ == '__main__':
    exit(main())
