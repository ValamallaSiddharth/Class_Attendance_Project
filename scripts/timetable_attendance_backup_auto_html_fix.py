import cv2
import os
import csv
import sys
import pickle
import argparse
import numpy as np
from collections import defaultdict
from datetime import datetime, time

# ============================================================
# ABSOLUTE PATHS  (work regardless of working directory)
# ============================================================

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR   = os.path.dirname(_SCRIPT_DIR)   # project root

VIDEO_DIR   = os.path.join(_ROOT_DIR, "cctv_videos")
MODEL_DIR   = os.path.join(_ROOT_DIR, "models")
WEBSITE_DIR = os.path.join(_ROOT_DIR, "attendance_website")
DETAILS_DIR = os.path.join(WEBSITE_DIR, "details")

TIMETABLE_PATH          = os.path.join(_ROOT_DIR, "timetable", "class_timetable.csv")
ATTENDANCE_TEMPLATE_PATH = os.path.join(_ROOT_DIR, "templates", "attendance_template.html")
DETAIL_TEMPLATE_PATH    = os.path.join(_ROOT_DIR, "templates", "student_detail_template.html")
TEACHER_TEMPLATE_PATH   = os.path.join(_ROOT_DIR, "templates", "teacher_dashboard_template.html")

YUNET_MODEL    = os.path.join(MODEL_DIR, "face_detection_yunet_2023mar.onnx")
SFACE_MODEL    = os.path.join(MODEL_DIR, "face_recognition_sface_2021dec.onnx")
EMBEDDINGS_FILE = os.path.join(MODEL_DIR, "sface_embeddings.pkl")

# ============================================================
# SETTINGS
# ============================================================

SIMILARITY_THRESHOLD      = 0.42
MIN_DETECTIONS_FOR_PRESENT = 3
FRAME_SKIP                = 2

os.makedirs(WEBSITE_DIR, exist_ok=True)
os.makedirs(DETAILS_DIR, exist_ok=True)

# ============================================================
# MODULE-LEVEL STATE
# These are set by run_attendance() so all helper functions
# can reference them as globals without needing parameter changes.
# ============================================================

timetable        = []
selected_day     = None
selected_time    = None
active_period    = None
demo_mode        = False

detector         = None
recognizer       = None
student_embeddings = {}
all_students     = []
video_files      = []

# ============================================================
# TIMETABLE HELPER FUNCTIONS
# ============================================================

def normalize_day(day_name):
    day_name = day_name.strip().lower()
    mapping = {
        "mon": "Monday",   "monday": "Monday",
        "tue": "Tuesday",  "tuesday": "Tuesday",
        "wed": "Wednesday","wednesday": "Wednesday",
        "thu": "Thursday", "thursday": "Thursday",
        "fri": "Friday",   "friday": "Friday",
        "sat": "Saturday", "saturday": "Saturday",
        "sun": "Sunday",   "sunday": "Sunday",
    }
    return mapping.get(day_name, day_name.capitalize())


def parse_time(time_text):
    hour, minute = map(int, time_text.strip().split(":"))
    return time(hour, minute)


def load_timetable():
    rows = []
    with open(TIMETABLE_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "day":         normalize_day(row["day"]),
                "period":      row["period"].strip(),
                "subject":     row["subject"].strip(),
                "start_time":  row["start_time"].strip(),
                "end_time":    row["end_time"].strip(),
                "room":        row["room"].strip(),
                "course_code": row.get("course_code", "-").strip(),
                "course_name": row.get("course_name", "-").strip(),
                "teacher":     row.get("teacher", "-").strip(),
            })
    return rows


def find_active_period(tt, day, t):
    for row in tt:
        if row["day"] != day:
            continue
        start = parse_time(row["start_time"])
        end   = parse_time(row["end_time"])
        if start <= t < end:
            return row
    return None


def safe_filename(text):
    return (
        text.replace("/", "_")
            .replace("\\", "_")
            .replace(" ", "_")
            .replace(":", "-")
    )

# ============================================================
# FACE FUNCTIONS  (use module globals: detector, recognizer,
#                  student_embeddings — set by run_attendance)
# ============================================================

def detect_faces(frame):
    height, width = frame.shape[:2]
    detector.setInputSize((width, height))
    _, faces = detector.detect(frame)
    return [] if faces is None else faces


def create_embedding(frame, face):
    aligned_face = recognizer.alignCrop(frame, face)
    embedding    = recognizer.feature(aligned_face)
    embedding    = embedding.flatten()
    norm = np.linalg.norm(embedding)
    if norm == 0:
        return None
    return embedding / norm


def cosine_similarity(a, b):
    return float(np.dot(a, b))


def match_face(query_embedding):
    best_roll  = "Unknown"
    best_score = -1
    for roll_no, embeddings in student_embeddings.items():
        for stored in embeddings:
            score = cosine_similarity(query_embedding, stored)
            if score > best_score:
                best_score = score
                best_roll  = roll_no
    if best_score >= SIMILARITY_THRESHOLD:
        return best_roll, best_score
    return "Unknown", best_score


