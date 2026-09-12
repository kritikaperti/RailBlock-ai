"""
Pydantic Data Models for AI-Powered Automatic Block Planning System (IR-ABPS)
Indian Railways Multi-Department Maintenance & Corridor Optimization
"""

from typing import List, Dict, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime, time


class Department(str, Enum):
    ENGINEERING = "ENGINEERING"  # TMS (Track, Turnouts, Ballast, Bridges)
    SNT = "SNT"                  # SMMS (Signals, Interlocking, Point Machines, Track Circuits)
    TRD = "TRD"                  # TDMS (Traction Distribution, 25kV OHE, Sub-stations)
    OPERATING = "OPERATING"      # COA (Train operations, Traffic control)


class Severity(str, Enum):
    EMERGENCY = "EMERGENCY"      # Imminent safety hazard (USFD IMR, Signal fail, OHE parting)
    CRITICAL = "CRITICAL"        # Severe defect (TSR threshold, Point overcurrent, Hotspot)
    HIGH = "HIGH"                # Approaching statutory limits / high wear rate
    MEDIUM = "MEDIUM"            # Periodic maintenance due / moderate defect
    LOW = "LOW"                  # Routine inspection / minor maintenance


class LineType(str, Enum):
    UP_MAIN = "UP_MAIN"
    DOWN_MAIN = "DOWN_MAIN"
    THIRD_LINE = "THIRD_LINE"
    FOURTH_LINE = "FOURTH_LINE"
    COMMON_LOOP = "COMMON_LOOP"
    YARD_LINE = "YARD_LINE"


class MachineType(str, Enum):
    NONE = "NONE"
    CSM_TAMPER = "CSM_TAMPER"              # Continuous Action Tamping Machine
    BCM_SCREENER = "BCM_SCREENER"          # Ballast Cleaning Machine
    UNIMAT_TURNOUT = "UNIMAT_TURNOUT"      # Points & Crossing Tamping Machine
    TOWER_WAGON = "TOWER_WAGON"            # TRD 8-Wheeler OHE Tower Wagon
    WIRING_TRAIN = "WIRING_TRAIN"          # OHE Wiring / Re-catenary Train
    DGS_STABILIZER = "DGS_STABILIZER"      # Dynamic Track Stabilizer
    USFD_VEHICLE = "USFD_VEHICLE"          # Ultrasonic Rail Testing Vehicle


class TrainType(str, Enum):
    VANDE_BHARAT = "VANDE_BHARAT"          # Super-premium (Priority 1)
    RAJDHANI_SHATABDI = "RAJDHANI_SHATABDI"# Premium express (Priority 2)
    SUPERFAST_MAIL = "SUPERFAST_MAIL"      # Express / Superfast (Priority 3)
    PASSENGER_MEMU = "PASSENGER_MEMU"      # Regional passenger (Priority 4)
    FREIGHT_CONTAINER = "FREIGHT_CONTAINER"# High priority goods (Priority 5)
    FREIGHT_COAL_MINERAL = "FREIGHT_COAL_MINERAL" # Heavy haul bulk (Priority 6)
    FREIGHT_GENERAL = "FREIGHT_GENERAL"    # General goods rake (Priority 7)


class Horizon(str, Enum):
    DAILY = "DAILY"     # 24-hour tactical execution schedule
    WEEKLY = "WEEKLY"   # 7-day rolling integrated corridor plan
    MONTHLY = "MONTHLY" # 30-day master mega-block cycle


# --- Raw Departmental Feeds ---

class TMSDefect(BaseModel):
    """Track Management System (TMS) Record"""
    id: str
    section_id: str
    station_from: str
    station_to: str
    line: LineType
    start_km: float
    end_km: float
    defect_type: str  # e.g., 'USFD_IMR_WELD_FLAW', 'TGI_DIP_URGENT', 'TURNOUT_TONGUE_RAIL_WEAR', 'BALLAST_DEEP_SCREENING_OVERDUE'
    severity: Severity
    speed_restriction_if_deferred_kmph: Optional[int] = None
    urgency_days_remaining: int
    gross_million_tonnes: float
    detected_on: str
    description: str


class SMMSDefect(BaseModel):
    """Signalling Maintenance & Management System (SMMS) Record"""
    id: str
    section_id: str
    station_from: str
    station_to: str
    line: LineType
    location_km: float
    equipment_type: str  # e.g., 'POINT_MACHINE_101A', 'SIGNAL_ASPECT_HOME', 'MSDAC_AXLE_COUNTER', 'TRACK_CIRCUIT_LOW_IR'
    defect_type: str
    severity: Severity
    urgency_days_remaining: int
    operating_current_draw_amp: Optional[float] = None
    insulation_resistance_megaohm: Optional[float] = None
    detected_on: str
    description: str


class TDMSDefect(BaseModel):
    """Traction Distribution Management System (TDMS) Record"""
    id: str
    section_id: str
    station_from: str
    station_to: str
    line: LineType
    start_km: float
    end_km: float
    equipment_type: str  # e.g., 'OHE_CONTACT_WIRE', 'CANTILEVER_ASSEMBLY', 'NEUTRAL_SECTION', 'FEEDER_ISOLATOR'
    defect_type: str
    severity: Severity
    contact_wire_wear_mm: Optional[float] = None
    hotspot_temp_celsius: Optional[float] = None
    urgency_days_remaining: int
    detected_on: str
    description: str


