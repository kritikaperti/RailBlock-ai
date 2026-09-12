"""
FastAPI Main Application for RailBlock AI
Indian Railways AI-Powered Automatic Block Planning System (IR-ABPS)
"""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse, Response

from backend.models import (
    Department, Severity, LineType, MachineType, TrainType, Horizon,
    TMSDefect, SMMSDefect, TDMSDefect, COATrainSchedule, BDMSRequisition,
    PrioritizedTask, OptimizedBlock, HorizonPlanSummary, WhatIfScenarioRequest,
    WhatIfSimulationResult, SystemBenchmarkMetrics, LoginRequest, LoginResponse
)
from backend.auth import AuthManager, OFFICIAL_ACCOUNTS, UserProfile, RegisterRequest
from backend.config import get_config, update_domain, SystemConfig
from backend.db_connector import DB_MANAGER, DBConnectionConfig, QueryRequest
from backend.live_api_connectors import CONNECTORS_HUB
from backend.data_generator import DataStore
from backend.ai_prioritizer import AIPrioritizer
from backend.multi_horizon_planner import MultiHorizonPlanner
from backend.simulator import WhatIfSimulator
from backend.report_generator import ReportGenerator

app = FastAPI(
    title="RailBlock AI - Indian Railways Automatic Block Planning System",
    description="AI-powered multi-department block planning, shadow blocking, and corridor optimization for Indian Railways.",
    version="2.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Data Store
store = DataStore()


def _ensure_optimized():
    """Helper to run AI prioritization and multi-horizon optimization if not done yet"""
    if not store.prioritized_tasks or not store.plans_by_horizon:
        tasks = AIPrioritizer.prioritize_all_feeds(
            tms_defects=store.tms_defects,
            smms_defects=store.smms_defects,
            tdms_defects=store.tdms_defects,
            bdms_reqs=store.bdms_requisitions
        )
        store.prioritized_tasks = tasks
        store.plans_by_horizon = MultiHorizonPlanner.generate_all_horizon_plans(
            tasks=tasks,
            trains=store.coa_trains,
            base_date="2026-08-27"
        )
        store.last_optimized_timestamp = datetime.now().isoformat()


@app.on_event("startup")
def startup_event():
    _ensure_optimized()


# --- Authentication & User Session Endpoints ---

@app.post("/api/auth/login", response_model=LoginResponse)
def login(req: LoginRequest):
    """Authenticates Indian Railways Officer credentials and returns session profile"""
    res = AuthManager.authenticate(req.username, req.password)
    if not res:
        raise HTTPException(status_code=401, detail="Invalid Indian Railways official credentials")
    
    token, profile = res
    return LoginResponse(
        status="SUCCESS",
        token=token,
        username=profile.username,
        name=profile.name,
        designation=profile.designation,
        department=profile.department.value,
        role=profile.role,
        division=profile.division,
        zone=profile.zone,
        avatar_color=profile.avatar_color
    )


@app.post("/api/auth/logout")
def logout(payload: Dict[str, str] = Body(...)):
    """Logs out the active user and clears the session"""
    token = payload.get("token", "")
    AuthManager.logout(token)
    return {"status": "SUCCESS", "message": "Successfully logged out of RailBlock AI session"}


@app.get("/api/auth/me", response_model=Dict[str, Any])
def get_current_user(token: Optional[str] = Query(None)):
    """Validates session token and returns active officer details"""
    if not token:
        raise HTTPException(status_code=401, detail="Missing session token")
    user = AuthManager.get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    return {
        "authenticated": True,
        "user": user
    }


@app.post("/api/auth/register", response_model=LoginResponse)
def register_user(req: RegisterRequest):
    """Registers a new officer/user account and creates an active session"""
    try:
        token, profile = AuthManager.register_user(req)
        return LoginResponse(
            status="SUCCESS",
            token=token,
            username=profile.username,
            name=profile.name,
            designation=profile.designation,
            department=profile.department.value,
            role=profile.role,
            division=profile.division,
            zone=profile.zone,
            avatar_color=profile.avatar_color
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/auth/users", response_model=List[UserProfile])
def get_all_registered_users():
    """Lists all registered Indian Railways users and officers"""
    return AuthManager.list_users()


@app.get("/api/auth/officials")
def list_demo_officials():
    """Returns list of pre-configured Indian Railways official roles for quick access"""
    return [
        {
            "username": k,
            "name": v["profile"].name,
            "designation": v["profile"].designation,
            "department": v["profile"].department.value,
            "role": v["profile"].role,
            "avatar_color": v["profile"].avatar_color
        }
        for k, v in OFFICIAL_ACCOUNTS.items()
    ]


# --- System Configuration & Domain Name API ---

@app.get("/api/config", response_model=SystemConfig)
def get_system_config():
    """Returns current website domain name, system branding, and portal settings"""
    return get_config()


@app.post("/api/config/domain", response_model=SystemConfig)
def set_domain_name(payload: Dict[str, Any] = Body(...)):
    """Updates the website domain name, branding title, and portal URLs dynamically"""
    new_domain = payload.get("domain_name", "abps.indianrailways.gov.in")
    new_app_name = payload.get("app_name")
    return update_domain(new_domain=new_domain, new_app_name=new_app_name)


# --- Real-Life Database & Live API Connectors API ---

@app.get("/api/db/status")
def get_db_status():
    """Returns connection health and summary of records across all railway tables"""
    return DB_MANAGER.get_database_status()


@app.get("/api/db/tables")
def get_db_tables():
    """Inspects all table schemas and column structures in connected railway DB"""
    return DB_MANAGER.list_tables()


@app.post("/api/db/connect")
def connect_database(config: DBConnectionConfig):
    """Configures connection to PostgreSQL, Oracle, MySQL, or SQLite database"""
    return DB_MANAGER.connect_external_database(config)


@app.post("/api/db/query")
def execute_sql_query(payload: QueryRequest):
    """Executes safe SQL queries against connected Indian Railways database"""
    try:
        return DB_MANAGER.execute_query(payload.sql_query, limit=payload.limit)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/connectors/status")
def get_connectors_status():
    """Returns live connection health for all CRIS & data.gov.in APIs"""
    return CONNECTORS_HUB.get_connectors_status()


@app.post("/api/connectors/cris/sync")
def sync_cris_feed(payload: Dict[str, str] = Body(...)):
    """Triggers on-demand synchronization with CRIS (TMS, SMMS, TDMS, COA, FOIS, NTES)"""
    system_name = payload.get("system_name", "TMS")
    try:
        return CONNECTORS_HUB.sync_from_cris(system_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/connectors/data-gov/sync")
def sync_data_gov(payload: Dict[str, Any] = Body(...)):
    """Synchronizes live datasets from data.gov.in using OGD API Key"""
    api_key = payload.get("api_key")
    return CONNECTORS_HUB.sync_from_data_gov_in(api_key)


# --- Railway Network & Multi-Corridor API ---

@app.get("/api/corridors", response_model=Dict[str, Any])
def get_corridors():
    """Returns all high-density corridors across Indian Railways"""
    return store.corridors


@app.get("/api/network", response_model=Dict[str, Any])
def get_network(corridor_id: Optional[str] = "CORRIDOR_GRAND_CHORD"):
    """Returns railway stations, sections, and corridor layout"""
    return {
        "active_corridor": store.corridors.get(corridor_id, store.corridors["CORRIDOR_GRAND_CHORD"]),
        "corridors_available": store.corridors,
        "stations": store.stations,
        "sections": store.sections
    }


@app.get("/api/network/terrain")
def get_corridor_terrain(corridor_id: Optional[str] = "CORRIDOR_GRAND_CHORD"):
    """Returns geographic rivers, jungles, forest reserves, and bridges along the corridor"""
    from backend.data_generator import TERRAIN_FEATURES_GRAND_CHORD
    return {
        "corridor_id": corridor_id,
        "terrain": TERRAIN_FEATURES_GRAND_CHORD,
        "total_rivers": len(TERRAIN_FEATURES_GRAND_CHORD["rivers"]),
        "total_jungles": len(TERRAIN_FEATURES_GRAND_CHORD["jungles"])
    }


# --- Train Timetable & Passenger Operations (data.gov.in Schema) ---

@app.get("/api/timetable")
def get_train_timetable(
    train_type: Optional[str] = None,
    direction: Optional[str] = None,
    query: Optional[str] = None
):
    """
    Returns Master Train Time Table aligned with data.gov.in / NTES schema.
    Supports filtering by Train Type, Direction, and search terms.
    """
    results = store.timetable_master
    if train_type:
        results = [t for t in results if t["type"] == train_type or t["type"].value == train_type]
    if direction:
        results = [t for t in results if t["direction"] == direction.upper()]
    if query:
        q = query.lower()
        results = [
            t for t in results
            if q in t["train_no"].lower() or q in t["name"].lower() or q in t["origin"].lower() or q in t["destination"].lower()
        ]
    return {
        "source": "Ministry of Railways / data.gov.in (National Train Enquiry System)",
        "count": len(results),
        "trains": results
    }


# --- data.gov.in Open Data Catalog & Schema Hub ---

@app.get("/api/data-gov-in/catalog")
def get_open_data_catalog():
    """Returns official metadata for Indian Railways datasets on data.gov.in"""
    return {
        "portal": "Open Government Data (OGD) Platform India",
        "url": "https://www.data.gov.in/sector/railways",
        "ministry": "Ministry of Railways, Government of India",
        "datasets": [
            {
                "id": "IR-DATA-001",
                "title": "Indian Railways Master Train Time Table & Station Schedules",
                "category": "Passenger & Freight Operations",
                "format": "JSON / CSV / REST API",
                "source_system": "National Train Enquiry System (NTES) & Control Office Application (COA)",
                "records_count": len(store.timetable_master),
                "frequency": "Dynamic / Daily Update",
                "data_gov_link": "https://www.data.gov.in/sector/railways"
            },
            {
                "id": "IR-DATA-002",
                "title": "Track Fixed Infrastructure Defect Register & Ultrasonic Flaw Log",
                "category": "Civil Engineering & Safety",
                "format": "JSON / CSV",
                "source_system": "Track Management System (TMS) & RDSO Lucknow",
                "records_count": len(store.tms_defects),
                "frequency": "Real-time Field Telemetry",
                "data_gov_link": "https://www.data.gov.in/sector/railways"
            },
            {
                "id": "IR-DATA-003",
                "title": "Signalling & Electronic Interlocking Telemetry Anomaly Log",
                "category": "Signalling & Telecommunications",
                "format": "JSON / CSV",
                "source_system": "Signalling Maintenance & Management System (SMMS)",
                "records_count": len(store.smms_defects),
                "frequency": "Continuous 24x7 IoT Telemetry",
                "data_gov_link": "https://www.data.gov.in/sector/railways"
            },
            {
                "id": "IR-DATA-004",
                "title": "25kV AC Traction & OHE Contact Wire Wear Inspection Register",
                "category": "Electrical & Traction Distribution",
                "format": "JSON / CSV",
                "source_system": "Traction Distribution Management System (TDMS)",
                "records_count": len(store.tdms_defects),
                "frequency": "Thermovision & Tower Wagon Patrols",
                "data_gov_link": "https://www.data.gov.in/sector/railways"
            },
            {
                "id": "IR-DATA-005",
                "title": "Integrated Mega-Block Sanction Circulars (Form B)",
                "category": "Corridor Optimization & Operations",
                "format": "JSON / Form B PDF",
                "source_system": "RailBlock AI (IR-ABPS) / BDMS",
                "records_count": len(store.plans_by_horizon.get("DAILY", HorizonPlanSummary(horizon=Horizon.DAILY, total_blocks_scheduled=0, integrated_mega_blocks=0, shadow_bundled_tasks_count=0, total_block_hours=0, multi_department_utilization_pct=0, projected_asset_availability_pct=0, estimated_train_delay_hours=0, blocks=[])).blocks),
                "frequency": "Daily / Weekly / Monthly Cycles",
                "data_gov_link": "https://www.data.gov.in/sector/railways"
            }
        ]
    }


@app.get("/api/data-gov-in/export/{dataset_name}")
def export_dataset(dataset_name: str):
    """Exports raw JSON dataset matching data.gov.in standards"""
    if dataset_name == "timetable":
        return {"dataset": "train_timetable_master", "records": store.timetable_master}
    elif dataset_name == "tms_defects":
        return {"dataset": "tms_track_defects", "records": store.tms_defects}
    elif dataset_name == "smms_defects":
        return {"dataset": "smms_signalling_defects", "records": store.smms_defects}
    elif dataset_name == "tdms_defects":
        return {"dataset": "tdms_traction_defects", "records": store.tdms_defects}
    elif dataset_name == "blocks_daily":
        _ensure_optimized()
        return {"dataset": "daily_optimized_blocks", "records": store.plans_by_horizon["DAILY"]}
    else:
        raise HTTPException(status_code=404, detail="Dataset not found")


# --- Departmental Data Feeds API ---

@app.get("/api/feeds/tms", response_model=List[TMSDefect])
def get_tms_feed():
    """Engineering Track Management System (TMS) defects & overdue maintenance"""
    return store.tms_defects


@app.get("/api/feeds/smms", response_model=List[SMMSDefect])
def get_smms_feed():
    """Signalling Maintenance & Management System (SMMS) defects & anomalies"""
    return store.smms_defects


@app.get("/api/feeds/tdms", response_model=List[TDMSDefect])
def get_tdms_feed():
    """Traction Distribution Management System (TDMS) 25kV OHE defects"""
    return store.tdms_defects


@app.get("/api/feeds/coa", response_model=List[COATrainSchedule])
def get_coa_feed():
    """Control Office Application (COA) Master Train Timetable & Goods Forecasts"""
    return store.coa_trains


@app.get("/api/feeds/bdms", response_model=List[BDMSRequisition])
def get_bdms_feed():
    """Block Demand Management System (BDMS) Requisitions"""
    return store.bdms_requisitions


@app.get("/api/feeds/summary", response_model=Dict[str, Any])
def get_feeds_summary():
    """Summary counts across all integrated departmental feeds"""
    return {
        "tms_defects_count": len(store.tms_defects),
        "smms_defects_count": len(store.smms_defects),
        "tdms_defects_count": len(store.tdms_defects),
        "total_defects_integrated": len(store.tms_defects) + len(store.smms_defects) + len(store.tdms_defects),
        "coa_trains_count": len(store.coa_trains),
        "bdms_requisitions_count": len(store.bdms_requisitions),
        "last_synced": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


# --- AI Task Prioritization & Scoring API ---

@app.get("/api/tasks/prioritized", response_model=List[PrioritizedTask])
def get_prioritized_tasks(department: Optional[Department] = None, horizon: Optional[Horizon] = None):
    """Returns AI scored and ranked maintenance tasks across departments"""
    _ensure_optimized()
    tasks = store.prioritized_tasks
    if department:
        tasks = [t for t in tasks if t.department == department]
    if horizon:
        tasks = [t for t in tasks if t.recommended_horizon == horizon]
    return tasks


# --- Optimization & Multi-Horizon Scheduling API ---

@app.post("/api/optimize", response_model=Dict[str, Any])
def run_ai_optimizer():
    """
    Executes full AI Multi-Department Corridor Optimization.
    Calculates task prioritization, shadow-block co-scheduling, and multi-horizon plans.
    """
    tasks = AIPrioritizer.prioritize_all_feeds(
        tms_defects=store.tms_defects,
        smms_defects=store.smms_defects,
        tdms_defects=store.tdms_defects,
        bdms_reqs=store.bdms_requisitions
    )
    store.prioritized_tasks = tasks
    store.plans_by_horizon = MultiHorizonPlanner.generate_all_horizon_plans(
        tasks=tasks,
        trains=store.coa_trains,
        base_date="2026-08-27"
    )
    store.last_optimized_timestamp = datetime.now().isoformat()
    
    daily_summary = store.plans_by_horizon["DAILY"]
    benchmarks = MultiHorizonPlanner.compute_system_benchmark(daily_summary)
    
    return {
        "status": "SUCCESS",
        "optimized_at": store.last_optimized_timestamp,
        "total_tasks_prioritized": len(tasks),
        "daily_plan": store.plans_by_horizon["DAILY"],
        "weekly_plan": store.plans_by_horizon["WEEKLY"],
        "monthly_plan": store.plans_by_horizon["MONTHLY"],
        "benchmarks": benchmarks
    }


@app.get("/api/plans/{horizon}", response_model=HorizonPlanSummary)
def get_horizon_plan(horizon: Horizon):
    """Retrieves optimized block schedule for DAILY, WEEKLY, or MONTHLY horizon"""
    _ensure_optimized()
    key = horizon.value
    if key not in store.plans_by_horizon:
        raise HTTPException(status_code=404, detail="Horizon plan not found")
    return store.plans_by_horizon[key]


# --- Benchmarks & Performance Metrics API ---

@app.get("/api/benchmarks", response_model=SystemBenchmarkMetrics)
def get_benchmarks():
    """Compares Legacy Manual Block Planning vs RailBlock AI Performance"""
    _ensure_optimized()
    daily_summary = store.plans_by_horizon["DAILY"]
    return MultiHorizonPlanner.compute_system_benchmark(daily_summary)


# --- What-If Simulation API ---

@app.post("/api/simulate", response_model=WhatIfSimulationResult)
def simulate_scenario(req: WhatIfScenarioRequest):
    """Executes dynamic What-If simulation scenario and AI re-optimization"""
    _ensure_optimized()
    current_blocks = store.plans_by_horizon["DAILY"].blocks
    result = WhatIfSimulator.run_simulation(req, store.coa_trains, current_blocks)
    store.simulation_history.append(result)
    return result


# --- Official Indian Railways Form B Sanction Memo API ---

@app.get("/api/block/{block_id}/memo", response_model=Dict[str, Any])
def get_block_memo(block_id: str):
    """Generates official Indian Railways Form B Joint Block Sanction Memo"""
    _ensure_optimized()
    target_block = None
    for h in store.plans_by_horizon.values():
        for b in h.blocks:
            if b.block_id == block_id:
                target_block = b
                break
        if target_block:
            break
            
    if not target_block:
        raise HTTPException(status_code=404, detail=f"Block ID '{block_id}' not found")
        
    return ReportGenerator.generate_form_b_memo(target_block)


# --- Custom Defect Ingestion Endpoint ---

@app.post("/api/feeds/defect")
def add_custom_defect(payload: Dict[str, Any] = Body(...)):
    """Allows control office or field engineers to inject a new defect dynamically"""
    dept = payload.get("department", "ENGINEERING")
    now_str = datetime.now().strftime("%Y-%m-%d")
    
    if dept == "ENGINEERING":
        new_def = TMSDefect(
            id=f"TMS-2026-{len(store.tms_defects) + 1001}",
            section_id=payload.get("section_id", "SEC_CNB_FTP"),
            station_from=payload.get("station_from", "CNB"),
            station_to=payload.get("station_to", "FTP"),
            line=payload.get("line", LineType.UP_MAIN),
            start_km=float(payload.get("start_km", 450.0)),
            end_km=float(payload.get("end_km", 452.0)),
            defect_type=payload.get("defect_type", "USFD_IMR_WELD_FLAW"),
            severity=payload.get("severity", Severity.CRITICAL),
            speed_restriction_if_deferred_kmph=payload.get("speed_restriction_if_deferred_kmph", 30),
            urgency_days_remaining=int(payload.get("urgency_days_remaining", 1)),
            gross_million_tonnes=55.0,
            detected_on=now_str,
            description=payload.get("description", "Field engineer logged defect via mobile inspection app.")
        )
        store.tms_defects.insert(0, new_def)
    elif dept == "SNT":
        new_def = SMMSDefect(
            id=f"SMMS-2026-{len(store.smms_defects) + 2001}",
            section_id=payload.get("section_id", "SEC_CNB_FTP"),
            station_from=payload.get("station_from", "CNB"),
            station_to=payload.get("station_to", "FTP"),
            line=payload.get("line", LineType.UP_MAIN),
            location_km=float(payload.get("start_km", 450.0)),
            equipment_type="SNT_POINT_MACHINE",
            defect_type=payload.get("defect_type", "POINT_MACHINE_SLOW_THROW"),
            severity=payload.get("severity", Severity.HIGH),
            urgency_days_remaining=int(payload.get("urgency_days_remaining", 2)),
            operating_current_draw_amp=5.6,
            insulation_resistance_megaohm=15.0,
            detected_on=now_str,
            description=payload.get("description", "SMMS telemetry alert logged by S&T supervisor.")
        )
        store.smms_defects.insert(0, new_def)
    else:
        new_def = TDMSDefect(
            id=f"TDMS-2026-{len(store.tdms_defects) + 3001}",
            section_id=payload.get("section_id", "SEC_CNB_FTP"),
            station_from=payload.get("station_from", "CNB"),
            station_to=payload.get("station_to", "FTP"),
            line=payload.get("line", LineType.UP_MAIN),
            start_km=float(payload.get("start_km", 450.0)),
            end_km=float(payload.get("end_km", 452.0)),
            equipment_type="TRD_OHE_CANTILEVER",
            defect_type=payload.get("defect_type", "HOTSPOT_FEEDER_JUMPER"),
            severity=payload.get("severity", Severity.EMERGENCY),
            contact_wire_wear_mm=7.8,
            hotspot_temp_celsius=88.0,
            urgency_days_remaining=int(payload.get("urgency_days_remaining", 1)),
            detected_on=now_str,
            description=payload.get("description", "TDMS Thermovision patrol recorded hotspot.")
        )
        store.tdms_defects.insert(0, new_def)
        
    # Re-run optimization
    run_ai_optimizer()
    return {"status": "SUCCESS", "message": f"Defect injected for {dept} and AI plan re-optimized."}


# --- Robust Frontend & Static Files Serving for Local & Vercel Serverless ---

def _find_frontend_file(rel_path: str) -> Optional[str]:
    possible_roots = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend"),
        os.path.join(os.getcwd(), "frontend"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend"),
        "/var/task/frontend",
        "frontend"
    ]
    for root in possible_roots:
        p = os.path.normpath(os.path.join(root, rel_path))
        if os.path.exists(p) and os.path.isfile(p):
            return p
    return None

def _get_index_html() -> str:
    path = _find_frontend_file("index.html")
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return "<!DOCTYPE html><html><body><h1>RailBlock AI</h1><p>Control Room Dashboard loading...</p></body></html>"

# Mount local StaticFiles if directory exists
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/", response_class=HTMLResponse)
@app.get("/api", response_class=HTMLResponse)
@app.get("/api/", response_class=HTMLResponse)
@app.get("/api/index", response_class=HTMLResponse)
@app.get("/api/index.py", response_class=HTMLResponse)
@app.get("/index.html", response_class=HTMLResponse)
def serve_index():
    return HTMLResponse(content=_get_index_html())

@app.get("/static/css/{file_name}")
@app.get("/css/{file_name}")
def serve_css(file_name: str):
    path = _find_frontend_file(f"css/{file_name}")
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return Response(content=f.read(), media_type="text/css")
    raise HTTPException(status_code=404, detail="CSS file not found")

@app.get("/static/js/{file_name}")
@app.get("/js/{file_name}")
def serve_js(file_name: str):
    path = _find_frontend_file(f"js/{file_name}")
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return Response(content=f.read(), media_type="application/javascript")
    raise HTTPException(status_code=404, detail="JS file not found")

