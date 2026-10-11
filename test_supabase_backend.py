"""
Comprehensive Automated Test Suite for Social Shield Supabase Migration
Tests Authentication, Authorization (RLS logic), Detection Pipeline, Storage, and Synchronization.
"""
import os
import sys
import unittest
import json
import uuid
import tempfile
import numpy as np
from PIL import Image

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from fastapi.testclient import TestClient
from main import app
from utils.database import init_db, get_supabase_client, is_mock_db
from utils.huggingface import validate_image_bytes, run_local_spectral_analysis
from utils.storage import validate_file


class TestSocialShieldSupabaseSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.user_a_token = "dev_user_alpha_uuid_1111"
        cls.user_b_token = "dev_user_beta_uuid_2222"
        cls.user_a_id = "user_alpha_uuid_1111"
        cls.user_b_id = "user_beta_uuid_2222"

    def setUp(self):
        # Reset tables in mock database
        db = get_supabase_client()
        if hasattr(db, "tables"):
            db.tables.clear()

    # ====================================================================
    # 1. AUTHENTICATION & HEALTH TESTS
    # ====================================================================

    def test_health_check_reports_supabase(self):
        """Verify /health reports supabase auth, postgresql, and huggingface model"""
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["auth_provider"], "supabase")
        self.assertIn("supabase", data["database_type"])
        self.assertEqual(data["deepfake_model"], "prithivMLmods/deepfake-detector-model-v1")

    def test_unauthenticated_request_rejected(self):
        """Verify protected routes strictly reject unauthenticated calls"""
        res = self.client.get("/api/v1/history")
        self.assertIn(res.status_code, [401, 403])  # Unauthenticated Bearer rejected

    def test_authenticated_profile_and_stats_retrieval(self):
        """Verify user stats can be retrieved with valid Bearer token"""
        headers = {"Authorization": f"Bearer {self.user_a_token}"}
        res = self.client.get("/api/v1/stats", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["totalScans"], 0)
        self.assertEqual(data["trustScore"], 100)

    # ====================================================================
    # 2. DETECTION PIPELINE & FILE VALIDATION TESTS
    # ====================================================================

    def test_invalid_image_upload_rejected(self):
        """Verify corrupted or invalid files are rejected with 400 Bad Request"""
        headers = {"Authorization": f"Bearer {self.user_a_token}"}
        # Send fake text file pretending to be image
        files = {"file": ("corrupt.jpg", b"This is not a real image binary file.", "image/jpeg")}
        res = self.client.post("/api/v1/scan/image", files=files, headers=headers)
        self.assertEqual(res.status_code, 400)
        self.assertTrue(any(msg in res.json()["detail"] for msg in ["Malformed", "corrupted", "too small"]))

    def test_valid_image_detection_persists_to_supabase(self):
        """Verify valid image upload runs inference and stores record in Supabase"""
        headers = {"Authorization": f"Bearer {self.user_a_token}"}
        
        # Create a valid in-memory test JPEG image
        img = Image.new("RGB", (200, 200), color=(73, 109, 137))
        img_bytes_io = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        img.save(img_bytes_io.name, format="JPEG")
        img_bytes_io.close()

        with open(img_bytes_io.name, "rb") as f:
            file_bytes = f.read()

        try:
            files = {"file": ("test_capture.jpg", file_bytes, "image/jpeg")}
            res = self.client.post("/api/v1/scan/image", files=files, headers=headers)
            self.assertEqual(res.status_code, 200)
            data = res.json()
            
            # Assert schema contracts
            self.assertIn("scan_id", data)
            self.assertIn("verdict", data)
            self.assertIn(data["verdict"], ["SAFE", "REAL", "SUSPICIOUS", "FAKE"])
            self.assertIn("confidence", data)
            self.assertIn("fake_probability", data)
            self.assertIn("real_probability", data)
            self.assertEqual(data["media_type"], "IMAGE")
            self.assertIn("recommendations", data)
            self.assertIn("storage_path", data)
            
            # Verify record exists in Supabase
            db = get_supabase_client()
            scans_res = db.table("scans").select("*").eq("id", data["scan_id"]).execute()
            self.assertEqual(len(scans_res.data), 1)
            self.assertEqual(scans_res.data[0]["user_id"], self.user_a_id)

        finally:
            if os.path.exists(img_bytes_io.name):
                os.remove(img_bytes_io.name)

    def test_text_fraud_scan_persists_and_updates_stats(self):
        """Verify text scam detection saves to database and recalculates user stats"""
        headers = {"Authorization": f"Bearer {self.user_a_token}"}
        payload = {"text": "URGENT: Your account has been suspended! Verify your OTP password immediately to avoid legal action."}
        res = self.client.post("/api/v1/scan/text", json=payload, headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["verdict"], "FAKE")
        self.assertEqual(data["risk_level"], "HIGH")

        # Verify stats updated
        stats_res = self.client.get("/api/v1/stats", headers=headers)
        self.assertEqual(stats_res.status_code, 200)
        stats = stats_res.json()
        self.assertGreaterEqual(stats["totalScans"], 1)
        self.assertGreaterEqual(stats["fakeDetected"], 1)

    # ====================================================================
    # 3. AUTHORIZATION & TENANT ISOLATION TESTS
    # ====================================================================

    def test_user_cannot_access_or_delete_other_user_records(self):
        """Verify strict isolation: User B cannot access or delete User A's scans"""
        headers_a = {"Authorization": f"Bearer {self.user_a_token}"}
        headers_b = {"Authorization": f"Bearer {self.user_b_token}"}

        # User A creates a scan
        payload = {"url": "https://suspicious-verify-paypal-login.xyz"}
        res_a = self.client.post("/api/v1/scan/url", json=payload, headers=headers_a)
        self.assertEqual(res_a.status_code, 200)
        scan_id = res_a.json()["scan_id"]

        # User A can view scan
        detail_a = self.client.get(f"/api/v1/history/{scan_id}", headers=headers_a)
        self.assertEqual(detail_a.status_code, 200)

        # User B CANNOT view scan (Returns 404 Not Found)
        detail_b = self.client.get(f"/api/v1/history/{scan_id}", headers=headers_b)
        self.assertEqual(detail_b.status_code, 404)

        # User B CANNOT delete scan (Returns 404 Not Found)
        delete_b = self.client.delete(f"/api/v1/history/{scan_id}", headers=headers_b)
        self.assertEqual(delete_b.status_code, 404)

        # User A's scan remains intact
        check_a = self.client.get(f"/api/v1/history/{scan_id}", headers=headers_a)
        self.assertEqual(check_a.status_code, 200)

        # User A can successfully delete their own scan
        delete_a = self.client.delete(f"/api/v1/history/{scan_id}", headers=headers_a)
        self.assertEqual(delete_a.status_code, 200)

    # ====================================================================
    # 4. SYNCHRONIZATION DATA-FLOW TESTS
    # ====================================================================

    def test_bidirectional_history_and_deletion_synchronization(self):
        """Simulates Android creating a scan and Web viewing/deleting it with the same account"""
        headers = {"Authorization": f"Bearer {self.user_a_token}"}

        # 1. Android submits scan
        profile_payload = {
            "username": "suspicious_bot_99",
            "following": 5000,
            "followers": 12,
            "account_age_days": 5,
            "post_count": 300
        }
        create_res = self.client.post("/api/v1/scan/profile", json=profile_payload, headers=headers)
        self.assertEqual(create_res.status_code, 200)
        scan_id = create_res.json()["scan_id"]

        # 2. Web queries history list -> record appears immediately
        history_res = self.client.get("/api/v1/history", headers=headers)
        self.assertEqual(history_res.status_code, 200)
        items = history_res.json()["items"]
        matching_scan = next((s for s in items if s["id"] == scan_id or s["scanId"] == scan_id), None)
        self.assertIsNotNone(matching_scan)
        self.assertEqual(matching_scan["mediaType"], "PROFILE")

        # 3. Web deletes scan -> Android view refreshes
        del_res = self.client.delete(f"/api/v1/history/{scan_id}", headers=headers)
        self.assertEqual(del_res.status_code, 200)

        # Verify scan no longer present in history
        history_after = self.client.get("/api/v1/history", headers=headers)
        remaining_ids = [s["id"] for s in history_after.json()["items"]]
        self.assertNotIn(scan_id, remaining_ids)


if __name__ == "__main__":
    unittest.main()
