import unittest
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import app


class TestAPIEndpoints(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_health_check(self):
        """Test the health check endpoint returns 200 and success."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("Smart Attendance", data.get("title", ""))

    def test_current_context(self):
        """Test current day and period context."""
        response = self.client.get("/api/current-context")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("current_day", data)
        self.assertIn("current_time", data)

    def test_dashboard_metrics(self):
        """Test dashboard endpoint returns student metrics."""
        response = self.client.get("/api/dashboard")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("total_students", data)
        self.assertIn("present", data)
        self.assertIn("absent", data)
        self.assertIn("recognition_rate", data)

    def test_reports_listing(self):
        """Test reports endpoint lists generated reports."""
        response = self.client.get("/api/reports")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)

    def test_videos_endpoint(self):
        """Test videos list endpoint."""
        response = self.client.get("/api/videos")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)

    def test_jobs_endpoint(self):
        """Test jobs list endpoint."""
        response = self.client.get("/api/jobs")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)

    def test_react_index_served(self):
        """Test root / serves React index page."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"html", response.data.lower())


if __name__ == "__main__":
    unittest.main()