def extract_checkpoint_frames(
    video_path,
    output_dir,
    frames_per_checkpoint=10,
    every_n_seconds=1,
    max_frames=10,
    start_seconds=0,
):
    """Extract a small set of frames from a video for checkpoint processing."""
    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return []

    fps = cap.get(cv2.CAP_PROP_FPS) or 1
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if total_frames <= 0:
        cap.release()
        return []

    if start_seconds > 0:
        cap.set(cv2.CAP_PROP_POS_MSEC, float(start_seconds) * 1000.0)

    interval = max(1, int(round(every_n_seconds * fps)))
    saved_paths = []
    frame_index = 0
    saved_count = 0
    target_frames = min(frames_per_checkpoint, max_frames)

    while saved_count < target_frames:
        success, frame = cap.read()
        if not success:
            break

        if frame_index % interval == 0:
            filename = f"frame_{saved_count + 1:03d}.jpg"
            out_path = os.path.join(output_dir, filename)
            cv2.imwrite(out_path, frame)
            saved_paths.append(out_path)
            saved_count += 1

        frame_index += 1
        if frame_index > total_frames:
            break

    cap.release()
    return saved_paths


def process_attendance_images(image_paths, checkpoint_name, evidence_dir):
    """Run YuNet + SFace on a small set of checkpoint images and save evidence crops."""
    os.makedirs(evidence_dir, exist_ok=True)
    checkpoint_results = {}

    for image_path in image_paths:
        image = cv2.imread(image_path)
        if image is None:
            continue

        faces = detect_faces(image)
        for face_index, face in enumerate(faces, start=1):
            query_embedding = create_embedding(image, face)
            if query_embedding is None:
                continue

            roll_no, score = match_face(query_embedding)
            if roll_no == "Unknown":
                continue

            result = checkpoint_results.setdefault(
                roll_no,
                {
                    "detection_count": 0,
                    "similarity_sum": 0.0,
                    "best_similarity": 0.0,
                    "evidence_images": [],
                    "checkpoint_name": checkpoint_name,
                },
            )

            result["detection_count"] += 1
            result["similarity_sum"] += score
            result["best_similarity"] = max(result["best_similarity"], score)

            try:
                crop = recognizer.alignCrop(image, face)
                evidence_filename = f"{checkpoint_name}_{roll_no}_{len(result['evidence_images']) + 1:03d}.jpg"
                evidence_path = os.path.join(evidence_dir, evidence_filename)
                cv2.imwrite(evidence_path, crop)
                result["evidence_images"].append(evidence_path)
            except Exception:
                continue

    final_results = {}
    for roll_no, result in checkpoint_results.items():
        count = result["detection_count"]
        avg_similarity = round(result["similarity_sum"] / count, 3) if count else 0.0
        final_results[roll_no] = {
            "detection_count": count,
            "best_similarity": round(result["best_similarity"], 3),
            "average_similarity": avg_similarity,
            "evidence_images": result["evidence_images"],
            "checkpoint_name": checkpoint_name,
        }

    return final_results

# ============================================================
# HTML GENERATION HELPERS
# (use module globals: active_period, selected_day, timetable,
#  demo_mode, all_students, video_files — set by run_attendance)
# ============================================================

def get_section():
    return active_period.get("section", "AIML")


def get_today_date_text():
    return datetime.now().strftime("%A | %d %B %Y")


def calculate_summary(attendance_data):
    total_students   = len(attendance_data)
    present_students = [s for s in attendance_data if s["Status"] == "Present"]
    absent_students  = [s for s in attendance_data if s["Status"] == "Absent"]
    present_count    = len(present_students)
    absent_count     = len(absent_students)

    if total_students == 0:
        attendance_percentage = 0
    else:
        attendance_percentage = round((present_count / total_students) * 100, 1)

    confidence_values = []
    for student in attendance_data:
        val = student["Best_Similarity"]
        if val != "-":
            try:
                confidence_values.append(float(val))
            except ValueError:
                pass

    if confidence_values:
        avg_confidence = round((sum(confidence_values) / len(confidence_values)) * 100, 1)
    else:
        avg_confidence = 0

    return {
        "total_students":        total_students,
        "present_students":      present_students,
        "absent_students":       absent_students,
        "present_count":         present_count,
        "absent_count":          absent_count,
        "attendance_percentage": attendance_percentage,
        "videos_processed":      len(video_files),
        "avg_confidence":        avg_confidence,
    }


def replace_common_class_info(html):
    mode_text = "Demo/Test Mode" if demo_mode else "Real Current Time Mode"
    replacements = {
        "{{SUBJECT}}":              active_period["subject"],
        "{{COURSE_CODE}}":          active_period["course_code"],
        "{{COURSE_NAME}}":          active_period["course_name"],
        "{{TEACHER}}":              active_period["teacher"],
        "{{DAY}}":                  selected_day,
        "{{DATE}}":                 get_today_date_text(),
        "{{PERIOD}}":               active_period["period"],
        "{{START_TIME}}":           active_period["start_time"],
        "{{END_TIME}}":             active_period["end_time"],
        "{{ROOM}}":                 active_period["room"],
        "{{SECTION}}":              get_section(),
        "{{MODE}}":                 mode_text,
        "{{MIN_DETECTIONS}}":       str(MIN_DETECTIONS_FOR_PRESENT),
        "{{SIMILARITY_THRESHOLD}}": str(SIMILARITY_THRESHOLD),
    }
    for key, val in replacements.items():
        html = html.replace(key, str(val))
    return html


