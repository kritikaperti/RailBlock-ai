"""
Indian Railways Official Joint Block Sanction Memo & Circular Generator
Formats Official Form B Disconnection Memos & Corridor Coordination Directives
"""

from typing import Dict, Any
from datetime import datetime
from backend.models import OptimizedBlock, Horizon


class ReportGenerator:
    """
    Generates official Indian Railways Joint Block Sanction Memos and Operational Circulars.
    """
    
    @staticmethod
    def generate_form_b_memo(block: OptimizedBlock) -> Dict[str, Any]:
        """
        Generates standard Indian Railways 'Form B' Joint Block Sanction Memo.
        Signed jointly by Operating (Sr. DOM), Engineering (Sr. DEN), S&T (Sr. DSTE), and TRD (Sr. DEE).
        """
        bundled_details = []
        for i, task in enumerate(block.bundled_tasks, 1):
            bundled_details.append({
                "sl_no": i,
                "dept": task.department.value,
                "task_id": task.task_id,
                "title": task.title,
                "machine": task.required_machine.value if hasattr(task.required_machine, 'value') else str(task.required_machine),
                "gangs": task.manpower_gangs,
                "scope": task.work_scope
            })
            
        memo = {
            "memo_number": block.disconnection_notice_number,
            "railway_zone": "NORTH CENTRAL RAILWAY (NCR)",
            "division": "PRAYAGRAJ (PRYJ) DIVISION",
            "subject": f"JOINT INTEGRATED CORRIDOR BLOCK SANCTION CIRCULAR ({block.plan_horizon.value})",
            "date_of_issue": block.date,
            "section": f"{block.station_from} - {block.station_to} ({block.section_id})",
            "line_affected": block.line.value,
            "location_km": f"KM {block.start_km} to KM {block.end_km}",
            "block_timing": {
                "start_time": block.start_time,
                "end_time": block.end_time,
                "duration_minutes": block.duration_minutes,
                "duration_hours": round(block.duration_minutes / 60.0, 2)
            },
            "primary_department": block.primary_department.value,
            "participating_departments": [d.value for d in block.participating_departments],
            "is_integrated_mega_block": block.is_integrated_mega_block,
            "shadow_coordination_gain": f"{block.coordination_efficiency_gain_pct}%",
            "allocated_heavy_machines": [m.value if hasattr(m, 'value') else str(m) for m in block.allocated_machines],
            "bundled_departmental_works": bundled_details,
            "train_regulation_instructions": {
                "total_impacted_trains": block.impacted_trains_count,
                "total_delay_minutes": block.total_train_delay_minutes,
                "regulated_trains": block.regulated_trains,
                "diverted_freight": block.diverted_trains,
                "passenger_cancellations": block.cancellations_count,
                "safety_interlock_buffer": f"{block.safety_margin_minutes} minutes"
            },
            "safety_certifications": [
                "Track fit certificate to be issued by Section Engineer (P-Way) prior to cancellation.",
                "S&T fail-safe test to be logged by Section Engineer (Signal) before reconnecting EI route.",
                "25kV OHE power permit (PTW) to be cleared & earth discharges removed by Traction Foreman."
            ],
            "joint_signatories": [
                {"role": "Senior Divisional Operations Manager (Sr. DOM)", "status": "APPROVED / DISPATCHED TO COA"},
                {"role": "Senior Divisional Engineer (Sr. DEN / Co-ord)", "status": "COORDINATED VIA TMS"},
                {"role": "Senior Divisional Signal & Telecom Engineer (Sr. DSTE)", "status": "INTEGRATED VIA SMMS"},
                {"role": "Senior Divisional Electrical Engineer (Sr. DEE / TRD)", "status": "POWER PERMIT SANCTIONED"}
            ],
            "status": block.sanction_status,
            "remarks": block.remarks
        }
        return memo
