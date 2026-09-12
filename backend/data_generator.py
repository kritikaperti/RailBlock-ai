"""
Realistic Indian Railways Multi-Corridor Network & Open Dataset Generator
Aligned with Open Government Data (OGD) Platform India: data.gov.in/sector/railways
Integrates TMS, SMMS, TDMS, COA Timetables, and BDMS across Major Trunk Routes
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from backend.models import (
    Department, Severity, LineType, MachineType, TrainType,
    TMSDefect, SMMSDefect, TDMSDefect, COATrainSchedule, BDMSRequisition
)

# ==============================================================================
# MULTI-CORRIDOR RAILWAY NETWORK DEFINITIONS (Aligned with data.gov.in GIS)
# ==============================================================================

CORRIDORS = {
    "CORRIDOR_GRAND_CHORD": {
        "id": "CORRIDOR_GRAND_CHORD",
        "name": "Delhi - Kanpur - Prayagraj - DDU (Grand Chord High-Density Corridor)",
        "zone": "North Central Railway (NCR) & Northern Railway (NR)",
        "division": "Prayagraj (PRYJ) & Pt. Deen Dayal Upadhyaya (DDU)",
        "route_km": 781.0,
        "max_speed": 160,
        "signalling": "Automatic Block Signalling (ABS) with 4-Aspect Signals",
        "traction": "25kV AC 50Hz Traction"
    },
    "CORRIDOR_WESTERN_TRUNK": {
        "id": "CORRIDOR_WESTERN_TRUNK",
        "name": "Mumbai Central - Surat - Vadodara - Kota - Delhi (Western Trunk Route)",
        "zone": "Western Railway (WR) & West Central Railway (WCR)",
        "division": "Mumbai (BCT), Vadodara (BRC) & Kota (KOTA)",
        "route_km": 1386.0,
        "max_speed": 160,
        "signalling": "Automatic Block Signalling & ETCS Level 2 (Kavach)",
        "traction": "25kV AC 50Hz Traction"
    },
    "CORRIDOR_SOUTHERN_MAIN": {
        "id": "CORRIDOR_SOUTHERN_MAIN",
        "name": "Chennai Central - Katpadi - Salem - Erode - Coimbatore / Bengaluru",
        "zone": "Southern Railway (SR) & South Western Railway (SWR)",
        "division": "Chennai (MAS), Salem (SA) & Bengaluru (SBC)",
        "route_km": 497.0,
        "max_speed": 130,
        "signalling": "Absolute & Automatic Block Territory",
        "traction": "25kV AC 50Hz Traction"
    },
    "CORRIDOR_EASTERN_TRUNK": {
        "id": "CORRIDOR_EASTERN_TRUNK",
        "name": "Howrah - Barddhaman - Asansol - Dhanbad - Gaya - DDU",
        "zone": "Eastern Railway (ER) & East Central Railway (ECR)",
        "division": "Howrah (HWH), Asansol (ASN) & Dhanbad (DHN)",
        "route_km": 678.0,
        "max_speed": 130,
        "signalling": "Continuous Track Circuiting & MSDAC",
        "traction": "25kV AC 50Hz Traction"
    }
}

# Grand Chord Station Master
STATIONS_GRAND_CHORD = [
    {"code": "NDLS", "name": "New Delhi", "km": -28.0, "lines": 16, "has_depot": True, "state": "Delhi", "zone": "NR"},
    {"code": "GZB", "name": "Ghaziabad Jn", "km": 0.0, "lines": 6, "has_depot": True, "state": "Uttar Pradesh", "zone": "NR"},
    {"code": "ALJN", "name": "Aligarh Jn", "km": 106.0, "lines": 5, "has_depot": True, "state": "Uttar Pradesh", "zone": "NCR"},
    {"code": "TDL", "name": "Tundla Jn", "km": 204.0, "lines": 5, "has_depot": True, "state": "Uttar Pradesh", "zone": "NCR"},
    {"code": "ETW", "name": "Etawah Jn", "km": 296.0, "lines": 4, "has_depot": False, "state": "Uttar Pradesh", "zone": "NCR"},
    {"code": "CNB", "name": "Kanpur Central", "km": 435.0, "lines": 10, "has_depot": True, "state": "Uttar Pradesh", "zone": "NCR"},
    {"code": "FTP", "name": "Fatehpur", "km": 513.0, "lines": 4, "has_depot": False, "state": "Uttar Pradesh", "zone": "NCR"},
    {"code": "PRYJ", "name": "Prayagraj Jn", "km": 628.0, "lines": 10, "has_depot": True, "state": "Uttar Pradesh", "zone": "NCR"},
    {"code": "MZP", "name": "Mirzapur", "km": 717.0, "lines": 4, "has_depot": False, "state": "Uttar Pradesh", "zone": "NCR"},
    {"code": "DDU", "name": "Pt. Deen Dayal Upadhyaya Jn", "km": 781.0, "lines": 12, "has_depot": True, "state": "Uttar Pradesh", "zone": "ECR"},
]

SECTIONS_GRAND_CHORD = [
    {"id": "SEC_NDLS_GZB", "from": "NDLS", "to": "GZB", "start_km": -28.0, "end_km": 0.0, "max_speed": 110, "lines_count": 4, "track_structure": "60kg UIC / PSC 1660"},
    {"id": "SEC_GZB_ALJN", "from": "GZB", "to": "ALJN", "start_km": 0.0, "end_km": 106.0, "max_speed": 130, "lines_count": 4, "track_structure": "60kg UIC / PSC 1660"},
    {"id": "SEC_ALJN_TDL", "from": "ALJN", "to": "TDL", "start_km": 106.0, "end_km": 204.0, "max_speed": 130, "lines_count": 4, "track_structure": "60kg UIC / PSC 1660"},
    {"id": "SEC_TDL_ETW", "from": "TDL", "to": "ETW", "start_km": 204.0, "end_km": 296.0, "max_speed": 160, "lines_count": 3, "track_structure": "60kg 90UTS / PSC 1660"},
    {"id": "SEC_ETW_CNB", "from": "ETW", "to": "CNB", "start_km": 296.0, "end_km": 435.0, "max_speed": 160, "lines_count": 3, "track_structure": "60kg 90UTS / PSC 1660"},
    {"id": "SEC_CNB_FTP", "from": "CNB", "to": "FTP", "start_km": 435.0, "end_km": 513.0, "max_speed": 130, "lines_count": 3, "track_structure": "60kg UIC / PSC 1660"},
    {"id": "SEC_FTP_PRYJ", "from": "FTP", "to": "PRYJ", "start_km": 513.0, "end_km": 628.0, "max_speed": 130, "lines_count": 3, "track_structure": "60kg UIC / PSC 1660"},
    {"id": "SEC_PRYJ_MZP", "from": "PRYJ", "to": "MZP", "start_km": 628.0, "end_km": 717.0, "max_speed": 130, "lines_count": 3, "track_structure": "60kg UIC / PSC 1660"},
    {"id": "SEC_MZP_DDU", "from": "MZP", "to": "DDU", "start_km": 717.0, "end_km": 781.0, "max_speed": 130, "lines_count": 4, "track_structure": "60kg UIC / PSC 1660"},
]

# Western Corridor Stations
STATIONS_WESTERN = [
    {"code": "MMCT", "name": "Mumbai Central", "km": 0.0, "lines": 8, "has_depot": True, "state": "Maharashtra", "zone": "WR"},
    {"code": "BVI", "name": "Borivali", "km": 30.0, "lines": 8, "has_depot": False, "state": "Maharashtra", "zone": "WR"},
    {"code": "ST", "name": "Surat", "km": 263.0, "lines": 6, "has_depot": True, "state": "Gujarat", "zone": "WR"},
    {"code": "BRC", "name": "Vadodara Jn", "km": 392.0, "lines": 8, "has_depot": True, "state": "Gujarat", "zone": "WR"},
    {"code": "RTM", "name": "Ratlam Jn", "km": 653.0, "lines": 7, "has_depot": True, "state": "Madhya Pradesh", "zone": "WR"},
    {"code": "KOTA", "name": "Kota Jn", "km": 920.0, "lines": 6, "has_depot": True, "state": "Rajasthan", "zone": "WCR"},
    {"code": "MTJ", "name": "Mathura Jn", "km": 1250.0, "lines": 8, "has_depot": True, "state": "Uttar Pradesh", "zone": "NCR"},
    {"code": "NZM", "name": "Hazrat Nizamuddin", "km": 1386.0, "lines": 8, "has_depot": True, "state": "Delhi", "zone": "NR"},
]

# ==============================================================================
# DATA.GOV.IN REAL-WORLD TIMETABLE MASTER (NTES Schema)
# ==============================================================================

OFFICIAL_TRAIN_TIMETABLE_MASTER = [
    # Premium Vande Bharat Expresses
    {
        "train_no": "22436",
        "name": "Vande Bharat Express (NDLS-BSB)",
        "type": TrainType.VANDE_BHARAT,
        "priority": 1,
        "direction": "DOWN",
        "origin": "NDLS",
        "destination": "DDU",
        "days": "Tue, Wed, Fri, Sat, Sun",
        "rakes": "16-Coach Vande Bharat 2.0 (Train 18)",
        "speed": 120.0,
        "max_delay_min": 5,
        "start_time": (6, 0),
        "halts": [
            {"stn": "NDLS", "arr": "06:00", "dep": "06:00", "halt": "Origin", "pf": "16", "km": -28.0},
            {"stn": "GZB", "arr": "06:22", "dep": "06:24", "halt": "2m", "pf": "2", "km": 0.0},
            {"stn": "ALJN", "arr": "07:18", "dep": "07:20", "halt": "2m", "pf": "3", "km": 106.0},
            {"stn": "TDL", "arr": "08:12", "dep": "08:14", "halt": "2m", "pf": "4", "km": 204.0},
            {"stn": "CNB", "arr": "10:08", "dep": "10:12", "halt": "4m", "pf": "1", "km": 435.0},
            {"stn": "PRYJ", "arr": "12:08", "dep": "12:10", "halt": "2m", "pf": "6", "km": 628.0},
            {"stn": "DDU", "arr": "13:45", "dep": "13:50", "halt": "Term", "pf": "2", "km": 781.0},
        ]
    },
    {
        "train_no": "22435",
        "name": "Vande Bharat Express (BSB-NDLS)",
        "type": TrainType.VANDE_BHARAT,
        "priority": 1,
        "direction": "UP",
        "origin": "DDU",
        "destination": "NDLS",
        "days": "Tue, Wed, Fri, Sat, Sun",
        "rakes": "16-Coach Vande Bharat 2.0 (Train 18)",
        "speed": 120.0,
        "max_delay_min": 5,
        "start_time": (15, 0),
        "halts": [
            {"stn": "DDU", "arr": "15:00", "dep": "15:00", "halt": "Origin", "pf": "1", "km": 781.0},
            {"stn": "PRYJ", "arr": "16:30", "dep": "16:32", "halt": "2m", "pf": "5", "km": 628.0},
            {"stn": "CNB", "arr": "18:30", "dep": "18:34", "halt": "4m", "pf": "1", "km": 435.0},
            {"stn": "TDL", "arr": "20:28", "dep": "20:30", "halt": "2m", "pf": "3", "km": 204.0},
            {"stn": "ALJN", "arr": "21:22", "dep": "21:24", "halt": "2m", "pf": "2", "km": 106.0},
            {"stn": "GZB", "arr": "22:18", "dep": "22:20", "halt": "2m", "pf": "1", "km": 0.0},
            {"stn": "NDLS", "arr": "22:50", "dep": "22:50", "halt": "Term", "pf": "16", "km": -28.0},
        ]
    },
    # Rajdhani Express Trains
    {
        "train_no": "12302",
        "name": "Howrah Rajdhani Express (via Gaya)",
        "type": TrainType.RAJDHANI_SHATABDI,
        "priority": 2,
        "direction": "DOWN",
        "origin": "NDLS",
        "destination": "DDU",
        "days": "Daily",
        "rakes": "LHB Tejas Sleeper Rake",
        "speed": 112.0,
        "max_delay_min": 10,
        "start_time": (16, 50),
        "halts": [
            {"stn": "NDLS", "arr": "16:50", "dep": "16:50", "halt": "Origin", "pf": "15", "km": -28.0},
            {"stn": "CNB", "arr": "21:32", "dep": "21:37", "halt": "5m", "pf": "4", "km": 435.0},
            {"stn": "PRYJ", "arr": "23:43", "dep": "23:45", "halt": "2m", "pf": "4", "km": 628.0},
            {"stn": "DDU", "arr": "01:42", "dep": "01:52", "halt": "10m", "pf": "1", "km": 781.0},
        ]
    },
    {
        "train_no": "12301",
        "name": "Howrah Rajdhani Express (UP to NDLS)",
        "type": TrainType.RAJDHANI_SHATABDI,
        "priority": 2,
        "direction": "UP",
        "origin": "DDU",
        "destination": "NDLS",
        "days": "Daily",
        "rakes": "LHB Tejas Sleeper Rake",
        "speed": 112.0,
        "max_delay_min": 10,
        "start_time": (0, 45),
        "halts": [
            {"stn": "DDU", "arr": "00:45", "dep": "00:55", "halt": "10m", "pf": "2", "km": 781.0},
            {"stn": "PRYJ", "arr": "02:43", "dep": "02:45", "halt": "2m", "pf": "1", "km": 628.0},
            {"stn": "CNB", "arr": "04:50", "dep": "04:55", "halt": "5m", "pf": "1", "km": 435.0},
            {"stn": "NDLS", "arr": "10:05", "dep": "10:05", "halt": "Term", "pf": "15", "km": -28.0},
        ]
    },
    {
        "train_no": "12314",
        "name": "Sealdah Rajdhani Express",
        "type": TrainType.RAJDHANI_SHATABDI,
        "priority": 2,
        "direction": "DOWN",
        "origin": "NDLS",
        "destination": "DDU",
        "days": "Daily",
        "rakes": "LHB Tejas Sleeper Rake",
        "speed": 110.0,
        "max_delay_min": 10,
        "start_time": (16, 30),
        "halts": [
            {"stn": "NDLS", "arr": "16:30", "dep": "16:30", "halt": "Origin", "pf": "14", "km": -28.0},
            {"stn": "CNB", "arr": "21:12", "dep": "21:17", "halt": "5m", "pf": "5", "km": 435.0},
            {"stn": "DDU", "arr": "01:27", "dep": "01:37", "halt": "10m", "pf": "2", "km": 781.0},
        ]
    },
    {
        "train_no": "12004",
        "name": "Lucknow Swarna Shatabdi Express",
        "type": TrainType.RAJDHANI_SHATABDI,
        "priority": 2,
        "direction": "DOWN",
        "origin": "NDLS",
        "destination": "CNB",
        "days": "Daily",
        "rakes": "LHB Chair Car Rake",
        "speed": 108.0,
        "max_delay_min": 10,
        "start_time": (6, 10),
        "halts": [
            {"stn": "NDLS", "arr": "06:10", "dep": "06:10", "halt": "Origin", "pf": "12", "km": -28.0},
            {"stn": "GZB", "arr": "06:46", "dep": "06:48", "halt": "2m", "pf": "2", "km": 0.0},
            {"stn": "ALJN", "arr": "07:47", "dep": "07:49", "halt": "2m", "pf": "3", "km": 106.0},
            {"stn": "TDL", "arr": "08:43", "dep": "08:45", "halt": "2m", "pf": "3", "km": 204.0},
            {"stn": "ETW", "arr": "09:40", "dep": "09:42", "halt": "2m", "pf": "2", "km": 296.0},
            {"stn": "CNB", "arr": "11:20", "dep": "11:25", "halt": "Term", "pf": "1", "km": 435.0},
        ]
    },
    # Superfast & Mail Express Trains
    {
        "train_no": "12418",
        "name": "Prayagraj Express",
        "type": TrainType.SUPERFAST_MAIL,
        "priority": 3,
        "direction": "DOWN",
        "origin": "NDLS",
        "destination": "PRYJ",
        "days": "Daily",
        "rakes": "24-Coach LHB Dedicated Rake",
        "speed": 95.0,
        "max_delay_min": 15,
        "start_time": (22, 10),
        "halts": [
            {"stn": "NDLS", "arr": "22:10", "dep": "22:10", "halt": "Origin", "pf": "14", "km": -28.0},
            {"stn": "GZB", "arr": "22:42", "dep": "22:44", "halt": "2m", "pf": "2", "km": 0.0},
            {"stn": "ALJN", "arr": "23:55", "dep": "23:57", "halt": "2m", "pf": "2", "km": 106.0},
            {"stn": "CNB", "arr": "03:50", "dep": "03:55", "halt": "5m", "pf": "6", "km": 435.0},
            {"stn": "FTP", "arr": "04:50", "dep": "04:52", "halt": "2m", "pf": "2", "km": 513.0},
            {"stn": "PRYJ", "arr": "07:00", "dep": "07:00", "halt": "Term", "pf": "1", "km": 628.0},
        ]
    },
    {
        "train_no": "12417",
        "name": "Prayagraj Express (Return to NDLS)",
        "type": TrainType.SUPERFAST_MAIL,
        "priority": 3,
        "direction": "UP",
        "origin": "PRYJ",
        "destination": "NDLS",
        "days": "Daily",
        "rakes": "24-Coach LHB Dedicated Rake",
        "speed": 95.0,
        "max_delay_min": 15,
        "start_time": (22, 10),
        "halts": [
            {"stn": "PRYJ", "arr": "22:10", "dep": "22:10", "halt": "Origin", "pf": "1", "km": 628.0},
            {"stn": "FTP", "arr": "23:16", "dep": "23:18", "halt": "2m", "pf": "1", "km": 513.0},
            {"stn": "CNB", "arr": "00:25", "dep": "00:30", "halt": "5m", "pf": "1", "km": 435.0},
            {"stn": "ALJN", "arr": "04:15", "dep": "04:17", "halt": "2m", "pf": "3", "km": 106.0},
            {"stn": "GZB", "arr": "06:13", "dep": "06:15", "halt": "2m", "pf": "3", "km": 0.0},
            {"stn": "NDLS", "arr": "07:00", "dep": "07:00", "halt": "Term", "pf": "14", "km": -28.0},
        ]
    },
    {
        "train_no": "12802",
        "name": "Purushottam Express (NDLS-PURI)",
        "type": TrainType.SUPERFAST_MAIL,
        "priority": 3,
        "direction": "DOWN",
        "origin": "NDLS",
        "destination": "DDU",
        "days": "Daily",
        "rakes": "22-Coach LHB",
        "speed": 92.0,
        "max_delay_min": 20,
        "start_time": (22, 40),
        "halts": [
            {"stn": "NDLS", "arr": "22:40", "dep": "22:40", "halt": "Origin", "pf": "8", "km": -28.0},
            {"stn": "GZB", "arr": "23:13", "dep": "23:15", "halt": "2m", "pf": "2", "km": 0.0},
            {"stn": "ALJN", "arr": "00:35", "dep": "00:37", "halt": "2m", "pf": "3", "km": 106.0},
            {"stn": "CNB", "arr": "04:00", "dep": "04:05", "halt": "5m", "pf": "4", "km": 435.0},
            {"stn": "FTP", "arr": "05:00", "dep": "05:02", "halt": "2m", "pf": "2", "km": 513.0},
            {"stn": "PRYJ", "arr": "06:55", "dep": "07:00", "halt": "5m", "pf": "5", "km": 628.0},
            {"stn": "MZP", "arr": "08:10", "dep": "08:12", "halt": "2m", "pf": "2", "km": 717.0},
            {"stn": "DDU", "arr": "09:50", "dep": "10:00", "halt": "10m", "pf": "3", "km": 781.0},
        ]
    },
    {
        "train_no": "12398",
        "name": "Mahabodhi Express (NDLS-GAYA)",
        "type": TrainType.SUPERFAST_MAIL,
        "priority": 3,
        "direction": "DOWN",
        "origin": "NDLS",
        "destination": "DDU",
        "days": "Daily",
        "rakes": "22-Coach LHB",
        "speed": 94.0,
        "max_delay_min": 20,
        "start_time": (12, 50),
        "halts": [
            {"stn": "NDLS", "arr": "12:50", "dep": "12:50", "halt": "Origin", "pf": "6", "km": -28.0},
            {"stn": "ALJN", "arr": "14:30", "dep": "14:32", "halt": "2m", "pf": "3", "km": 106.0},
            {"stn": "CNB", "arr": "17:55", "dep": "18:00", "halt": "5m", "pf": "5", "km": 435.0},
            {"stn": "PRYJ", "arr": "20:15", "dep": "20:20", "halt": "5m", "pf": "4", "km": 628.0},
            {"stn": "DDU", "arr": "23:15", "dep": "23:25", "halt": "10m", "pf": "1", "km": 781.0},
        ]
    },
    # Commuter / Regional MEMU
    {
        "train_no": "64583",
        "name": "Kanpur - Fatehpur Daily MEMU",
        "type": TrainType.PASSENGER_MEMU,
        "priority": 4,
        "direction": "DOWN",
        "origin": "CNB",
        "destination": "FTP",
        "days": "Daily",
        "rakes": "12-Car 3-Phase MEMU",
        "speed": 60.0,
        "max_delay_min": 30,
        "start_time": (8, 30),
        "halts": [
            {"stn": "CNB", "arr": "08:30", "dep": "08:30", "halt": "Origin", "pf": "8", "km": 435.0},
            {"stn": "FTP", "arr": "09:55", "dep": "09:55", "halt": "Term", "pf": "3", "km": 513.0},
        ]
    },
    {
        "train_no": "64153",
        "name": "Aligarh - Tundla Shuttle MEMU",
        "type": TrainType.PASSENGER_MEMU,
        "priority": 4,
        "direction": "DOWN",
        "origin": "ALJN",
        "destination": "TDL",
        "days": "Daily",
        "rakes": "12-Car MEMU",
        "speed": 55.0,
        "max_delay_min": 30,
        "start_time": (10, 15),
        "halts": [
            {"stn": "ALJN", "arr": "10:15", "dep": "10:15", "halt": "Origin", "pf": "5", "km": 106.0},
            {"stn": "TDL", "arr": "12:00", "dep": "12:00", "halt": "Term", "pf": "5", "km": 204.0},
        ]
    },
    # High Priority Freight / Freight Operations Information System (FOIS)
    {
        "train_no": "FR-COAL-101",
        "name": "NTPC Dadri Thermal Coal Rake (Singrauli-Dadri)",
        "type": TrainType.FREIGHT_COAL_MINERAL,
        "priority": 6,
        "direction": "UP",
        "origin": "DDU",
        "destination": "GZB",
        "days": "Daily",
        "rakes": "59 BOXNHL Wagons (3,900 Tonnes Coal)",
        "speed": 65.0,
        "max_delay_min": 60,
        "start_time": (1, 0),
        "halts": [
            {"stn": "DDU", "arr": "01:00", "dep": "01:00", "halt": "Origin", "pf": "Yard", "km": 781.0},
            {"stn": "PRYJ", "arr": "03:45", "dep": "03:50", "halt": "Crew", "pf": "Goods", "km": 628.0},
            {"stn": "CNB", "arr": "07:15", "dep": "07:25", "halt": "Crew", "pf": "Goods", "km": 435.0},
            {"stn": "TDL", "arr": "10:45", "dep": "10:50", "halt": "5m", "pf": "Goods", "km": 204.0},
            {"stn": "GZB", "arr": "14:30", "dep": "14:30", "halt": "Term", "pf": "Siding", "km": 0.0},
        ]
    },
    {
        "train_no": "FR-CONCOR-201",
        "name": "JNPT - Dadri Container Express (CONCOR)",
        "type": TrainType.FREIGHT_CONTAINER,
        "priority": 5,
        "direction": "DOWN",
        "origin": "GZB",
        "destination": "DDU",
        "days": "Daily",
        "rakes": "45 BLC Wagons (90 TEUs Double Stack)",
        "speed": 75.0,
        "max_delay_min": 45,
        "start_time": (11, 0),
        "halts": [
            {"stn": "GZB", "arr": "11:00", "dep": "11:00", "halt": "Origin", "pf": "ICD", "km": 0.0},
            {"stn": "ALJN", "arr": "12:35", "dep": "12:35", "halt": "Thru", "pf": "Loop", "km": 106.0},
            {"stn": "CNB", "arr": "16:20", "dep": "16:30", "halt": "Crew", "pf": "Goods", "km": 435.0},
            {"stn": "PRYJ", "arr": "19:15", "dep": "19:20", "halt": "5m", "pf": "Goods", "km": 628.0},
            {"stn": "DDU", "arr": "22:00", "dep": "22:00", "halt": "Term", "pf": "Yard", "km": 781.0},
        ]
    },
    {
        "train_no": "FR-BOBYN-301",
        "name": "Divisional P-Way Ballast Hopper Special",
        "type": TrainType.FREIGHT_GENERAL,
        "priority": 7,
        "direction": "DOWN",
        "origin": "TDL",
        "destination": "CNB",
        "days": "On Demand",
        "rakes": "30 BOBYN Hopper Wagons",
        "speed": 50.0,
        "max_delay_min": 90,
        "start_time": (11, 45),
        "halts": [
            {"stn": "TDL", "arr": "11:45", "dep": "11:45", "halt": "Origin", "pf": "Yard", "km": 204.0},
            {"stn": "CNB", "arr": "16:30", "dep": "16:30", "halt": "Term", "pf": "Yard", "km": 435.0},
        ]
    }
]


# ==============================================================================
# DATASET GENERATION FUNCTIONS
# ==============================================================================

def generate_tms_defects(count: int = 32) -> List[TMSDefect]:
    """Generates Track Management System (TMS) defects & overdue maintenance"""
    catalog = [
        ("USFD_IMR_WELD_FLAW", Severity.EMERGENCY, 1, 30, "Ultrasonic testing (USFD) detected Immediate Removal (IMR) flaw in thermit weld. Emergency fishplate bolted."),
        ("TGI_DIP_URGENT", Severity.CRITICAL, 2, 50, "Track Geometry Index (TGI) dropped below 60 on high speed track. CSM machine tamping required urgently."),
        ("TURNOUT_TONGUE_RAIL_WEAR", Severity.HIGH, 4, 60, "Tongue rail wear at 1 in 12 curved turnout exceeds 6mm limit. Unimat turnout tamper needed."),
        ("BALLAST_DEEP_SCREENING_OVERDUE", Severity.MEDIUM, 14, 75, "Ballast caking > 38%. Deep screening with BCM machine required to restore track elasticity."),
        ("RAIL_CORRUGATION_GRINDING", Severity.LOW, 21, None, "Rail surface micro-cracking and corrugation (0.4mm depth). Rail Grinding Machine (RGM) pass due."),
        ("GLUED_INSULATED_JOINT_FAIL", Severity.CRITICAL, 2, 45, "Glued Insulated Joint endpost fractured; potential track circuit shunting hazard."),
        ("SLEEPER_RENEWAL_FRACTURE", Severity.HIGH, 5, 60, "Cluster of 4 cracked prestressed concrete sleepers on UP line. Casual renewal needed."),
        ("POINT_CROSSING_NOSE_WEAR", Severity.HIGH, 3, 50, "CMS Crossing nose wear 8.5mm. In-situ weld reconditioning required."),
    ]
    
    tms_list = []
    base_date = datetime.now()
    
    for i in range(count):
        sec = random.choice(SECTIONS_GRAND_CHORD)
        dtype, sev, urg, psr, desc_template = random.choice(catalog)
        line = random.choice([LineType.UP_MAIN, LineType.DOWN_MAIN, LineType.THIRD_LINE])
        start_km = round(random.uniform(sec["start_km"], sec["end_km"] - 4.0), 2)
        end_km = round(start_km + random.uniform(0.2, 4.0), 2)
        gmt = round(random.uniform(28.0, 82.5), 1)
        det_date = (base_date - timedelta(days=random.randint(0, 5))).strftime("%Y-%m-%d")
        
        tms = TMSDefect(
            id=f"TMS-2026-{1000 + i}",
            section_id=sec["id"],
            station_from=sec["from"],
            station_to=sec["to"],
            line=line,
            start_km=start_km,
            end_km=end_km,
            defect_type=dtype,
            severity=sev,
            speed_restriction_if_deferred_kmph=psr,
            urgency_days_remaining=urg,
            gross_million_tonnes=gmt,
            detected_on=det_date,
            description=f"{desc_template} Location: KM {start_km}-{end_km} on {line.value} between {sec['from']}-{sec['to']}."
        )
        tms_list.append(tms)
        
    return tms_list


def generate_smms_defects(count: int = 28) -> List[SMMSDefect]:
    """Generates Signalling Maintenance & Management System (SMMS) records"""
    catalog = [
        ("POINT_MACHINE_SLOW_THROW", Severity.CRITICAL, 2, 5.8, 12.0, "Point machine motor operating current 5.8A (normal 3.2A). Throw time 6.4s. Clutch overhaul needed."),
        ("TRACK_CIRCUIT_LOW_IR", Severity.HIGH, 3, None, 1.8, "Track circuit fail-safe relay voltage low (1.1V). Low ballast resistance due to water stagnation."),
        ("MSDAC_AXLE_COUNTER_RESET_ALARM", Severity.CRITICAL, 1, None, 45.0, "Multi-Section Digital Axle Counter dual channel mismatch. Sensor pulse drift detected."),
        ("SIGNAL_LED_ASPECT_DEGRADED", Severity.MEDIUM, 7, 0.45, 100.0, "Green aspect current transformer sensing 15% current drop. LED cluster replacement overdue."),
        ("INTERLOCKING_RELAY_CHATTER", Severity.HIGH, 4, None, 25.0, "Q-series line relay chatter during heavy vibration. Relay rack overhaul required."),
        ("LEVEL_CROSSING_GATE_INTERLOCK", Severity.EMERGENCY, 1, 4.2, 8.0, "LC Gate 74-C electrical boom lock sticking. Solenoid overhaul required immediately."),
    ]
    
    smms_list = []
    base_date = datetime.now()
    
    for i in range(count):
        sec = random.choice(SECTIONS_GRAND_CHORD)
        dtype, sev, urg, amp, ir, desc = random.choice(catalog)
        line = random.choice([LineType.UP_MAIN, LineType.DOWN_MAIN])
        loc_km = round(random.uniform(sec["start_km"], sec["end_km"]), 2)
        det_date = (base_date - timedelta(days=random.randint(0, 4))).strftime("%Y-%m-%d")
        
        smms = SMMSDefect(
            id=f"SMMS-2026-{2000 + i}",
            section_id=sec["id"],
            station_from=sec["from"],
            station_to=sec["to"],
            line=line,
            location_km=loc_km,
            equipment_type=f"SNT_EQ_{sec['from']}_{random.randint(101, 299)}",
            defect_type=dtype,
            severity=sev,
            urgency_days_remaining=urg,
            operating_current_draw_amp=amp,
            insulation_resistance_megaohm=ir,
            detected_on=det_date,
            description=f"{desc} Location: KM {loc_km} ({sec['from']}-{sec['to']})."
        )
        smms_list.append(smms)
        
    return smms_list


def generate_tdms_defects(count: int = 28) -> List[TDMSDefect]:
    """Generates Traction Distribution Management System (TDMS) records"""
    catalog = [
        ("OHE_CONTACT_WIRE_CRITICAL_WEAR", Severity.CRITICAL, 2, 7.9, 32.0, "Contact wire diameter reduced to 7.9mm (Condemning limit 8.0mm). Contact wire splice insertion or replacement urgent."),
        ("HOTSPOT_FEEDER_JUMPER", Severity.EMERGENCY, 1, None, 92.5, "Thermovision camera revealed 92.5C hotspot at PG clamp (Ambient 34C). Immediate tightening/replacement required."),
        ("CANTILEVER_INSULATOR_FLASH_MARK", Severity.HIGH, 3, None, 40.0, "Heavy carbon flashover mark on 25kV composite stay-arm insulator. Megger test & replacement needed."),
        ("NEUTRAL_SECTION_ARCING", Severity.HIGH, 4, 9.1, 48.0, "PTFE neutral section short overlap showing severe electrical arc pitting. Overhaul with Tower Wagon needed."),
        ("TREE_BRANCH_25KV_INFRINGE", Severity.MEDIUM, 6, None, None, "Eucalyptus trees within 3.2m of live 25kV OHE feeder wire. Power block & trimming mandatory."),
        ("DROPPER_LOOSENESS_SAG", Severity.LOW, 14, 10.2, 30.0, "Catenary dropper loose at 4 consecutive mast spans. Tension check & re-sagging required."),
    ]
    
    tdms_list = []
    base_date = datetime.now()
    
    for i in range(count):
        sec = random.choice(SECTIONS_GRAND_CHORD)
        dtype, sev, urg, wear, temp, desc = random.choice(catalog)
        line = random.choice([LineType.UP_MAIN, LineType.DOWN_MAIN])
        start_km = round(random.uniform(sec["start_km"], sec["end_km"] - 3.0), 2)
        end_km = round(start_km + random.uniform(0.5, 3.0), 2)
        det_date = (base_date - timedelta(days=random.randint(0, 4))).strftime("%Y-%m-%d")
        
        tdms = TDMSDefect(
            id=f"TDMS-2026-{3000 + i}",
            section_id=sec["id"],
            station_from=sec["from"],
            station_to=sec["to"],
            line=line,
            start_km=start_km,
            end_km=end_km,
            equipment_type=f"TRD_OHE_MAST_{int(start_km * 25)}",
            defect_type=dtype,
            severity=sev,
            contact_wire_wear_mm=wear,
            hotspot_temp_celsius=temp,
            urgency_days_remaining=urg,
            detected_on=det_date,
            description=f"{desc} Sector: KM {start_km}-{end_km} on {line.value} between {sec['from']}-{sec['to']}."
        )
        tdms_list.append(tdms)
        
    return tdms_list


def generate_coa_trains_from_master() -> List[COATrainSchedule]:
    """Generates COA trains based on the official Indian Railways NTES Master Schedule"""
    coa_list = []
    
    for item in OFFICIAL_TRAIN_TIMETABLE_MASTER:
        # Build station timings dict
        timings = {}
        for h in item["halts"]:
            timings[h["stn"]] = {
                "arr": h["arr"],
                "dep": h["dep"],
                "halt": h["halt"],
                "pf": h["pf"],
                "km": h["km"]
            }
            
        coa = COATrainSchedule(
            train_number=item["train_no"],
            train_name=item["name"],
            train_type=item["type"],
            priority=item["priority"],
            direction=item["direction"],
            origin=item["origin"],
            destination=item["destination"],
            station_timings=timings,
            average_speed_kmph=item["speed"],
            delay_minutes=random.randint(0, 7),
            can_be_regulated_on_loop=item["priority"] > 2,
            max_acceptable_delay_min=item["max_delay_min"]
        )
        coa_list.append(coa)
        
    return coa_list


def generate_bdms_requisitions(tms: List[TMSDefect], smms: List[SMMSDefect], tdms: List[TDMSDefect]) -> List[BDMSRequisition]:
    """Generates BDMS departmental requisitions"""
    requisitions = []
    req_idx = 1
    
    # Engineering
    for t in tms[:14]:
        mtype = MachineType.CSM_TAMPER if "TGI" in t.defect_type else (
            MachineType.BCM_SCREENER if "SCREENING" in t.defect_type else (
                MachineType.UNIMAT_TURNOUT if "TURNOUT" in t.defect_type or "CROSSING" in t.defect_type else MachineType.NONE
            )
        )
        dur = 180 if mtype != MachineType.NONE else 90
        req = BDMSRequisition(
            id=f"BDMS-ENG-{5000 + req_idx}",
            department=Department.ENGINEERING,
            section_id=t.section_id,
            station_from=t.station_from,
            station_to=t.station_to,
            line=t.line,
            start_km=t.start_km,
            end_km=t.end_km,
            requested_duration_minutes=dur,
            earliest_preferred_date="2026-08-27",
            latest_permissible_date="2026-08-30",
            preferred_window_type="DAY_LIGHT" if mtype in [MachineType.BCM_SCREENER, MachineType.CSM_TAMPER] else "ANY",
            required_machine=mtype,
            manpower_gangs_required=3 if mtype != MachineType.NONE else 2,
            source_defect_id=t.id,
            justification=f"Requisition for track maintenance: {t.description}",
            status="PENDING"
        )
        requisitions.append(req)
        req_idx += 1
        
    # S&T
    for s in smms[:12]:
        dur = 120 if "POINT" in s.defect_type else 60
        req = BDMSRequisition(
            id=f"BDMS-SNT-{5000 + req_idx}",
            department=Department.SNT,
            section_id=s.section_id,
            station_from=s.station_from,
            station_to=s.station_to,
            line=s.line,
            start_km=s.location_km - 0.5,
            end_km=s.location_km + 0.5,
            requested_duration_minutes=dur,
            earliest_preferred_date="2026-08-27",
            latest_permissible_date="2026-08-29",
            preferred_window_type="ANY",
            required_machine=MachineType.NONE,
            manpower_gangs_required=1,
            source_defect_id=s.id,
            justification=f"Signal Disconnection requisition: {s.description}",
            status="PENDING"
        )
        requisitions.append(req)
        req_idx += 1
        
    # TRD
    for tr in tdms[:12]:
        dur = 150 if "CONTACT" in tr.defect_type or "NEUTRAL" in tr.defect_type else 90
        req = BDMSRequisition(
            id=f"BDMS-TRD-{5000 + req_idx}",
            department=Department.TRD,
            section_id=tr.section_id,
            station_from=tr.station_from,
            station_to=tr.station_to,
            line=tr.line,
            start_km=tr.start_km,
            end_km=tr.end_km,
            requested_duration_minutes=dur,
            earliest_preferred_date="2026-08-27",
            latest_permissible_date="2026-08-30",
            preferred_window_type="DAY_LIGHT",
            required_machine=MachineType.TOWER_WAGON,
            manpower_gangs_required=2,
            source_defect_id=tr.id,
            justification=f"25kV OHE Power Block requisition: {tr.description}",
            status="PENDING"
        )
        requisitions.append(req)
        req_idx += 1
        
    return requisitions


class DataStore:
    """Singleton in-memory data store holding all ingested feeds and plans"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataStore, cls).__new__(cls)
            cls._instance.initialize()
        return cls._instance
        
    def initialize(self):
        self.corridors = CORRIDORS
        self.stations = STATIONS_GRAND_CHORD
        self.sections = SECTIONS_GRAND_CHORD
        self.western_stations = STATIONS_WESTERN
        self.timetable_master = OFFICIAL_TRAIN_TIMETABLE_MASTER
        self.tms_defects = generate_tms_defects(32)
        self.smms_defects = generate_smms_defects(28)
        self.tdms_defects = generate_tdms_defects(28)
        self.coa_trains = generate_coa_trains_from_master()
        self.bdms_requisitions = generate_bdms_requisitions(self.tms_defects, self.smms_defects, self.tdms_defects)
        self.prioritized_tasks = []
        self.plans_by_horizon = {}
        self.last_optimized_timestamp = None
        self.simulation_history = []
