import csv
import os
import re
import sys
import time
import traceback
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

from flask import Flask, jsonify, request, send_file


# =========================================================
# BASE CONFIG
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
EXPORTS_DIR = BASE_DIR / "exports"
FRONTEND_DIST = BASE_DIR / "my-react-website" / "dist"

INDIA_TZ = timezone(timedelta(hours=5, minutes=30), name="IST")

app = Flask(__name__, static_folder=str(FRONTEND_DIST), static_url_path="")

JOBS = []


# =========================================================
# TIMETABLE CONFIG
# =========================================================

PERIOD_TIMINGS = {
    "P1": {"start": "09:00", "end": "09:50", "process_time": "09:20"},
    "P2": {"start": "09:50", "end": "10:40", "process_time": "10:10"},
    "P3": {"start": "10:50", "end": "11:40", "process_time": "11:10"},
    "P4": {"start": "11:40", "end": "12:30", "process_time": "12:00"},
    "Lunch": {"start": "12:30", "end": "13:20", "process_time": ""},
    "P6": {"start": "13:20", "end": "14:10", "process_time": "13:40"},
    "P7": {"start": "14:20", "end": "15:10", "process_time": "14:40"},
    "P8": {"start": "15:10", "end": "16:00", "process_time": "15:30"},
}

TIMETABLE = {
    "Monday": {
        "P1": {"subject": "SWE", "room": "1106"},
        "P2": {"subject": "SWE", "room": "1106"},
        "P3": {"subject": "CCM/CVO", "room": "1016"},
        "P4": {"subject": "CCM/CVO", "room": "1016"},
        "P6": {"subject": "SWE", "room": "1106"},
        "P7": {"subject": "CCM/CVO", "room": "1106"},
        "P8": {"subject": "CCM/CVO", "room": "1106"},
    },
    "Tuesday": {
        "P1": {"subject": "CCM/CVO", "room": "1106"},
        "P2": {"subject": "CCM/CVO", "room": "1106"},
        "P3": {"subject": "SWE", "room": "1106"},
        "P4": {"subject": "SWE", "room": "1106"},
        "P6": {"subject": "CCM/CVO", "room": "1106"},
        "P7": {"subject": "SWE", "room": "1016"},
        "P8": {"subject": "SWE", "room": "1016"},
    },
    "Wednesday": {
        "P1": {"subject": "SWE", "room": "1106"},
        "P2": {"subject": "SWE", "room": "1106"},
        "P3": {"subject": "CCM/CVO", "room": "1106"},
        "P4": {"subject": "CCM/CVO", "room": "1106"},
        "P6": {"subject": "SWE", "room": "1106"},
        "P7": {"subject": "CCM/CVO", "room": "1016"},
        "P8": {"subject": "CCM/CVO", "room": "1016"},
    },
    "Thursday": {
        "P1": {"subject": "CCM/CVO", "room": "1106"},
        "P2": {"subject": "CCM/CVO", "room": "1106"},
        "P3": {"subject": "SWE", "room": "1106"},
        "P4": {"subject": "SWE", "room": "1106"},
        "P6": {"subject": "CCM/CVO", "room": "1106"},
        "P7": {"subject": "SWE", "room": "1016"},
        "P8": {"subject": "SWE", "room": "1016"},
    },
    "Friday": {
        "P1": {"subject": "SWE", "room": "1106"},
        "P2": {"subject": "SWE", "room": "1106"},
        "P3": {"subject": "CCM/CVO", "room": "1106"},
        "P4": {"subject": "CCM/CVO", "room": "1106"},
        "P6": {"subject": "SWE", "room": "1106"},
        "P7": {"subject": "CCM/CVO", "room": "1106"},
        "P8": {"subject": "SWE/CCM/CVO", "room": "1106"},
    },
}


# =========================================================
# HELPERS
# =========================================================

def ensure_exports_dir():
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


def json_error(message, status=500, **extra):
    return jsonify({
        "success": False,
        "error": message,
        **extra,
    }), status


def normalize_text(value):
    return str(value or "").strip().lower().replace("_", "").replace(" ", "")


def time_to_minutes(time_text):
    if not time_text:
        return -1

    hours, minutes = time_text.split(":")
    return int(hours) * 60 + int(minutes)


