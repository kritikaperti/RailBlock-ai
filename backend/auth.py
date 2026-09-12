"""
Authentication & Role-Based Access Control (RBAC) for RailBlock AI
Supports Separate Registration & Login for:
1. Train Passengers / Citizens (Simple: Name, Username, Password, Email - No Department/Designation)
2. Railway Employees & Officers (Official: Employee ID, Department, Designation, Division)
"""

import uuid
from typing import Dict, Optional, List
from pydantic import BaseModel
from backend.models import Department


class UserProfile(BaseModel):
    username: str
    name: str
    user_type: str = "PASSENGER"  # PASSENGER or EMPLOYEE
    email: Optional[str] = "user@railnet.gov.in"
    phone: Optional[str] = None
    designation: Optional[str] = "Train Passenger"
    department: Optional[Department] = None
    role: str = "PASSENGER"
    division: Optional[str] = "All Divisions"
    zone: Optional[str] = "Indian Railways"
    avatar_color: str = "#f5a623"


class RegisterRequest(BaseModel):
    user_type: str = "PASSENGER"  # PASSENGER or EMPLOYEE
    username: str
    password: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[Department] = None
    division: Optional[str] = None
    zone: Optional[str] = None


# Pre-configured Indian Railways official accounts
DEFAULT_ACCOUNTS: Dict[str, dict] = {
    "operating": {
        "password": "rail123",
        "profile": UserProfile(
            username="operating",
            name="Rajesh Sharma",
            user_type="EMPLOYEE",
            email="rajesh.sharma@ncr.railnet.gov.in",
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
            user_type="EMPLOYEE",
            email="amit.verma@ncr.railnet.gov.in",
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
            user_type="EMPLOYEE",
            email="sunil.gupta@ncr.railnet.gov.in",
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
            user_type="EMPLOYEE",
            email="pooja.singh@ncr.railnet.gov.in",
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
            user_type="EMPLOYEE",
            email="drm.pryj@ncr.railnet.gov.in",
            designation="Divisional Railway Manager (DRM)",
            department=Department.OPERATING,
            role="EXECUTIVE",
            division="Prayagraj (PRYJ)",
            zone="North Central Railway (NCR)",
            avatar_color="#ef4444"
        )
    },
    # Sample Passenger Account
    "passenger": {
        "password": "pass123",
        "profile": UserProfile(
            username="passenger",
            name="Rahul Mehra",
            user_type="PASSENGER",
            email="rahul.mehra@gmail.com",
            designation="Train Passenger",
            department=None,
            role="PASSENGER",
            division="All Routes",
            zone="Indian Railways",
            avatar_color="#06b6d4"
        )
    }
}

# Runtime In-Memory Accounts & Sessions
OFFICIAL_ACCOUNTS: Dict[str, dict] = dict(DEFAULT_ACCOUNTS)
ACTIVE_SESSIONS: Dict[str, UserProfile] = {}


class AuthManager:
    """Authentication and User Persistence Manager"""

    @classmethod
    def authenticate(cls, username: str, password: str) -> Optional[tuple[str, UserProfile]]:
        u_key = username.lower().strip()
        user_entry = OFFICIAL_ACCOUNTS.get(u_key)
        if user_entry and user_entry["password"] == password:
            token = f"ir-token-{uuid.uuid4().hex}"
            ACTIVE_SESSIONS[token] = user_entry["profile"]
            return token, user_entry["profile"]
        return None

    @classmethod
    def register_user(cls, req: RegisterRequest) -> tuple[str, UserProfile]:
        u_key = req.username.lower().strip()
        if u_key in OFFICIAL_ACCOUNTS:
            raise ValueError(f"Username '{req.username}' is already taken. Please choose another username or sign in.")

        is_employee = req.user_type.upper() == "EMPLOYEE"

        colors = ["#10b981", "#38bdf8", "#c084fc", "#f5a623", "#f43f5e", "#06b6d4", "#ec4899"]
        avatar_color = colors[len(OFFICIAL_ACCOUNTS) % len(colors)]

        if is_employee:
            profile = UserProfile(
                username=u_key,
                name=req.name.strip(),
                user_type="EMPLOYEE",
                email=req.email or f"{u_key}@railnet.gov.in",
                phone=req.phone,
                designation=req.designation.strip() if req.designation else "Railway Officer",
                department=req.department or Department.OPERATING,
                role=req.department.value if req.department else "OPERATING",
                division=req.division or "Prayagraj (PRYJ)",
                zone=req.zone or "North Central Railway (NCR)",
                avatar_color=avatar_color
            )
        else:
            # TRAIN PASSENGER / CITIZEN (No department, No employee designation)
            profile = UserProfile(
                username=u_key,
                name=req.name.strip(),
                user_type="PASSENGER",
                email=req.email or f"{u_key}@gmail.com",
                phone=req.phone,
                designation="Train Passenger",
                department=None,
                role="PASSENGER",
                division="All Routes",
                zone="Indian Railways",
                avatar_color=avatar_color
            )

        OFFICIAL_ACCOUNTS[u_key] = {
            "password": req.password,
            "profile": profile
        }

        token = f"ir-token-{uuid.uuid4().hex}"
        ACTIVE_SESSIONS[token] = profile
        return token, profile

    @classmethod
    def get_user_by_token(cls, token: str) -> Optional[UserProfile]:
        return ACTIVE_SESSIONS.get(token)

    @classmethod
    def list_users(cls) -> List[UserProfile]:
        return [acc["profile"] for acc in OFFICIAL_ACCOUNTS.values()]

    @classmethod
    def logout(cls, token: str) -> bool:
        if token in ACTIVE_SESSIONS:
            del ACTIVE_SESSIONS[token]
            return True
        return False
