"""
API Integration & End-to-End Test for RailBlock AI
Validates Network, Multi-Corridor, data.gov.in Timetable, Optimizer, and Form B Memos
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_api_suite():
    print("Testing GET /api/config...")
    res = client.get("/api/config")
    assert res.status_code == 200
    assert "domain_name" in res.json()
    print("[OK] Domain config endpoint OK")

    print("Testing POST /api/config/domain...")
    res = client.post("/api/config/domain", json={"domain_name": "abps.indianrailways.gov.in", "app_name": "RailBlock AI"})
    assert res.status_code == 200
    assert res.json()["domain_name"] == "abps.indianrailways.gov.in"
    print("[OK] Set domain name endpoint OK")

    print("Testing GET /api/corridors...")
    res = client.get("/api/corridors")
    assert res.status_code == 200
    corridors = res.json()
    assert "CORRIDOR_GRAND_CHORD" in corridors
    assert "CORRIDOR_WESTERN_TRUNK" in corridors
    print("[OK] Multi-Corridor endpoint OK")

    print("Testing GET /api/network...")
    res = client.get("/api/network")
    assert res.status_code == 200
    data = res.json()
    assert len(data["stations"]) >= 8
    print("[OK] Network endpoint OK")

    print("Testing GET /api/network/terrain...")
    res = client.get("/api/network/terrain")
    assert res.status_code == 200
    terr_data = res.json()
    assert terr_data["total_rivers"] >= 5
    assert terr_data["total_jungles"] >= 3
    print("[OK] Terrain Rivers & Jungles endpoint OK")

    print("Testing GET /api/timetable (data.gov.in NTES Master)...")
    res = client.get("/api/timetable")
    assert res.status_code == 200
    tt_data = res.json()
    assert tt_data["count"] >= 10
    first_train = tt_data["trains"][0]
    assert "halts" in first_train
    assert len(first_train["halts"]) > 0
    print("[OK] Timetable Master endpoint OK")

    print("Testing GET /api/data-gov-in/catalog...")
    res = client.get("/api/data-gov-in/catalog")
    assert res.status_code == 200
    catalog = res.json()
    assert len(catalog["datasets"]) >= 5
    print("[OK] data.gov.in Open Data Catalog endpoint OK")

    print("Testing GET /api/data-gov-in/export/timetable...")
    res = client.get("/api/data-gov-in/export/timetable")
    assert res.status_code == 200
    assert len(res.json()["records"]) >= 10
    print("[OK] data.gov.in Export JSON endpoint OK")

    print("Testing GET /api/feeds/summary...")
    res = client.get("/api/feeds/summary")
    assert res.status_code == 200
    assert res.json()["total_defects_integrated"] >= 60
    print("[OK] Feeds summary OK")

    print("Testing POST /api/optimize...")
    res = client.post("/api/optimize")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert "daily_plan" in data
    assert "weekly_plan" in data
    assert "monthly_plan" in data
    print("[OK] AI Optimization endpoint OK")

    print("Testing GET /api/plans/DAILY...")
    res = client.get("/api/plans/DAILY")
    assert res.status_code == 200
    daily_plan = res.json()
    assert daily_plan["total_blocks_scheduled"] > 0
    first_block_id = daily_plan["blocks"][0]["block_id"]
    print("[OK] Daily plan endpoint OK")

    print(f"Testing GET /api/block/{first_block_id}/memo...")
    res = client.get(f"/api/block/{first_block_id}/memo")
    assert res.status_code == 200
    memo = res.json()
    assert "NORTH CENTRAL RAILWAY" in memo["railway_zone"]
    assert len(memo["joint_signatories"]) == 4
    print("[OK] Form B Memo endpoint OK")

    print("Testing POST /api/simulate (Emergency Rail Fracture)...")
    sim_payload = {
        "scenario_type": "EMERGENCY_RAIL_FRACTURE",
        "station_from": "TDL",
        "station_to": "ETW",
        "km_location": 214.5,
        "line": "UP_MAIN"
    }
    res = client.post("/api/simulate", json=sim_payload)
    assert res.status_code == 200
    sim_data = res.json()
    assert sim_data["emergency_block_granted"] is not None
    print("[OK] What-If Simulator endpoint OK")

    print("Testing static root GET /...")
    res = client.get("/")
    assert res.status_code == 200
    print("[OK] Frontend root OK")

    print("Testing favicon endpoints GET /favicon.ico & /favicon.png...")
    res_ico = client.get("/favicon.ico")
    assert res_ico.status_code == 200
    res_png = client.get("/favicon.png")
    assert res_png.status_code == 200
    print("[OK] Favicon and static assets OK")

    print("\n==========================================")
    print("ALL API ENDPOINTS TESTED AND VERIFIED OK!")
    print("==========================================")


if __name__ == "__main__":
    test_api_suite()