def is_probable_attendance_csv(path):
    name = path.name.lower()

    ignored = [
        "detection_log",
        "embedding_summary",
        "student_checkpoint_evidence",
        "checkpoint",
        "camera_summary",
        "slot_summary",
    ]

    if path.suffix.lower() != ".csv":
        return False

    return not any(word in name for word in ignored)


def get_latest_csv():
    ensure_exports_dir()

    csv_files = [
        file for file in EXPORTS_DIR.glob("*.csv")
        if file.is_file() and is_probable_attendance_csv(file)
    ]

    if not csv_files:
        return None

    attendance_files = [
        file for file in csv_files
        if "attendance" in file.name.lower()
    ]

    candidates = attendance_files if attendance_files else csv_files

    return max(candidates, key=lambda file: file.stat().st_mtime)


def find_new_csv_after(start_timestamp):
    ensure_exports_dir()

    candidates = []

    for file in EXPORTS_DIR.glob("*.csv"):
        if not file.is_file():
            continue

        if not is_probable_attendance_csv(file):
            continue

        if file.stat().st_mtime >= start_timestamp - 2:
            candidates.append(file)

    if not candidates:
        return None

    return max(candidates, key=lambda file: file.stat().st_mtime)


def read_csv_rows(path):
    if not path or not path.exists():
        return []

    for encoding in ["utf-8-sig", "utf-8", "cp1252"]:
        try:
            with path.open("r", encoding=encoding, newline="") as file:
                reader = csv.DictReader(file)
                rows = list(reader)

            cleaned_rows = []

            for row in rows:
                cleaned_row = {}

                for key, value in row.items():
                    if key is None:
                        continue

                    cleaned_row[str(key).strip()] = "" if value is None else str(value).strip()

                cleaned_rows.append(cleaned_row)

            return cleaned_rows

        except UnicodeDecodeError:
            continue

    return []


def detect_status(row):
    possible_columns = [
        "Status",
        "status",
        "attendance_status",
        "Attendance Status",
        "final_status",
        "Final Status",
        "Attendance",
        "attendance",
        "Result",
        "result",
    ]

    normalized_keys = {
        normalize_text(key): key
        for key in row.keys()
    }

    for column in possible_columns:
        matched_key = normalized_keys.get(normalize_text(column))

        if matched_key:
            value = str(row.get(matched_key, "")).strip()

            if value:
                return value

    for value in row.values():
        text = str(value or "").strip().lower()

        if text.startswith("present"):
            return "Present"

        if text.startswith("absent"):
            return "Absent"

        if "unknown" in text:
            return "Unknown"

    return "Unknown"


def get_roll_no(row):
    return (
        row.get("roll_no")
        or row.get("Roll_No")
        or row.get("roll")
        or row.get("Roll")
        or row.get("RollNo")
        or row.get("Roll No")
        or row.get("Roll Number")
        or row.get("student_id")
        or row.get("Student_ID")
        or "-"
    )


def summarize_rows(rows):
    total = len(rows)
    present = 0
    absent = 0
    unknown = 0

    present_roll_numbers = []
    absent_roll_numbers = []

    for row in rows:
        status = detect_status(row).lower()
        roll_no = str(get_roll_no(row))

        if "present" in status:
            present += 1
            present_roll_numbers.append(roll_no)
        elif "absent" in status:
            absent += 1
            absent_roll_numbers.append(roll_no)
        else:
            unknown += 1

    recognition_rate = round((present / total) * 100, 2) if total else 0

    return {
        "total_students": total,
        "present": present,
        "absent": absent,
        "unknown": unknown,
        "recognition_rate": recognition_rate,
        "present_roll_numbers": present_roll_numbers,
        "absent_roll_numbers": absent_roll_numbers,
    }


def latest_attendance_payload():
    latest_csv = get_latest_csv()

    if not latest_csv:
        return {
            "success": True,
            "latest_file": "",
            "rows": [],
            "total_students": 0,
            "present": 0,
            "absent": 0,
            "unknown": 0,
            "recognition_rate": 0,
            "present_roll_numbers": [],
            "absent_roll_numbers": [],
        }

    rows = read_csv_rows(latest_csv)

    return {
        "success": True,
        "latest_file": latest_csv.name,
        "rows": rows,
        **summarize_rows(rows),
    }


