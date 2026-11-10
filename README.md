# Sreenidhi University Smart Attendance System 🎓📸

An automated smart attendance management system that uses CCTV footage, deep learning facial detection (**YuNet**) and facial recognition (**SFace**), combined with class timetable scheduling and an interactive modern web dashboard (**React + Flask**).

---

## 🌟 Key Features

- **Automated Face Recognition**: Real-time face detection using OpenCV's YuNet ONNX model and 128D face feature extraction via SFace ONNX model.
- **Timetable-Aware Attendance**: Automatically maps CCTV video processing to class periods and rooms based on `timetable/class_timetable.csv`.
- **Modern Web Dashboard**: Interactive UI built with React 19 and Vite, served seamlessly by the Flask backend.
- **Live Attendance Status & Manual Edits**: Real-time statistics (total students, present, absent, recognition rate) with teacher manual override capability.
- **Multi-Format Reports**: Automatic export to CSV and Excel (`.xlsx`) in the `exports/` folder.
- **Evidence & Audit Trail**: Generates student detail pages and detection evidence snapshots for full transparency.

---

## 📁 Project Structure

```text
Class_Attendance_Project/
├── app.py                      # Main Flask application and API server
├── api_server.py               # Lightweight secondary API server
├── requirements.txt            # Python dependencies
├── package.json                # Root package configuration (frontend script forwarding)
├── .gitignore                  # Git ignore rules for venvs, node_modules, weights, etc.
│
├── models/                     # Deep learning models & labels
│   ├── face_detection_yunet_2023mar.onnx
│   ├── face_recognition_sface_2021dec.onnx
│   ├── sface_embeddings.pkl
│   ├── trainer.yml
│   └── labels.txt
│
├── my-react-website/           # React + Vite frontend source code
│   ├── src/                    # Components and pages
│   ├── public/                 # Static assets
│   ├── dist/                   # Production build (served by Flask)
│   └── package.json            # Frontend npm dependencies
│
├── scripts/                    # Automation and utility scripts
│   ├── crop_dataset_faces.py   # Crop student faces from raw images
│   ├── create_sface_embeddings.py # Generate SFace embeddings
│   ├── augment_dataset.py      # Face dataset augmentation tool
│   ├── timetable_attendance.py # Core attendance recognition engine
│   ├── mark_attendance.py      # CLI attendance runner
│   ├── run_smoke_test.py       # API smoke test
│   └── verify_all.py           # Comprehensive system test suite
│
├── templates/                  # Jinja2 HTML templates for reports
│   ├── attendance_template.html
│   ├── student_detail_template.html
│   └── teacher_dashboard_template.html
│
├── timetable/                  # Timetable configuration
│   └── class_timetable.csv     # Daily schedule (periods, subjects, rooms)
│
├── cctv_videos/                # Input CCTV video footage (.mp4, .avi)
├── dataset/                    # Raw student image dataset
├── cropped_dataset/            # Cropped student face dataset
├── data/                       # Attendance runs, logs, and manual overrides
├── exports/                    # Generated CSV and Excel attendance reports
└── runtime/                    # Evidence images and checkpoint frames
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.10+** (Tested on Python 3.14)
- **Node.js 18+** & npm

### 2. Python Setup
Create and activate a virtual environment, then install dependencies:
```bash
python -m venv .venv

# On Windows:
.venv\Scripts\activate

# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Frontend Setup
Build the React web interface:
```bash
# From project root:
npm run build

# Or directly in my-react-website:
cd my-react-website
npm install
npm run build
cd ..
```

---

## 🖥️ Running the Application

Start the unified Flask server:
```bash
python app.py
```
Open your browser at:
`http://127.0.0.1:5000`

---

## 🧪 Testing & Verification

Run the comprehensive project verification script:
```bash
python scripts/verify_all.py
```

Run the API smoke tests:
```bash
python scripts/run_smoke_test.py
```

---

## 📄 License
Private and Academic Project - Sreenidhi Institute of Science and Technology.