def create_reason(student):
    # Manual override takes priority in the explanation
    if student.get("Manual_Override"):
        orig   = student.get("Original_AI_Status", "—")
        reason = student.get("Override_Reason", "No reason provided")
        editor = student.get("Edited_By", "Main Admin")
        return (
            f"Status was manually overridden by {editor} from '{orig}' "
            f"to '{student['Status']}'. Reason: {reason}."
        )
    count  = student["Detection_Count"]
    status = student["Status"]
    if status == "Present":
        return "Student satisfied the minimum detection rule and was marked Present."
    if count == 0:
        return "Student was not detected in any CCTV video for this class period."
    return (
        "Student was detected, but the detection count was below the required minimum. "
        "This may happen due to side face, blur, distance, low lighting, or weak visibility."
    )


def get_status_badge(status):
    css = "present" if status == "Present" else "absent"
    return f'<span class="badge {css}">{status}</span>'


def build_attendance_rows(students, detail_links=None, include_detail=True):
    rows = ""
    for student in students:
        roll_no     = student["Roll_Number"]
        status      = student["Status"]
        detail_link = "#"
        if detail_links is not None:
            detail_link = detail_links.get(roll_no, "#")
        details_btn = ""
        if include_detail:
            details_btn = f'<td><a class="btn" href="{detail_link}">View Details</a></td>'

        # Manual override badge
        override_badge = ""
        if student.get("Manual_Override"):
            reason_txt = student.get("Override_Reason", "") or ""
            title_attr = f'title="{reason_txt}"' if reason_txt else ""
            override_badge = (
                f' <span class="badge override" {title_attr}>'
                f'&#9998; Edited by Admin</span>'
            )

        rows += f"""
        <tr>
            <td>{roll_no}</td>
            <td>{get_status_badge(status)}{override_badge}</td>
            <td>{student["Detection_Count"]}</td>
            <td>{student["Best_Similarity"]}</td>
            <td>{student["Average_Similarity"]}</td>
            <td>{student["Detected_In_Videos"]}</td>
            {details_btn}
        </tr>
        """
    if rows == "":
        colspan = "7" if include_detail else "6"
        rows = f'<tr><td colspan="{colspan}" class="empty">No records found.</td></tr>'
    return rows


def build_teacher_attendance_rows(students, detail_links=None):
    rows = ""
    for student in students:
        roll_no     = student["Roll_Number"]
        status      = student["Status"]
        detail_link = "#"
        if detail_links is not None:
            detail_link = detail_links.get(roll_no, "#")

        # Manual override badge
        override_badge = ""
        if student.get("Manual_Override"):
            reason_txt = student.get("Override_Reason", "") or ""
            title_attr = f'title="{reason_txt}"' if reason_txt else ""
            override_badge = (
                f' <span class="badge override" {title_attr}>'
                f'&#9998; Edited by Admin</span>'
            )

        rows += f"""
        <tr>
            <td>{roll_no}</td>
            <td>{get_status_badge(status)}{override_badge}</td>
            <td>{student["Detection_Count"]}</td>
            <td>{student["Best_Similarity"]}</td>
            <td>{student["Average_Similarity"]}</td>
            <td>{student["Detected_In_Videos"]}</td>
            <td><a class="btn" href="{detail_link}">View</a></td>
        </tr>
        """
    if rows == "":
        rows = '<tr><td colspan="7" class="empty">No records found.</td></tr>'
    return rows


def build_detection_rows(attendance_data):
    rows = ""
    for student in attendance_data:
        if student["Detection_Count"] == 0:
            continue
        rows += f"""
        <tr>
            <td>{datetime.now().strftime("%I:%M:%S %p")}</td>
            <td>{student["Detected_In_Videos"]}</td>
            <td>{student["Roll_Number"]}</td>
            <td>{student["Best_Similarity"]}</td>
            <td>{get_status_badge(student["Status"])}</td>
        </tr>
        """
    if rows == "":
        rows = '<tr><td colspan="5" class="empty">No detections found.</td></tr>'
    return rows


def build_today_timetable_rows():
    """5-column timetable used on the student detail page."""
    rows      = ""
    today_rows = [r for r in timetable if r["day"] == selected_day]
    for row in today_rows:
        is_active = (
            row["period"]     == active_period["period"]
            and row["subject"]    == active_period["subject"]
            and row["start_time"] == active_period["start_time"]
        )
        status      = "Processed" if is_active else "Pending"
        badge_class = "safe" if is_active else "warning"
        rows += f"""
        <tr>
            <td>{row["period"]}</td>
            <td>{row["subject"]}</td>
            <td>{row["teacher"]}</td>
            <td>{row["start_time"]} - {row["end_time"]}</td>
            <td><span class="badge {badge_class}">{status}</span></td>
        </tr>
        """
    if rows == "":
        rows = '<tr><td colspan="5" class="empty">No timetable found for today.</td></tr>'
    return rows


