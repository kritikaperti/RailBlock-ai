"""
Unit Test Suite for RailBlock AI Route Terrain, Rivers & Jungles API
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from fastapi.testclient import TestClient
from backend.main import app
from backend.data_generator import get_corridor_terrain_features

client = TestClient(app)


class TestTerrainAndGeography(unittest.TestCase):

    def test_terrain_generator_features(self):
        """Verify rivers, jungles, and stations generated for Grand Chord corridor"""
        data = get_corridor_terrain_features("CORRIDOR_GRAND_CHORD")
        self.assertIn("rivers", data)
        self.assertIn("jungles", data)
        self.assertIn("stations", data)
        
        # Check river crossings
        rivers = data["rivers"]
        self.assertGreaterEqual(len(rivers), 5)
        river_names = [r["name"] for r in rivers]
        self.assertTrue(any("Yamuna River" in n for n in river_names))
        self.assertTrue(any("Ganga River" in n for n in river_names))

        # Check jungle / forest reserves
        jungles = data["jungles"]
        self.assertGreaterEqual(len(jungles), 3)
        jungle_names = [j["name"] for j in jungles]
        self.assertTrue(any("Hastinapur" in n or "Keetham" in n or "Vindhyachal" in n for n in jungle_names))

    def test_terrain_api_endpoint(self):
        """Verify GET /api/network/terrain endpoint output"""
        res = client.get("/api/network/terrain?corridor_id=CORRIDOR_GRAND_CHORD")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["corridor_id"], "CORRIDOR_GRAND_CHORD")
        self.assertIn("terrain", data)
        terrain = data["terrain"]
        self.assertIn("rivers", terrain)
        self.assertIn("jungles", terrain)
        self.assertIn("stations", terrain)


if __name__ == "__main__":
    unittest.main()