class COATrainSchedule(BaseModel):
    """Control Office Application (COA) Train Path Record"""
    train_number: str
    train_name: str
    train_type: TrainType
    priority: int  # 1 (Highest) to 7
    direction: str  # 'UP' or 'DOWN'
    origin: str
    destination: str
    station_timings: Dict[str, Dict[str, Any]]  # {station_code: {"arr": "HH:MM", "dep": "HH:MM", "km": float}}
    average_speed_kmph: float
    delay_minutes: int = 0
    can_be_regulated_on_loop: bool = True
    max_acceptable_delay_min: int = 15


class BDMSRequisition(BaseModel):
    """Block Demand Management System (BDMS) User Requisition"""
    id: str
    department: Department
    section_id: str
    station_from: str
    station_to: str
    line: LineType
    start_km: float
    end_km: float
    requested_duration_minutes: int
    earliest_preferred_date: str
    latest_permissible_date: str
    preferred_window_type: str  # 'DAY_LIGHT', 'NIGHT_SHADOW', 'ANY'
    required_machine: MachineType
    manpower_gangs_required: int
    source_defect_id: Optional[str] = None
    justification: str
    status: str = "PENDING"


# --- Prioritized & Unified Maintenance Task ---

class PrioritizedTask(BaseModel):
    task_id: str
    department: Department
    defect_id: Optional[str] = None
    requisition_id: Optional[str] = None
    section_id: str
    station_from: str
    station_to: str
    line: LineType
    start_km: float
    end_km: float
    title: str
    description: str
    severity: Severity
    required_duration_minutes: int
    required_machine: MachineType
    manpower_gangs: int
    
    # AI Scoring Attributes
    safety_risk_index: float       # 0 - 100
    punctuality_impact_index: float # 0 - 100
    asset_degradation_score: float # 0 - 100
    regulatory_urgency_score: float# 0 - 100
    composite_criticality_score: float # 0 - 100
    
    recommended_horizon: Horizon
    can_be_shadow_bundled: bool = True


# --- Optimized Block Plan Models ---

class BundledDepartmentTask(BaseModel):
    department: Department
    task_id: str
    title: str
    required_machine: MachineType
    manpower_gangs: int
    work_scope: str


class OptimizedBlock(BaseModel):
    block_id: str
    plan_horizon: Horizon
    date: str
    station_from: str
    station_to: str
    section_id: str
    line: LineType
    start_km: float
    end_km: float
    start_time: str   # "HH:MM" or "YYYY-MM-DDTHH:MM"
    end_time: str
    duration_minutes: int
    primary_department: Department
    allocated_machines: List[MachineType]
    
    # Multi-Department Co-Scheduling (Shadow Blocking)
    is_integrated_mega_block: bool
    participating_departments: List[Department]
    bundled_tasks: List[BundledDepartmentTask]
    coordination_efficiency_gain_pct: float
    
    # Train Impact & Operations
    impacted_trains_count: int
    total_train_delay_minutes: int
    regulated_trains: List[str]  # List of train numbers
    diverted_trains: List[str]
    cancellations_count: int = 0
    safety_margin_minutes: int
    
    # Status & Formal Clearance
    disconnection_notice_number: str
    sanction_status: str  # "SANCTIONED", "PROVISIONAL", "REQUESTED", "ACTIVE", "COMPLETED"
    remarks: str


class HorizonPlanSummary(BaseModel):
    horizon: Horizon
    total_blocks_scheduled: int
    integrated_mega_blocks: int
    shadow_bundled_tasks_count: int
    total_block_hours: float
    multi_department_utilization_pct: float
    projected_asset_availability_pct: float
    estimated_train_delay_hours: float
    blocks: List[OptimizedBlock]


# --- What-If Simulation Models ---

class WhatIfScenarioType(str, Enum):
    EMERGENCY_RAIL_FRACTURE = "EMERGENCY_RAIL_FRACTURE"
    FREIGHT_TRAFFIC_SURGE = "FREIGHT_TRAFFIC_SURGE"
    TRACK_MACHINE_BREAKDOWN = "TRACK_MACHINE_BREAKDOWN"
    FOG_WEATHER_SPEED_DROP = "FOG_WEATHER_SPEED_DROP"
    OHE_HOTSPOT_ALERT = "OHE_HOTSPOT_ALERT"


class WhatIfScenarioRequest(BaseModel):
    scenario_type: WhatIfScenarioType
    station_from: Optional[str] = "KANPUR_CENTRAL"
    station_to: Optional[str] = "FATEHPUR"
    line: Optional[LineType] = LineType.UP_MAIN
    km_location: Optional[float] = 168.4
    freight_increase_pct: Optional[int] = 35
    broken_machine: Optional[MachineType] = MachineType.CSM_TAMPER


class WhatIfSimulationResult(BaseModel):
    scenario_title: str
    impact_summary: str
    original_plan_violation_count: int
    re_optimized_blocks_count: int
    emergency_block_granted: Optional[OptimizedBlock] = None
    affected_trains: List[Dict[str, Any]]
    asset_uptime_delta_pct: float
    train_delay_delta_minutes: int
    ai_resolution_strategy: str


# --- Overall Benchmark & KPI System ---

class SystemBenchmarkMetrics(BaseModel):
    asset_availability_before_ai_pct: float
    asset_availability_after_ai_pct: float
    asset_availability_gain_pct: float
    
    train_punctuality_before_ai_pct: float
    train_punctuality_after_ai_pct: float
    train_delay_reduction_pct: float
    
    multi_department_block_utilization_before_ai: float
    multi_department_block_utilization_after_ai: float
    
    shadow_blocking_efficiency_pct: float
    overdue_safety_defects_resolved_pct: float
    manual_planning_time_hours: float
    ai_planning_time_seconds: float


# --- Authentication & User Session Models ---

class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    status: str
    token: str
    username: str
    name: str
    designation: str
    department: str
    role: str
    division: str
    zone: str
    avatar_color: str