def get_video_files():
    folders = [
        BASE_DIR / "cctv_videos",
        BASE_DIR / "videos",
        BASE_DIR / "test_videos",
    ]

    allowed = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
    videos = []

    for folder in folders:
        if not folder.exists():
            continue

        for path in folder.rglob("*"):
            if not path.is_file():
                continue

            if path.suffix.lower() not in allowed:
                continue

            videos.append({
                "name": path.name,
                "filename": path.name,
                "path": str(path.relative_to(BASE_DIR)),
                "size_mb": round(path.stat().st_size / (1024 * 1024), 2),
                "modified_at": datetime.fromtimestamp(
                    path.stat().st_mtime,
                    INDIA_TZ
                ).strftime("%d-%m-%Y %I:%M %p"),
            })

    return sorted(videos, key=lambda item: item["name"])


def patch_disable_html_generation():
    """
    The old HTML report generation is crashing after video processing.
    This keeps video attendance running and avoids old template crashes.
    """
    script_path = BASE_DIR / "scripts" / "timetable_attendance.py"

    if not script_path.exists():
        return

    text = script_path.read_text(encoding="utf-8", errors="ignore")
    patched = re.sub(r"generate_html\s*=\s*True", "generate_html=False", text)

    if patched != text:
        backup = BASE_DIR / "scripts" / "timetable_attendance_backup_auto_html_fix.py"

        if not backup.exists():
            backup.write_text(text, encoding="utf-8")

        script_path.write_text(patched, encoding="utf-8")


def current_context_payload():
    now = datetime.now(INDIA_TZ)
    day = now.strftime("%A")
    current_minutes = now.hour * 60 + now.minute

    current_period = None

    for period, timing in PERIOD_TIMINGS.items():
        start = time_to_minutes(timing["start"])
        end = time_to_minutes(timing["end"])

        if start <= current_minutes < end:
            current_period = period
            break

    subject = "-"
    room = "-"
    process_time = ""

    if current_period:
        process_time = PERIOD_TIMINGS[current_period]["process_time"]

        class_info = TIMETABLE.get(day, {}).get(current_period)

        if class_info:
            subject = class_info["subject"]
            room = class_info["room"]

    can_process = False

    if not current_period:
        recommendation = "No active class period right now."
        badge = "danger"
    elif current_period == "Lunch":
        recommendation = "Lunch break. Attendance not required."
        badge = "warning"
    else:
        start = time_to_minutes(PERIOD_TIMINGS[current_period]["start"])

        if current_minutes < start + 10:
            recommendation = "Wait for settling time before taking attendance."
            badge = "warning"
        else:
            recommendation = "Recommended: take attendance now."
            badge = "success"
            can_process = True

    return {
        "success": True,
        "current_date": now.strftime("%d-%m-%Y"),
        "display_date": now.strftime("%A, %d %B %Y"),
        "current_day": day,
        "current_time": now.strftime("%H:%M:%S"),
        "display_time": now.strftime("%I:%M:%S %p"),
        "current_period": current_period,
        "current_subject": subject,
        "room": room,
        "recommendation": recommendation,
        "recommendation_badge": badge,
        "can_process": can_process,
        "process_time": process_time,
        "recommended_time": process_time,
    }


def add_job(job):
    JOBS.insert(0, job)

    if len(JOBS) > 30:
        JOBS.pop()


