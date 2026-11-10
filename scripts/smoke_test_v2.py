import time
import requests
import json
import os
from pathlib import Path

BASE = 'http://127.0.0.1:5000'
TIMEOUT_SECONDS = 600  # 10 minutes
POLL_INTERVAL = 4

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
                    print(f"[{elapsed:.0f}s] Job status: {status}")
                    last_status = status
                
                if status in ('Completed', 'Failed'):
                    print(f"\n✓ Job finished after {elapsed:.1f}s")
                    return job
            else:
                print(f"Status fetch failed: {r.status_code}")
        except Exception as e:
            print(f"Poll error: {e}")
        
        time.sleep(POLL_INTERVAL)
    
    raise TimeoutError(f'Job did not finish in {timeout}s (polled {poll_count} times)')


def validate_runs_json(day, period):
    """Check attendance_runs.json for the run entry."""
    runs_path = Path(__file__).parent.parent / 'data' / 'attendance_runs.json'
    if not runs_path.exists():
        return None
    
    with open(runs_path) as f:
        runs = json.load(f)
    
    key = f"{day}_{period}"
    for k, v in runs.items():
        if v.get('day') == day and str(v.get('period')).upper() == str(period).upper():
            return v
    return None


def test_manual_edit(day, period):
    """Edit first student and check overrides file."""
    run = validate_runs_json(day, period)
    if not run or not run.get('students'):
        print("No students in run to edit")
        return None
    
    first = run['students'][0]
    roll = first.get('roll_number')
    new_status = 'Present' if first.get('status') != 'Present' else 'Absent'
    
    print(f"\n[EDIT TEST] Flipping {roll} from {first.get('status')} to {new_status}")
    changes = [{'roll': roll, 'status': new_status, 'reason': 'Smoke test manual edit'}]
    
    r = requests.post(f"{BASE}/api/attendance/{day}/{period}/edit", json={'changes': changes})
    print(f"Edit response: {r.status_code}")
    if r.status_code != 200:
        print(f"  Error: {r.text}")
        return None
    
    result = r.json()
    if result.get('success'):
        print(f"  ✓ Manual edit applied")
    
    # Check overrides file
    overrides_path = Path(__file__).parent.parent / 'data' / 'manual_overrides.json'
    if overrides_path.exists():
        with open(overrides_path) as f:
            overrides = json.load(f)
        key = f"{day}_{period}"
        if key in overrides:
            print(f"  ✓ Overrides file updated for key {key}")
            print(f"    Override entry: {overrides[key].get(roll, {})}")
    
    return result


def test_export(day, period, fmt='csv'):
    """Test export endpoint."""
    print(f"\n[EXPORT TEST] Testing {fmt.upper()} export")
    try:
        r = requests.get(f"{BASE}/api/export/{day}/{period}?format={fmt}", timeout=10)
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            if data.get('success'):
                url = data.get('url') or data.get('file')
                print(f"  ✓ Export successful: {url}")
                return True
            else:
                print(f"  ✗ Export failed: {data.get('error')}")
                return False
        else:
            print(f"  ✗ HTTP error: {r.text[:200]}")
            return False
    except Exception as e:
        print(f"  ✗ Export error: {e}")
        return False


def main():
    job_id = '02E25BD0'
    day = 'Tuesday'
    period = 'P1'
    
    print("=" * 70)
    print("SMOKE TEST — POLLING FOR JOB COMPLETION (10 MIN TIMEOUT)")
    print("=" * 70)
    
    try:
        job = poll_job_with_timeout(job_id, timeout=TIMEOUT_SECONDS)
        print(f"\nJob final status: {job.get('status')}")
        if job.get('error'):
            print(f"Job error: {job.get('error')}")
            return 1
    except TimeoutError as e:
        print(f"\n✗ {e}")
        return 1
    
    print("\n" + "=" * 70)
    print("VALIDATION PHASE")
    print("=" * 70)
    
    # Validate runs.json
    print("\n[1] Checking data/attendance_runs.json")
    run = validate_runs_json(day, period)
    if run:
        print(f"  ✓ Run entry found for {day} {period}")
        print(f"    Status: {run.get('status')}")
        print(f"    Total students: {run.get('total_students')}")
        print(f"    Present: {run.get('present_count')}, Absent: {run.get('absent_count')}")
        print(f"    Attendance %: {run.get('attendance_percentage')}%")
        if 'result' in run:
            print(f"    Result object present: ✓")
    else:
        print(f"  ✗ Run entry not found")
        return 1
    
    # Check attendance_website
    print("\n[2] Checking for automatic HTML report generation")
    website_dir = Path(__file__).parent.parent / 'attendance_website'
    if website_dir.exists():
        files = list(website_dir.glob('*'))
        print(f"  Files in attendance_website/: {len(files)}")
        # Count .html files
        html_files = [f.name for f in files if f.suffix == '.html']
        if html_files:
            print(f"    HTML files: {html_files}")
            print(f"  ✗ Automatic HTML generation occurred (should not happen)")
        else:
            print(f"  ✓ No HTML reports auto-generated (expected)")
    
    # Test manual edit
    print("\n[3] Testing manual edit API")
    edit_result = test_manual_edit(day, period)
    
    # Re-validate run after edit
    if edit_result and edit_result.get('success'):
        print("\n[4] Checking run after manual edit")
        run2 = validate_runs_json(day, period)
        if run2:
            print(f"  ✓ Run updated")
            print(f"    Present count (after): {run2.get('present_count')}")
            print(f"    Absent count (after): {run2.get('absent_count')}")
            print(f"    Attendance %: {run2.get('attendance_percentage')}%")
    
    # Test exports
    print("\n[5] Testing exports")
    for fmt in ['csv', 'excel', 'pdf']:
        test_export(day, period, fmt)
    
    print("\n" + "=" * 70)
    print("SMOKE TEST COMPLETE ✓")
    print("=" * 70)
    return 0

if __name__ == '__main__':
    exit(main())
