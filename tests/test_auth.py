"""
Authentication & RBAC Test Suite for RailBlock AI
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


class TestAuthentication(unittest.TestCase):

    def test_successful_officer_logins(self):
        """Test valid logins for Operating, Engineering, S&T, TRD, and DRM"""
        roles = [
            ("operating", "rail123", "Rajesh Sharma", "OPERATING"),
            ("engineering", "rail123", "Amit Verma", "ENGINEERING"),
            ("signalling", "rail123", "Sunil Gupta", "SNT"),
            ("traction", "rail123", "Pooja Singh", "TRD"),
            ("admin", "admin123", "Vikas Meena, IRTS", "EXECUTIVE"),
        ]

        for username, password, expected_name, expected_role in roles:
            res = client.post("/api/auth/login", json={"username": username, "password": password})
            self.assertEqual(res.status_code, 200, f"Login failed for {username}")
            data = res.json()
            self.assertEqual(data["status"], "SUCCESS")
            self.assertTrue(data["token"].startswith("ir-token-"))
            self.assertEqual(data["name"], expected_name)
            self.assertEqual(data["role"], expected_role)

    def test_invalid_login(self):
        """Test rejection of incorrect credentials"""
        res = client.post("/api/auth/login", json={"username": "operating", "password": "wrongpassword"})
        self.assertEqual(res.status_code, 401)

        res2 = client.post("/api/auth/login", json={"username": "unknown_user", "password": "rail123"})
        self.assertEqual(res2.status_code, 401)

    def test_session_validation_and_logout(self):
        """Test /api/auth/me and /api/auth/logout lifecycle"""
        # 1. Login
        login_res = client.post("/api/auth/login", json={"username": "operating", "password": "rail123"})
        token = login_res.json()["token"]

        # 2. Verify /api/auth/me
        me_res = client.get(f"/api/auth/me?token={token}")
        self.assertEqual(me_res.status_code, 200)
        self.assertTrue(me_res.json()["authenticated"])
        self.assertEqual(me_res.json()["user"]["username"], "operating")

        # 3. Logout
        logout_res = client.post("/api/auth/logout", json={"token": token})
        self.assertEqual(logout_res.status_code, 200)

        # 4. Verify token is now invalid
        me_after = client.get(f"/api/auth/me?token={token}")
        self.assertEqual(me_after.status_code, 401)

    def test_officials_list(self):
        """Test listing of demo official accounts"""
        res = client.get("/api/auth/officials")
        self.assertEqual(res.status_code, 200)
        officials = res.json()
        self.assertGreaterEqual(len(officials), 5)


if __name__ == "__main__":
    unittest.main()
