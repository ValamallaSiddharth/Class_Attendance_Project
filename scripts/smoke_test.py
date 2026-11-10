import time
import requests
import os

BASE = 'http://127.0.0.1:5000'

def pick_period_for_day(day='Tuesday'):
    r = requests.get(f"{BASE}/api/timetable?day={day}")
    r.raise_for_status()
    tt = r.json().get('timetable', [])
    for row in tt:
        if row.get('subject','').upper()!='LUNCH':
            return row['period']
    return None


def start_job(day, period):
    r = requests.post(f"{BASE}/api/process", json={'day': day, 'period': period})
    r.raise_for_status()
    return r.json()


def poll_job(job_id, timeout=600):
    start = time.time()
    while time.time()-start < timeout:
        r = requests.get(f"{BASE}/api/status/{job_id}")
        if r.status_code==200:
            job = r.json()
            print('Job status:', job.get('status'))
            if job.get('status') in ('Completed','Failed'):
                return job
        else:
            print('Status fetch failed', r.status_code, r.text)
        time.sleep(4)
    raise TimeoutError('Job did not finish in time')


def get_runs():
    r = requests.get(f"{BASE}/api/runs")
    r.raise_for_status()
    return r.json().get('runs', [])


def get_run(day, period):
    key = f"{day}_{period}".replace(' ', '_')
    runs = get_runs()
    for r in runs:
        if r.get('day')==day and str(r.get('period'))==str(period):
            return r
    # fallback to map key
    return None


def edit_first_student(day, period):
    run = get_run(day, period)
    students = run.get('students', [])
    if not students:
        print('No students to edit')
        return None
    first = students[0]
    roll = first.get('roll_number')
    # flip status
    new_status = 'Present' if first.get('status')!='Present' else 'Absent'
    changes = [{'roll': roll, 'status': new_status, 'reason': 'Smoke test edit'}]
    r = requests.post(f"{BASE}/api/attendance/{day}/{period}/edit", json={'changes': changes})
    print('Edit response:', r.status_code, r.text)
    return r.json()


def export(day, period, fmt):
    r = requests.get(f"{BASE}/api/export/{day}/{period}?format={fmt}")
    print(f'Export {fmt}:', r.status_code, r.text[:200])
    return r


if __name__=='__main__':
    day = 'Tuesday'
    period = pick_period_for_day(day)
    if not period:
        print('No suitable period found for', day)
        exit(1)
    print('Selected period', period)

    before_files = set(os.listdir(os.path.join(os.path.dirname(__file__), '..', 'attendance_website')))
    print('Attendance website files before:', len(before_files))

    resp = start_job(day, period)
    print('Start job response:', resp)
    job_id = resp.get('job_id')
    if not job_id:
        print('No job id returned; abort')
        exit(1)

    job = poll_job(job_id)
    print('Job finished:', job)

    # validate runs
    runs = get_runs()
    print('Total runs stored:', len(runs))
    run = get_run(day, period)
    print('Run entry:', run)

    after_files = set(os.listdir(os.path.join(os.path.dirname(__file__), '..', 'attendance_website')))
    new_files = after_files - before_files
    print('New attendance_website files created:', new_files)

    # manual edit
    edit_resp = edit_first_student(day, period)
    print('Manual edit response:', edit_resp)

    # fetch run again
    run2 = get_run(day, period)
    print('Run after edit:', run2)

    # exports
    export(day, period, 'csv')
    try:
        export(day, period, 'excel')
    except Exception as e:
        print('Excel export error', e)
    export(day, period, 'pdf')

    print('Smoke test complete')
