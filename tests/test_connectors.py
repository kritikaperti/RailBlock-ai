"""
Test Suite for Real-Life Indian Railways Database Connectors & SQL Query Engine
"""

import sys
import os
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from backend.main import app
from backend.db_connector import DB_MANAGER
from backend.live_api_connectors import CONNECTORS_HUB


class TestDatabaseConnectors(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_db_status(self):
        res = self.client.get("/api/db/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "CONNECTED")
        self.assertGreaterEqual(data["total_tables"], 6)

    def test_db_tables_schema(self):
        res = self.client.get("/api/db/tables")
        self.assertEqual(res.status_code, 200)
        tables = res.json()
        table_names = [t["table_name"] for t in tables]
        self.assertIn("tms_track_defects", table_names)
        self.assertIn("smms_signal_telemetry", table_names)
        self.assertIn("tdms_traction_hotspots", table_names)
        self.assertIn("coa_live_trains", table_names)

    def test_sql_query_execution(self):
        # Query TMS Defects
        payload = {"sql_query": "SELECT * FROM tms_track_defects WHERE severity = 'EMERGENCY'", "limit": 10}
        res = self.client.post("/api/db/query", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "SUCCESS")
        self.assertIn("columns", data)
        self.assertGreaterEqual(len(data["data"]), 1)

    def test_cris_connectors_status(self):
        res = self.client.get("/api/connectors/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("TMS", data["cris_systems"])
        self.assertIn("SMMS", data["cris_systems"])
        self.assertEqual(data["railnet_gateway_status"], "ONLINE")

    def test_cris_live_sync(self):
        res = self.client.post("/api/connectors/cris/sync", json={"system_name": "TMS"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "SUCCESS")
        self.assertGreaterEqual(data["records_synced"], 1)

    def test_data_gov_live_sync(self):
        res = self.client.post("/api/connectors/data-gov/sync", json={"api_key": "TEST_KEY_123"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "SUCCESS")


if __name__ == "__main__":
    unittest.main()