def build_teacher_timetable_rows():
    """8-column timetable (Period | Subject | Course | Assigned Faculty | Start | End | Room | Status)."""
    rows      = ""
    today_rows = [r for r in timetable if r["day"] == selected_day]
    for row in today_rows:
        is_active = (
            row["period"]     == active_period["period"]
            and row["subject"]    == active_period["subject"]
            and row["start_time"] == active_period["start_time"]
        )
        row_class = "active-row" if is_active else ""
        if is_active:
            status_badge = '<span class="badge active-class">🟢 Active Class</span>'
        elif row["subject"].upper() == "LUNCH":
            status_badge = '<span class="badge warning">🍽 Lunch</span>'
        else:
            status_badge = '<span class="badge" style="background:#f1f5f9;color:#475569;">⏳ Pending</span>'

        rows += f"""
        <tr class="{row_class}">
            <td>{row["period"]}</td>
            <td>{row["subject"]}</td>
            <td>{row["course_name"]}</td>
            <td>{row["teacher"]}</td>
            <td>{row["start_time"]}</td>
            <td>{row["end_time"]}</td>
            <td>{row["room"]}</td>
            <td>{status_badge}</td>
        </tr>
        """
    if rows == "":
        rows = '<tr><td colspan="8" class="empty">No timetable found for this day.</td></tr>'
    return rows


def build_subject_attendance_cards(summary):
    subject    = active_period["subject"]
    percentage = summary["attendance_percentage"]
    if percentage >= 75:
        status      = "Safe"
        badge_class = "safe"
    elif percentage >= 65:
        status      = "Warning"
        badge_class = "warning"
    else:
        status      = "Critical"
        badge_class = "absent"
    return f"""
    <div class="bar-row">
        <span>{subject}</span>
        <div class="bar">
            <div class="bar-fill" style="width: {percentage}%;"></div>
        </div>
    </div>
    <p>
        <span class="badge {badge_class}">{status}</span>
        &nbsp; {percentage}% attendance in {subject}
    </p>
    """


def build_recent_activity_rows(student):
    return f"""
    <tr>
        <td>{get_today_date_text()}</td>
        <td>{active_period["subject"]}</td>
        <td>{active_period["period"]}</td>
        <td>{get_status_badge(student["Status"])}</td>
        <td>{student["Best_Similarity"]}</td>
    </tr>
    """

# ============================================================
# REPORT GENERATION FUNCTIONS
# ============================================================

