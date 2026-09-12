"""
Authentication & Role-Based Access Control (RBAC) for RailBlock AI
Supports Indian Railways Official Logins (Operating, Engineering, S&T, TRD, DRM)
"""

import uuid
from typing import Dict, Optional
from pydantic import BaseModel
from backend.models import Department


class UserRole(str):
    OPERATING = "OPERATING"        # Sr. DOM / Section Controller (Block Sanctions)
    ENGINEERING = "ENGINEERING"    # Sr. DEN / SSE P-Way (Track Demands)
    SNT = "SNT"                    # Sr. DSTE / SSE Signal (Signal Demands)
    TRD = "TRD"                    # Sr. DEE / SSE Traction (OHE Demands)
    EXECUTIVE = "EXECUTIVE"        # DRM / AGM / GM (Master Overview)


class UserProfile(BaseModel):
    username: str
    name: str
    designation: str
    department: Department
    role: str
    division: str = "Prayagraj (PRYJ)"
    zone: str = "North Central Railway (NCR)"
    avatar_color: str = "#f5a623"


# Pre-configured Indian Railways official accounts
OFFICIAL_ACCOUNTS: Dict[str, dict] = {
    "operating": {
        "password": "rail123",
        "profile": UserProfile(
            username="operating",
            name="Rajesh Sharma",
            designation="Sr. Divisional Operations Manager (Sr. DOM)",
            department=Department.OPERATING,
            role="OPERATING",
            division="Prayagraj (PRYJ)",
            zone="North Central Railway (NCR)",
            avatar_color="#10b981"
        )
    },
    "engineering": {
        "password": "rail123",
        "profile": UserProfile(
            username="engineering",
            name="Amit Verma",
            designation="Sr. Divisional Engineer / Co-ord (Sr. DEN)",
            department=Department.ENGINEERING,
            role="ENGINEERING",
            division="Prayagraj (PRYJ)",
            zone="North Central Railway (NCR)",
            avatar_color="#38bdf8"
        )
    },
    "signalling": {
        "password": "rail123",
        "profile": UserProfile(
            username="signalling",
            name="Sunil Gupta",
            designation="Sr. Divisional Signal & Telecom Engineer (Sr. DSTE)",
            department=Department.SNT,
            role="SNT",
            division="Prayagraj (PRYJ)",
            zone="North Central Railway (NCR)",
            avatar_color="#c084fc"
        )
    },
    "traction": {
        "password": "rail123",
        "profile": UserProfile(
            username="traction",
            name="Pooja Singh",
            designation="Sr. Divisional Electrical Engineer (Sr. DEE / TRD)",
            department=Department.TRD,
            role="TRD",
            division="Prayagraj (PRYJ)",
            zone="North Central Railway (NCR)",
            avatar_color="#f5a623"
        )
    },
    "admin": {
        "password": "admin123",
        "profile": UserProfile(
            username="admin",
            name="Vikas Meena, IRTS",
            designation="Divisional Railway Manager (DRM)",
            department=Department.OPERATING,
            role="EXECUTIVE",
            division="Prayagraj (PRYJ)",
            zone="North Central Railway (NCR)",
            avatar_color="#ef4444"
        )
    }
}

# Active Session Tokens
ACTIVE_SESSIONS: Dict[str, UserProfile] = {}


class AuthManager:
    @staticmethod
    def authenticate(username: str, password: str) -> Optional[tuple[str, UserProfile]]:
        user_entry = OFFICIAL_ACCOUNTS.get(username.lower().strip())
        if user_entry and user_entry["password"] == password:
            token = f"ir-token-{uuid.uuid4().hex}"
            ACTIVE_SESSIONS[token] = user_entry["profile"]
            return token, user_entry["profile"]
        return None

    @staticmethod
    def get_user_by_token(token: str) -> Optional[UserProfile]:
        return ACTIVE_SESSIONS.get(token)

    @staticmethod
    def logout(token: str) -> bool:
        if token in ACTIVE_SESSIONS:
            del ACTIVE_SESSIONS[token]
            return True
        return False