def run_attendance_script(day, period, process_time, reprocess=False):
    ensure_exports_dir()

    start_timestamp = time.time()
    started_at = datetime.now(INDIA_TZ)

    job = {
        "id": f"JOB-{int(start_timestamp)}",
        "day": day,
        "period": period,
        "status": "running",
        "started_at": started_at.strftime("%d-%m-%Y %I:%M:%S %p"),
        "finished_at": "",
        "latest_file": "",
        "stdout": "",
        "stderr": "",
    }

    script_path = BASE_DIR / "scripts" / "timetable_attendance.py"

    if not script_path.exists():
        job["status"] = "failed"
        job["stderr"] = f"Script not found: {script_path}"
        job["finished_at"] = datetime.now(INDIA_TZ).strftime("%d-%m-%Y %I:%M:%S %p")
        add_job(job)

        return {
            "success": False,
            "error": f"Script not found: {script_path}",
            "stdout": "",
            "stderr": job["stderr"],
        }

    videos = get_video_files()

    if not videos:
        job["status"] = "failed"
        job["stderr"] = "No CCTV videos found in cctv_videos, videos, or test_videos."
        job["finished_at"] = datetime.now(INDIA_TZ).strftime("%d-%m-%Y %I:%M:%S %p")
        add_job(job)

        return {
            "success": False,
            "error": "No CCTV videos found.",
            "stdout": "",
            "stderr": job["stderr"],
        }

    patch_disable_html_generation()

    command = [
        sys.executable,
        str(script_path),
        "--day",
        str(day),
        "--time",
        str(process_time),
    ]

    try:
        completed = subprocess.run(
            command,
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=300,
        )

        stdout = completed.stdout or ""
        stderr = completed.stderr or ""

        new_csv = find_new_csv_after(start_timestamp)
        finished_at = datetime.now(INDIA_TZ)

        if not new_csv:
            job["status"] = "failed"
            job["finished_at"] = finished_at.strftime("%d-%m-%Y %I:%M:%S %p")
            job["stdout"] = stdout
            job["stderr"] = stderr or "Videos processed, but no CSV was saved in exports."
            add_job(job)

            return {
                "success": False,
                "error": "Videos processed, but attendance was not saved. No new CSV was created in exports.",
                "day": day,
                "period": period,
                "time": process_time,
                "videos_found": len(videos),
                "returncode": completed.returncode,
                "stdout": stdout,
                "stderr": stderr or "No new CSV was created.",
            }

        rows = read_csv_rows(new_csv)
        summary = summarize_rows(rows)

        job["status"] = "success"
        job["finished_at"] = finished_at.strftime("%d-%m-%Y %I:%M:%S %p")
        job["latest_file"] = new_csv.name
        job["stdout"] = stdout
        job["stderr"] = stderr
        add_job(job)

        return {
            "success": True,
            "warning": "" if completed.returncode == 0 else "Script returned an error after saving CSV. Attendance was still saved.",
            "reprocess": reprocess,
            "day": day,
            "period": period,
            "time": process_time,
            "videos_found": len(videos),
            "latest_file": new_csv.name,
            "rows": rows,
            **summary,
            "returncode": completed.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "command": " ".join(command),
        }

    except subprocess.TimeoutExpired as exc:
        job["status"] = "failed"
        job["finished_at"] = datetime.now(INDIA_TZ).strftime("%d-%m-%Y %I:%M:%S %p")
        job["stderr"] = "Attendance processing timed out after 300 seconds."
        add_job(job)

        return {
            "success": False,
            "error": "Attendance processing timed out after 300 seconds.",
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
        }

    except Exception as exc:
        job["status"] = "failed"
        job["finished_at"] = datetime.now(INDIA_TZ).strftime("%d-%m-%Y %I:%M:%S %p")
        job["stderr"] = traceback.format_exc()
        add_job(job)

        return {
            "success": False,
            "error": "Unexpected backend error while processing attendance.",
            "details": str(exc),
            "traceback": traceback.format_exc(),
        }


# =========================================================
# API ROUTES
# =========================================================

@app.route("/api/health", methods=["GET"])
def api_health():
    return jsonify({
        "success": True,
        "message": "Smart Attendance API is running",
        "title": "Sreenidhi University Smart Attendance",
        "server": "python app.py",
        "time": datetime.now(INDIA_TZ).strftime("%d-%m-%Y %I:%M:%S %p"),
    })


@app.route("/api/dashboard", methods=["GET"])
def api_dashboard():
    try:
        return jsonify(latest_attendance_payload())
    except Exception as exc:
        return json_error(
            "Failed to load dashboard data.",
            traceback=traceback.format_exc(),
            details=str(exc),
        )


@app.route("/api/attendance/latest", methods=["GET"])
def api_latest_attendance():
    try:
        return jsonify(latest_attendance_payload())
    except Exception as exc:
        return json_error(
            "Failed to load latest attendance.",
            traceback=traceback.format_exc(),
            details=str(exc),
        )


@app.route("/api/current-context", methods=["GET"])
def api_current_context():
    return jsonify(current_context_payload())


@app.route("/api/videos", methods=["GET"])
def api_videos():
    return jsonify(get_video_files())


@app.route("/api/jobs", methods=["GET"])
def api_jobs():
    return jsonify(JOBS)


