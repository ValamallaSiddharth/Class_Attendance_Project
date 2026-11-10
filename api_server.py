from flask import Flask, jsonify, send_file
from flask_cors import CORS
from pathlib import Path
import csv
import os
import sys
import subprocess

BASE_DIR = Path(__file__).resolve().parent
EXPORTS_DIR = BASE_DIR / "exports"

app = Flask(__name__)
CORS(app)


def get_latest_file(extensions):
    if not EXPORTS_DIR.exists():
        return None

    files = []
    for ext in extensions:
        files.extend(EXPORTS_DIR.glob(f"*{ext}"))

    if not files:
        return None

    return max(files, key=lambda file: file.stat().st_mtime)


def read_csv_file(file_path):
    rows = []

    with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            clean_row = {}
            for key, value in row.items():
                clean_key = str(key).strip() if key else ""
                clean_value = str(value).strip() if value else ""
                clean_row[clean_key] = clean_value
            rows.append(clean_row)

    return rows


def find_status_value(row):
    possible_status_columns = [
        "status",
        "Status",
        "attendance_status",
        "Attendance Status",
        "final_status",
        "Final Status",
    ]

    for column in possible_status_columns:
        if column in row:
            return str(row[column]).lower()

    values = " ".join(str(value).lower() for value in row.values())

    if "present" in values:
        return "present"

    if "absent" in values:
        return "absent"

    return "unknown"


@app.route("/")
def home():
    return jsonify({
        "message": "Smart Attendance API is running",
        "exports_folder": str(EXPORTS_DIR)
    })


@app.route("/api/dashboard")
def dashboard():
    latest_csv = get_latest_file([".csv"])

    if latest_csv is None:
        return jsonify({
            "total_students": 0,
            "present": 0,
            "absent": 0,
            "unknown": 0,
            "recognition_rate": 0,
            "latest_file": None,
            "rows": []
        })

    rows = read_csv_file(latest_csv)

    total_students = len(rows)
    present = 0
    absent = 0
    unknown = 0

    for row in rows:
        status = find_status_value(row)

        if "present" in status:
            present += 1
        elif "absent" in status:
            absent += 1
        else:
            unknown += 1

    recognition_rate = round((present / total_students) * 100, 2) if total_students else 0

    return jsonify({
        "total_students": total_students,
        "present": present,
        "absent": absent,
        "unknown": unknown,
        "recognition_rate": recognition_rate,
        "latest_file": latest_csv.name,
        "rows": rows
    })


@app.route("/api/attendance/latest")
def latest_attendance():
    latest_csv = get_latest_file([".csv"])

    if latest_csv is None:
        return jsonify({
            "file": None,
            "rows": []
        })

    return jsonify({
        "file": latest_csv.name,
        "rows": read_csv_file(latest_csv)
    })


@app.route("/api/reports")
def reports():
    if not EXPORTS_DIR.exists():
        return jsonify([])

    files = []

    for file in EXPORTS_DIR.glob("*"):
        if file.suffix.lower() in [".csv", ".xlsx"]:
            files.append({
                "name": file.name,
                "size_kb": round(file.stat().st_size / 1024, 2),
                "type": file.suffix.lower().replace(".", ""),
                "download_url": f"/api/download/{file.name}"
            })

    files = sorted(files, key=lambda item: item["name"], reverse=True)

    return jsonify(files)


@app.route("/api/download/<filename>")
def download_file(filename):
    file_path = EXPORTS_DIR / filename

    if not file_path.exists():
        return jsonify({"error": "File not found"}), 404

    return send_file(file_path, as_attachment=True)



@app.route("/api/process-period", methods=["POST"])
def process_period():
    from flask import request

    data = request.get_json() or {}

    day = data.get("day", "Tuesday")
    time_value = data.get("time", "09:20")
    period = data.get("period", "P1")

    script_path = BASE_DIR / "scripts" / "timetable_attendance.py"

    if not script_path.exists():
        return jsonify({
            "success": False,
            "error": "timetable_attendance.py not found",
            "script_path": str(script_path)
        }), 404

    command = [
        sys.executable,
        str(script_path),
        "--day",
        day,
        "--time",
        time_value
    ]

    try:
        result = subprocess.run(
            command,
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=300
        )

        latest_csv = get_latest_file([".csv"])
        rows = read_csv_file(latest_csv) if latest_csv else []

        return jsonify({
            "success": result.returncode == 0,
            "period": period,
            "day": day,
            "time": time_value,
            "command": " ".join(command),
            "stdout": result.stdout,
            "stderr": result.stderr,
            "latest_file": latest_csv.name if latest_csv else None,
            "rows": rows
        })

    except subprocess.TimeoutExpired:
        return jsonify({
            "success": False,
            "error": "Attendance processing took too long and was stopped."
        }), 500

    except Exception as error:
        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)

