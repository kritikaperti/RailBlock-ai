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

    def test_user_registration(self):
        """Test registering a new officer user"""
        reg_payload = {
            "name": "Kritika Perti",
            "username": "kperti_test",
            "password": "securepass123",
            "email": "kperti@railnet.gov.in",
            "department": "ENGINEERING",
            "designation": "Sr. Divisional Engineer / Track",
            "division": "Prayagraj (PRYJ)",
            "zone": "North Central Railway (NCR)"
        }
        res = client.post("/api/auth/register", json=reg_payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "SUCCESS")
        self.assertTrue(data["token"].startswith("ir-token-"))
        self.assertEqual(data["username"], "kperti_test")
        self.assertEqual(data["name"], "Kritika Perti")

        # Duplicate username should be rejected
        res_dup = client.post("/api/auth/register", json=reg_payload)
        self.assertEqual(res_dup.status_code, 400)

        # Verify listed in /api/auth/users
        res_users = client.get("/api/auth/users")
        self.assertEqual(res_users.status_code, 200)
        usernames = [u["username"] for u in res_users.json()]
        self.assertIn("kperti_test", usernames)

    def test_passenger_login_and_profile(self):
        """Test logging in with default passenger account without department requirement"""
        res = client.post("/api/auth/login", json={"username": "passenger", "password": "pass123"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "SUCCESS")
        self.assertEqual(data["user_type"], "PASSENGER")
        self.assertEqual(data["name"], "Rahul Mehra")
        self.assertIsNone(data.get("department"))

    def test_passenger_registration(self):
        """Test passenger account creation without department or designation"""
        reg_payload = {
            "name": "Simran Kaur",
            "username": "simran_traveler",
            "password": "passUser789",
            "email": "simran@gmail.com",
            "user_type": "PASSENGER",
            "department": None,
            "designation": None,
            "division": "Northern Railway",
            "zone": "NR"
        }
        res = client.post("/api/auth/register", json=reg_payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "SUCCESS")
        self.assertEqual(data["user_type"], "PASSENGER")
        self.assertEqual(data["name"], "Simran Kaur")
        self.assertIsNone(data.get("department"))
        self.assertEqual(data.get("designation"), "Train Passenger")


if __name__ == "__main__":
    unittest.main()