def generate_student_detail_pages(attendance_data, vfiles, main_report_file, summary):
    detail_links = {}
    with open(DETAIL_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    for student in attendance_data:
        roll_no = student["Roll_Number"]

        detected_set = set()
        if student["Detected_In_Videos"] != "-":
            detected_videos_value = student.get("Detected_In_Videos", [])
            if isinstance(detected_videos_value, list):
                detected_set = {
                str(v).strip()
                for v in detected_videos_value
                if str(v).strip()
            }
            else:
                detected_set = {
                    v.strip()
                    for v in str(detected_videos_value).split(",")
                    if v.strip()
                }

        not_detected     = [v for v in vfiles if v not in detected_set]
        not_detected_txt = ", ".join(not_detected) if not_detected else "None"

        detail_file = f"{roll_no}_{safe_filename(active_period['subject'])}_{active_period['period']}.html"
        detail_path = os.path.join(DETAILS_DIR, detail_file)

        html = template
        html = replace_common_class_info(html)

        student_pct    = 100 if student["Status"] == "Present" else 0
        present_cls    = 1   if student["Status"] == "Present" else 0
        absent_cls     = 1   if student["Status"] == "Absent"  else 0
        required_cls   = 0   if student["Status"] == "Present" else 1
        low_subjects   = 0   if student["Status"] == "Present" else 1
        status_lower   = student["Status"].lower()
        status_emoji   = "✅" if student["Status"] == "Present" else "❌"
        status_alert   = "success" if student["Status"] == "Present" else "danger"

        replacements = {
            "{{STUDENT_NAME}}":          roll_no,
            "{{ROLL_NUMBER}}":           roll_no,
            "{{BRANCH}}":                "CSE-AI&ML",
            "{{YEAR}}":                  "2nd Year",
            "{{EMAIL}}":                 f"{roll_no.lower()}@college.edu",
            "{{FACE_STATUS}}":           "Registered",
            "{{STATUS}}":                student["Status"],
            "{{STATUS_LOWER}}":          status_lower,
            "{{STATUS_EMOJI}}":          status_emoji,
            "{{STATUS_ALERT_CLASS}}":    status_alert,
            "{{DETECTION_COUNT}}":       str(student["Detection_Count"]),
            "{{BEST_SIMILARITY}}":       str(student["Best_Similarity"]),
            "{{AVERAGE_SIMILARITY}}":    str(student["Average_Similarity"]),
            "{{DETECTED_IN_VIDEOS}}":    student["Detected_In_Videos"],
            "{{NOT_DETECTED_IN_VIDEOS}}": not_detected_txt,
            "{{REASON}}":                create_reason(student),
            "{{MAIN_REPORT_FILE}}":      main_report_file,
            "{{ATTENDANCE_PERCENTAGE}}": str(student_pct),
            "{{PRESENT_CLASSES}}":       str(present_cls),
            "{{ABSENT_CLASSES}}":        str(absent_cls),
            "{{TOTAL_CLASSES}}":         "1",
            "{{LOW_ATTENDANCE_SUBJECTS}}": str(low_subjects),
            "{{CLASSES_TODAY}}":         str(len([r for r in timetable if r["day"] == selected_day])),
            "{{REQUIRED_CLASSES}}":      str(required_cls),
            "{{AVG_CONFIDENCE}}":        str(summary["avg_confidence"]),
            "{{TODAY_TIMETABLE_ROWS}}":  build_today_timetable_rows(),
            "{{SUBJECT_ATTENDANCE_CARDS}}": build_subject_attendance_cards(summary),
            "{{RECENT_ACTIVITY_ROWS}}":  build_recent_activity_rows(student),
        }
        for key, val in replacements.items():
            html = html.replace(key, str(val))

        with open(detail_path, "w", encoding="utf-8") as f:
            f.write(html)

        detail_links[roll_no] = f"details/{detail_file}"

    return detail_links


def generate_class_report(attendance_data, timestamp):
    subject = active_period["subject"]
    period  = active_period["period"]
    file_name = (
        f"{safe_filename(subject)}_"
        f"{selected_day}_"
        f"{period}_"
        f"{timestamp}.html"
    )
    html_path = os.path.join(WEBSITE_DIR, file_name)
    summary   = calculate_summary(attendance_data)

    detail_links = generate_student_detail_pages(
        attendance_data, video_files, file_name, summary
    )

    with open(ATTENDANCE_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    html = replace_common_class_info(html)

    replacements = {
        "{{CREATED_TIME}}":          datetime.now().strftime("%d-%m-%Y %I:%M:%S %p"),
        "{{TOTAL_STUDENTS}}":        str(summary["total_students"]),
        "{{PRESENT_STUDENTS}}":      str(summary["present_count"]),
        "{{ABSENT_STUDENTS}}":       str(summary["absent_count"]),
        "{{PRESENT_COUNT}}":         str(summary["present_count"]),
        "{{ABSENT_COUNT}}":          str(summary["absent_count"]),
        "{{ATTENDANCE_PERCENTAGE}}": str(summary["attendance_percentage"]),
        "{{TOTAL_CLASSES}}":         "1",
        "{{VIDEOS_PROCESSED}}":      str(summary["videos_processed"]),
        "{{AVG_CONFIDENCE}}":        str(summary["avg_confidence"]),
        "{{TIMETABLE_ROWS}}":        build_teacher_timetable_rows(),
        "{{ATTENDANCE_ROWS}}":       build_attendance_rows(attendance_data, detail_links, include_detail=True),
        "{{ALL_ROWS}}":              build_attendance_rows(attendance_data, detail_links, include_detail=True),
        "{{PRESENT_ROWS}}":          build_attendance_rows(summary["present_students"], detail_links, include_detail=True),
        "{{ABSENT_ROWS}}":           build_attendance_rows(summary["absent_students"],  detail_links, include_detail=True),
        "{{DETECTION_ROWS}}":        build_detection_rows(attendance_data),
    }
    for key, val in replacements.items():
        html = html.replace(key, str(val))

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    return file_name, html_path, summary, detail_links


def generate_teacher_dashboard(class_report_file, timestamp, summary, detail_links, attendance_data):
    file_name = (
        f"teacher_dashboard_"
        f"{selected_day}_"
        f"{active_period['period']}_"
        f"{timestamp}.html"
    )
    html_path = os.path.join(WEBSITE_DIR, file_name)

    with open(TEACHER_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    html = replace_common_class_info(html)

    replacements = {
        "{{CREATED_TIME}}":          datetime.now().strftime("%d-%m-%Y %I:%M:%S %p"),
        "{{CLASS_REPORT_LINK}}":     class_report_file,
        "{{TOTAL_STUDENTS}}":        str(summary["total_students"]),
        "{{PRESENT_STUDENTS}}":      str(summary["present_count"]),
        "{{ABSENT_STUDENTS}}":       str(summary["absent_count"]),
        "{{PRESENT_COUNT}}":         str(summary["present_count"]),
        "{{ABSENT_COUNT}}":          str(summary["absent_count"]),
        "{{ATTENDANCE_PERCENTAGE}}": str(summary["attendance_percentage"]),
        "{{TOTAL_CLASSES}}":         "1",
        "{{VIDEOS_PROCESSED}}":      str(summary["videos_processed"]),
        "{{AVG_CONFIDENCE}}":        str(summary["avg_confidence"]),
        "{{TIMETABLE_ROWS}}":        build_teacher_timetable_rows(),
        "{{ATTENDANCE_ROWS}}":       build_teacher_attendance_rows(attendance_data, detail_links),
        "{{DETECTION_ROWS}}":        build_detection_rows(attendance_data),
    }
    for key, val in replacements.items():
        html = html.replace(key, str(val))

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    return html_path

# ============================================================
# MAIN CALLABLE FUNCTION
# Called by both Flask (app.py) and the CLI __main__ block.
# ============================================================

def run_attendance(
    day=None,
    period=None,
    time_value=None,
    selected_videos=None,
    show_video=False,
    generate_html=False,
    max_frames=None,
):
    """
    Process CCTV attendance for a given class period.

    Args:
        day             : Day name, e.g. "Monday"  (optional — uses today if omitted)
        period          : Period code, e.g. "P2"   (takes priority over time_value)
        time_value      : Time string "HH:MM"      (fallback when period not given)
        selected_videos : Optional list of video file names to process
        show_video      : Open cv2 display window   (False when called from Flask)
        generate_html   : Generate legacy HTML reports (CLI/admin only)
        max_frames      : Stop after this many processed frames (smoke test mode)

    Returns:
        dict with keys:
            day, period, subject, course_name, teacher,
            start_time, end_time, room, selected_videos,
            total_students, present_count, absent_count,
            attendance_percentage, students
    """
    global timetable, selected_day, selected_time, active_period, demo_mode
    global detector, recognizer, student_embeddings, all_students, video_files

    # ── Validate required files ──────────────────────────
    required = [YUNET_MODEL, SFACE_MODEL, EMBEDDINGS_FILE, TIMETABLE_PATH]
    for f in required:
        if not os.path.exists(f):
            raise FileNotFoundError(f"Missing required file: {f}")

    # ── Load timetable ───────────────────────────────────
    timetable = load_timetable()

    # ── Resolve day / active period ──────────────────────
    if day and period:
        selected_day  = normalize_day(day)
        demo_mode     = True
        active_period = None
        for row in timetable:
            if row["day"] == selected_day and row["period"].upper() == period.upper():
                active_period = row
                break
        if active_period is None:
            raise ValueError(f"Period '{period}' not found for {selected_day} in the timetable.")
        selected_time = parse_time(active_period["start_time"])

    elif day and time_value:
        selected_day  = normalize_day(day)
        selected_time = parse_time(time_value)
        demo_mode     = True
        active_period = find_active_period(timetable, selected_day, selected_time)
        if active_period is None:
            raise ValueError(f"No active class found for {selected_day} at {time_value}.")

    else:
        now           = datetime.now()
        selected_day  = now.strftime("%A")
        selected_time = now.time().replace(second=0, microsecond=0)
        demo_mode     = False
        active_period = find_active_period(timetable, selected_day, selected_time)
        if active_period is None:
            raise ValueError("No active class found for the current day and time.")

    print("\n=== Attendance Run Started ===")
    print(f"Day: {selected_day}")
    print(f"Period: {active_period['period'] if day and period else '(resolved from time)'}")
    print("Time:", selected_time.strftime("%H:%M"))
    print("Mode:", "Demo/Test Mode" if demo_mode else "Real Current Time Mode")
    if max_frames is not None:
        print(f"Smoke test mode: max_frames={max_frames}")

    if active_period["subject"].upper() == "LUNCH":
        raise ValueError("Lunch time detected. Attendance not marked.")

    print("\nActive Class Found")
    print("Subject:", active_period["subject"])
    print("Course:",  active_period["course_name"])
    print("Assigned Faculty:", active_period["teacher"])
    print("Period:",  active_period["period"])
    print("Time:",    active_period["start_time"], "-", active_period["end_time"])
    print("Room:",    active_period["room"])

    # ── Load AI models ───────────────────────────────────
    detector   = cv2.FaceDetectorYN_create(YUNET_MODEL, "", (320, 320), 0.6, 0.3, 5000)
    recognizer = cv2.FaceRecognizerSF_create(SFACE_MODEL, "")

    with open(EMBEDDINGS_FILE, "rb") as f:
        student_embeddings = pickle.load(f)

    all_students = sorted(student_embeddings.keys())
    print(f"\nTotal students loaded: {len(all_students)}")

    # ── Discover video files ─────────────────────────────
    video_files = [
        f for f in sorted(os.listdir(VIDEO_DIR))
        if f.lower().endswith((".mp4", ".avi", ".mov", ".mkv"))
    ]
    if not video_files:
        raise FileNotFoundError("No videos found in cctv_videos folder.")

    if selected_videos:
        requested = set(selected_videos)
        selected = [v for v in video_files if v in requested]
        if not selected:
            raise ValueError("Selected videos were not found in cctv_videos folder.")
        video_files = selected

    print(f"\nSelected videos ({len(video_files)}): {', '.join(video_files)}")

    # ── Per-student accumulation storage ─────────────────
    detection_count   = defaultdict(int)
    similarity_sum    = defaultdict(float)
    best_sim_map      = defaultdict(float)
    detected_videos   = defaultdict(set)

    # ── Process each video ───────────────────────────────
    processed_frames = 0
    stop_processing = False

    for video_name in video_files:
        if stop_processing:
            break

        video_path = os.path.join(VIDEO_DIR, video_name)
        cap        = cv2.VideoCapture(video_path)

        print(f"\nCurrent video: {video_name}")

        frame_count = 0
        while True:
            success, frame = cap.read()
            if not success:
                break

            frame_count += 1
            if frame_count % FRAME_SKIP != 0:
                continue

            processed_frames += 1
            if processed_frames % 100 == 0:
                print(f"  Frame progress: {processed_frames} processed frames")

            if max_frames is not None and processed_frames >= max_frames:
                print(f"  Reached max_frames limit ({max_frames}), stopping.")
                stop_processing = True
                break

            faces = detect_faces(frame)

            for face in faces:
                query_embedding = create_embedding(frame, face)
                if query_embedding is None:
                    continue

                roll_no, score = match_face(query_embedding)

                if roll_no != "Unknown":
                    detection_count[roll_no]  += 1
                    similarity_sum[roll_no]   += score
                    best_sim_map[roll_no]      = max(best_sim_map[roll_no], score)
                    detected_videos[roll_no].add(video_name)

            if show_video:
                display_frame = frame.copy()
                for face in faces:
                    x, y, w, h = face[:4].astype(int)
                    x1 = max(0, x);            y1 = max(0, y)
                    x2 = min(frame.shape[1], x + w); y2 = min(frame.shape[0], y + h)

                    query_embedding = create_embedding(frame, face)
                    if query_embedding is None:
                        continue

                    roll_no, score = match_face(query_embedding)
                    if roll_no != "Unknown":
                        color = (0, 255, 0)
                        text  = f"{roll_no} {score:.2f}"
                    else:
                        color = (0, 0, 255)
                        text  = f"Unknown {score:.2f}"

                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(display_frame, text, (x1, y1 - 8),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

                cur_present = sum(
                    1 for r in all_students
                    if detection_count[r] >= MIN_DETECTIONS_FOR_PRESENT
                )
                cv2.putText(display_frame,
                            f"{active_period['subject']} | {active_period['period']}",
                            (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
                cv2.putText(display_frame,
                            f"Present: {cur_present} / {len(all_students)}",
                            (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
                cv2.putText(display_frame, "Press q to stop",
                            (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
                cv2.imshow("Timetable-Based Attendance", display_frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    stop_processing = True
                    break

        cap.release()

    if show_video:
        cv2.destroyAllWindows()

    # ── Build final attendance data ───────────────────────
    attendance_data = []
    for roll_no in all_students:
        count = detection_count[roll_no]
        if count > 0:
            avg_similarity = round(similarity_sum[roll_no] / count, 3)
            best_sim       = round(best_sim_map[roll_no], 3)
            videos         = sorted(detected_videos[roll_no])
        else:
            avg_similarity = 0.0
            best_sim       = 0.0
            videos         = []

        status = "Present" if count >= MIN_DETECTIONS_FOR_PRESENT else "Absent"
        attendance_data.append({
            "Roll_Number":       roll_no,
            "Status":            status,
            "Detection_Count":   count,
            "Best_Similarity":   best_sim,
            "Average_Similarity": avg_similarity,
            "Detected_In_Videos": videos,
        })

    summary = calculate_summary(attendance_data)

    students = [
        {
            "roll_number": student["Roll_Number"],
            "status": student["Status"],
            "detection_count": student["Detection_Count"],
            "best_similarity": student["Best_Similarity"],
            "average_similarity": student["Average_Similarity"],
            "detected_in_videos": student["Detected_In_Videos"],
        }
        for student in attendance_data
    ]

    completed_at = datetime.now().isoformat()

    print("\n=== Attendance Summary ===")
    print("Subject:", active_period["subject"])
    print("Assigned Faculty:", active_period["teacher"])
    print(f"Present: {summary['present_count']} / {summary['total_students']}")
    print(f"Absent: {summary['absent_count']}")
    print(f"Attendance: {summary['attendance_percentage']}%")
    print(f"Frames processed: {processed_frames}")
    print(f"Videos processed: {len(video_files)}")

    result = {
        "day": selected_day,
        "period": active_period["period"],
        "subject": active_period["subject"],
        "course_name": active_period.get("course_name", "-"),
        "assigned_faculty": active_period.get("teacher", "-"),
        "start_time": active_period.get("start_time", ""),
        "end_time": active_period.get("end_time", ""),
        "room": active_period.get("room", "-"),
        "selected_videos": list(video_files),
        "total_students": summary["total_students"],
        "present_count": summary["present_count"],
        "absent_count": summary["absent_count"],
        "attendance_percentage": summary["attendance_percentage"],
        "avg_confidence": summary.get("avg_confidence", 0),
        "videos_processed": len(video_files),
        "frames_processed": processed_frames,
        "students": students,
        "completed_at": completed_at,
    }

    # Optionally generate legacy HTML reports (admin/CLI use only)
    if generate_html:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        class_report_file, class_report_path, gen_summary, detail_links = generate_class_report(
            attendance_data, ts
        )
        teacher_dashboard_path = generate_teacher_dashboard(
            class_report_file, ts, gen_summary, detail_links, attendance_data
        )
        teacher_dashboard_file = os.path.basename(teacher_dashboard_path)
        result.update({
            "class_report_file": class_report_file,
            "class_report_path": class_report_path,
            "teacher_dashboard_file": teacher_dashboard_file,
            "teacher_dashboard_path": teacher_dashboard_path,
        })

    return result

# ============================================================
# REPORT BANNER INJECTION & REPORT REGENERATION
# (Called from app.py — no face recognition involved)
# ============================================================

def inject_report_banner(html_path: str, report_type: str) -> None:
    """
    Post-process a generated HTML file to add a sticky colored banner at the top
    indicating its type (Admin Edited, Reprocessed).
    Safe to call with report_type=None or 'AI' — does nothing in those cases.
    """
    if not report_type or report_type == "AI":
        return

    BANNERS = {
        "Admin Edited": (
            '<div style="background:linear-gradient(90deg,#b45309,#d97706);'
            'color:white;padding:11px 24px;text-align:center;font-weight:700;'
            'font-size:13px;letter-spacing:.4px;position:sticky;top:0;z-index:9999;">'
            '&#9998;&nbsp; Admin Edited Report &nbsp;&mdash;&nbsp; '
            'Manual corrections applied by Main&nbsp;Admin'
            '</div>'
        ),
        "Reprocessed": (
            '<div style="background:linear-gradient(90deg,#0b2d5e,#1a6fd4);'
            'color:white;padding:11px 24px;text-align:center;font-weight:700;'
            'font-size:13px;letter-spacing:.4px;position:sticky;top:0;z-index:9999;">'
            '&#128260;&nbsp; Reprocessed Report &nbsp;&mdash;&nbsp; Fresh AI face-recognition result'
            '</div>'
        ),
    }

    banner = BANNERS.get(report_type)
    if not banner or not os.path.exists(html_path):
        return

    try:
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()
        html = html.replace("<body>", f"<body>\n{banner}", 1)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
    except Exception as exc:
        print(f"[inject_report_banner] Could not inject banner into {html_path}: {exc}")


def regenerate_reports(
    day: str,
    period: str,
    attendance_data: list,
    video_files_list: list,
    label: str = None,
) -> dict:
    """
    Regenerate HTML attendance reports from existing attendance_data.
    Does NOT re-run face recognition — only rebuilds HTML output.

    Args:
        day:              Day name, e.g. 'Monday'
        period:           Period code, e.g. 'P2'
        attendance_data:  Student dicts with manual overrides already applied
        video_files_list: Original video filenames (for stats display)
        label:            Optional filename suffix: 'EDITED', 'REPROCESSED', etc.

    Returns:
        dict with class_report_file, class_report_path,
              teacher_dashboard_path, teacher_dashboard_file, summary
    """
    global timetable, selected_day, selected_time, active_period, demo_mode, video_files

    timetable    = load_timetable()
    selected_day = normalize_day(day)
    demo_mode    = True
    video_files  = list(video_files_list) if video_files_list else []

    active_period = None
    for row in timetable:
        if row["day"] == selected_day and row["period"].upper() == period.upper():
            active_period = row
            break
    if active_period is None:
        raise ValueError(f"Period '{period}' not found for {selected_day} in the timetable.")

    selected_time = parse_time(active_period["start_time"])

    # Build timestamp with optional label suffix for clear filename identification
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    if label:
        ts = f"{ts}_{label.upper()}"

    class_report_file, class_report_path, summary, detail_links = generate_class_report(
        attendance_data, ts
    )
    teacher_dashboard_path = generate_teacher_dashboard(
        class_report_file, ts, summary, detail_links, attendance_data
    )
    teacher_dashboard_file = os.path.basename(teacher_dashboard_path)

    # Inject colored type banner into both generated HTML files
    if label:
        banner_type = (
            "Admin Edited" if "EDITED" in label.upper()
            else label.replace("_", " ").title()
        )
        inject_report_banner(class_report_path, banner_type)
        inject_report_banner(teacher_dashboard_path, banner_type)

    print(f"\nReport regenerated ({label or 'AI'}):")
    print(f"  Class report:      {class_report_path}")
    print(f"  Admin dashboard: {teacher_dashboard_path}")

    return {
        "class_report_file":       class_report_file,
        "class_report_path":       class_report_path,
        "teacher_dashboard_path":  teacher_dashboard_path,
        "teacher_dashboard_file":  teacher_dashboard_file,
        "summary":                 summary,
    }


# ============================================================
# CLI ENTRY POINT  (keeps old commands working + adds --period)
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sreenidhi University Smart Attendance System")
    parser.add_argument("--day",    help="Day name, e.g. Monday")
    parser.add_argument("--time",   help="Time in HH:MM format, e.g. 09:20")
    parser.add_argument("--period", help="Period code, e.g. P2  (overrides --time)")
    cli_args = parser.parse_args()

    try:
        result = run_attendance(
            day=cli_args.day,
            period=cli_args.period,
            time_value=cli_args.time,
            show_video=True,           # Show window when run from CLI
            generate_html=True,        # CLI invokes legacy HTML generation for convenience
        )
        if result.get("teacher_dashboard_path"):
            print("\nOpen admin dashboard:")
            print(f"start {result['teacher_dashboard_path']}")
        else:
            print("\nAttendance run completed (no HTML generated).")

    except (ValueError, FileNotFoundError) as err:
        print(f"\nError: {err}")
        sys.exit(1)