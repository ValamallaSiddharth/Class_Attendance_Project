# Contributing to Smart Attendance System

Thank you for your interest in contributing to the **Smart Attendance System**! We welcome contributions to enhance facial recognition accuracy, UI features, performance, and documentation.

---

## 🛠️ How to Contribute

### 1. Reporting Bugs
- Search existing issues to ensure the bug hasn't been reported.
- Open an issue using the **Bug Report** template with clear reproduction steps, logs, and system environment info.

### 2. Suggesting Enhancements
- Open an issue using the **Feature Request** template describing the proposed functionality and motivation.

### 3. Pull Requests
1. **Fork** the repository and clone your fork locally.
2. Create a new branch: `git checkout -b feature/your-feature-name`.
3. Make your changes:
   - Ensure clean code formatting.
   - Run tests: `python -m unittest discover -s tests`.
   - Run verification: `python scripts/verify_all.py`.
4. Commit your changes with clear semantic messages (`feat: ...`, `fix: ...`, `docs: ...`).
5. Push to your fork: `git push origin feature/your-feature-name`.
6. Open a **Pull Request** against the `main` branch.

---

## 🧪 Testing Standards
- All Python changes must pass `python scripts/verify_all.py` and `python -m unittest discover -s tests`.
- All frontend changes must build cleanly via `npm run build` with zero errors.