@app.route("/api/reports", methods=["GET"])
def api_reports():
    ensure_exports_dir()

    allowed = {".csv", ".xlsx", ".pdf", ".html"}
    files = []

    for path in EXPORTS_DIR.iterdir():
        if not path.is_file():
            continue

        if path.suffix.lower() not in allowed:
            continue

        stat = path.stat()

        files.append({
            "name": path.name,
            "type": path.suffix.replace(".", "").upper(),
            "size_kb": round(stat.st_size / 1024, 2),
            "modified_timestamp": stat.st_mtime,
            "modified_at": datetime.fromtimestamp(
                stat.st_mtime,
                INDIA_TZ
            ).strftime("%d-%m-%Y %I:%M %p"),
            "download_url": f"/api/download/{path.name}",
        })

    files.sort(key=lambda item: item["modified_timestamp"], reverse=True)

    return jsonify(files)


@app.route("/api/process-period", methods=["POST"])
def api_process_period():
    payload = request.get_json(silent=True) or {}

    day = payload.get("day")
    period = payload.get("period")
    process_time = payload.get("time") or payload.get("process_time")

    if not day:
        day = current_context_payload().get("current_day")

    if not period:
        period = current_context_payload().get("current_period")

    if not period or period == "Lunch":
        return jsonify({
            "success": False,
            "error": "No valid class period selected.",
        }), 200

    if period not in PERIOD_TIMINGS:
        return jsonify({
            "success": False,
            "error": f"Invalid period: {period}",
        }), 200

    process_time = process_time or PERIOD_TIMINGS[period]["process_time"]

    result = run_attendance_script(day, period, process_time, reprocess=False)

    return jsonify(result), 200


@app.route("/api/reprocess-period", methods=["POST"])
def api_reprocess_period():
    payload = request.get_json(silent=True) or {}

    day = payload.get("day")
    period = payload.get("period")
    process_time = payload.get("time") or payload.get("process_time")

    if not day or not period:
        return jsonify({
            "success": False,
            "error": "Day and period are required for reprocess.",
        }), 200

    process_time = process_time or PERIOD_TIMINGS.get(period, {}).get("process_time", "")

    result = run_attendance_script(day, period, process_time, reprocess=True)

    return jsonify(result), 200


@app.route("/api/process-video", methods=["POST"])
def api_process_video():
    payload = request.get_json(silent=True) or {}

    day = payload.get("day") or "Friday"
    period = payload.get("period") or "P1"
    process_time = payload.get("time") or PERIOD_TIMINGS.get(period, {}).get("process_time", "09:20")

    result = run_attendance_script(day, period, process_time, reprocess=False)

    return jsonify(result), 200


@app.route("/api/download/<path:filename>", methods=["GET"])
def api_download(filename):
    ensure_exports_dir()

    safe_name = os.path.basename(filename)
    file_path = EXPORTS_DIR / safe_name

    if not file_path.exists() or not file_path.is_file():
        return json_error("Requested file was not found.", status=404)

    return send_file(file_path, as_attachment=False)


@app.route("/api/manual-edit", methods=["POST"])
def api_manual_edit():
    ensure_exports_dir()

    payload = request.get_json(silent=True) or {}
    rows = payload.get("rows", [])

    if not isinstance(rows, list):
        return jsonify({
            "success": False,
            "error": "Rows must be a list.",
        }), 200

    if not rows:
        return jsonify({
            "success": False,
            "error": "No rows received to save.",
        }), 200

    timestamp = datetime.now(INDIA_TZ).strftime("%Y%m%d_%H%M%S")
    edited_file = f"attendance_edited_{timestamp}.csv"
    output_path = EXPORTS_DIR / edited_file

    fieldnames = []

    for row in rows:
        if not isinstance(row, dict):
            continue

        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)

    with output_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow({
                key: row.get(key, "")
                for key in fieldnames
            })

    return jsonify({
        "success": True,
        "edited_file": edited_file,
        "download_url": f"/api/download/{edited_file}",
    })


# =========================================================
# REACT STATIC SERVING
# =========================================================

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react(path):
    if path.startswith("api/"):
        return json_error("API route not found.", status=404)

    index_file = FRONTEND_DIST / "index.html"

    if path:
        requested_file = FRONTEND_DIST / path

        if requested_file.exists() and requested_file.is_file():
            return send_file(requested_file)

    if not index_file.exists():
        return """
        <h1>React build not found</h1>
        <p>Run this first:</p>
        <pre>
cd my-react-website
npm run build
cd ..
python app.py
        </pre>
        """, 500

    return send_file(index_file)


if __name__ == "__main__":
    ensure_exports_dir()
    app.run(host="127.0.0.1", port=5000, debug=True)