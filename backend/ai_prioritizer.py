"""
AI/ML Criticality, Urgency & Risk Scoring Engine for RailBlock AI
Evaluates Multi-Criteria Safety, Punctuality Impact, Asset Degradation, and Regulatory Compliance
"""

from typing import List
from datetime import datetime
from backend.models import (
    Department, Severity, LineType, MachineType, Horizon,
    TMSDefect, SMMSDefect, TDMSDefect, BDMSRequisition, PrioritizedTask
)


class AIPrioritizer:
    """
    AI Multi-Criteria Scoring & Ranking Engine for Railway Fixed Infrastructure Maintenance.
    Synthesizes diverse departmental failure modes into actionable, calibrated urgency scores.
    """
    
    @staticmethod
    def calculate_tms_scores(defect: TMSDefect) -> dict:
        # Safety Risk Index
        sri_base = {
            Severity.EMERGENCY: 96.0,
            Severity.CRITICAL: 82.0,
            Severity.HIGH: 68.0,
            Severity.MEDIUM: 45.0,
            Severity.LOW: 25.0
        }[defect.severity]
        
        # Additional risk if gross million tonnes (GMT) is high (heavy axle load)
        gmt_factor = min(15.0, (defect.gross_million_tonnes / 80.0) * 15.0)
        sri = min(100.0, sri_base + gmt_factor)
        
        # Punctuality Impact Index (Calculated from speed restriction if deferred)
        if defect.speed_restriction_if_deferred_kmph is not None:
            # Slower speed restriction = higher punctuality penalty
            pii = max(20.0, 100.0 - (defect.speed_restriction_if_deferred_kmph * 0.9))
        else:
            pii = 35.0
            
        # Asset Degradation Velocity
        if "IMR" in defect.defect_type:
            advs = 95.0
        elif "TGI" in defect.defect_type:
            advs = 80.0
        elif "TURNOUT" in defect.defect_type:
            advs = 70.0
        else:
            advs = 40.0
            
        # Regulatory Urgency Score
        days = defect.urgency_days_remaining
        rus = max(10.0, 100.0 - (days * 12.0))
        
        return {
            "sri": round(sri, 1),
            "pii": round(pii, 1),
            "advs": round(advs, 1),
            "rus": round(rus, 1),
        }

    @staticmethod
    def calculate_smms_scores(defect: SMMSDefect) -> dict:
        sri_base = {
            Severity.EMERGENCY: 95.0,
            Severity.CRITICAL: 85.0,
            Severity.HIGH: 65.0,
            Severity.MEDIUM: 40.0,
            Severity.LOW: 20.0
        }[defect.severity]
        
        # Electrical signature anomaly penalty
        current_factor = 0.0
        if defect.operating_current_draw_amp and defect.operating_current_draw_amp > 4.5:
            current_factor = min(12.0, (defect.operating_current_draw_amp - 3.2) * 5.0)
            
        sri = min(100.0, sri_base + current_factor)
        
        # S&T failure often causes complete signal red / route failure -> severe punctuality loss
        pii = 90.0 if defect.severity in [Severity.EMERGENCY, Severity.CRITICAL] else 60.0
        
        # Degradation score
        advs = 88.0 if "POINT" in defect.defect_type or "MSDAC" in defect.defect_type else 55.0
        
        # Regulatory Urgency
        days = defect.urgency_days_remaining
        rus = max(10.0, 100.0 - (days * 15.0))
        
        return {
            "sri": round(sri, 1),
            "pii": round(pii, 1),
            "advs": round(advs, 1),
            "rus": round(rus, 1),
        }

    @staticmethod
    def calculate_tdms_scores(defect: TDMSDefect) -> dict:
        sri_base = {
            Severity.EMERGENCY: 98.0,  # 25kV OHE parting / dewirement risk
            Severity.CRITICAL: 84.0,
            Severity.HIGH: 65.0,
            Severity.MEDIUM: 42.0,
            Severity.LOW: 20.0
        }[defect.severity]
        
        temp_factor = 0.0
        if defect.hotspot_temp_celsius and defect.hotspot_temp_celsius > 75.0:
            temp_factor = 12.0
            
        sri = min(100.0, sri_base + temp_factor)
        
        # OHE power trip stops all electric locomotives on the entire section
        pii = 92.0 if defect.severity in [Severity.EMERGENCY, Severity.CRITICAL] else 50.0
        
        # Degradation: wire wear close to 8.0mm condemning limit
        if defect.contact_wire_wear_mm and defect.contact_wire_wear_mm <= 8.2:
            advs = 94.0
        else:
            advs = 60.0
            
        days = defect.urgency_days_remaining
        rus = max(10.0, 100.0 - (days * 12.0))
        
        return {
            "sri": round(sri, 1),
            "pii": round(pii, 1),
            "advs": round(advs, 1),
            "rus": round(rus, 1),
        }

    @classmethod
    def prioritize_all_feeds(
        cls,
        tms_defects: List[TMSDefect],
        smms_defects: List[SMMSDefect],
        tdms_defects: List[TDMSDefect],
        bdms_reqs: List[BDMSRequisition]
    ) -> List[PrioritizedTask]:
        """
        Unifies and ranks all maintenance demands using multi-objective AI scoring.
        """
        tasks: List[PrioritizedTask] = []
        req_map = {r.source_defect_id: r for r in bdms_reqs if r.source_defect_id}
        
        # 1. Process TMS Engineering defects
        for tms in tms_defects:
            scores = cls.calculate_tms_scores(tms)
            ccs = round(0.35 * scores["sri"] + 0.25 * scores["pii"] + 0.20 * scores["advs"] + 0.20 * scores["rus"], 1)
            
            # Determine horizon
            if ccs >= 75.0 or tms.severity == Severity.EMERGENCY or tms.urgency_days_remaining <= 2:
                horizon = Horizon.DAILY
            elif ccs >= 50.0 or tms.urgency_days_remaining <= 7:
                horizon = Horizon.WEEKLY
            else:
                horizon = Horizon.MONTHLY
                
            req = req_map.get(tms.id)
            machine = req.required_machine if req else (
                MachineType.CSM_TAMPER if "TGI" in tms.defect_type else (
                    MachineType.BCM_SCREENER if "SCREENING" in tms.defect_type else MachineType.NONE
                )
            )
            duration = req.requested_duration_minutes if req else (180 if machine != MachineType.NONE else 90)
            gangs = req.manpower_gangs_required if req else (3 if machine != MachineType.NONE else 2)
            
            task = PrioritizedTask(
                task_id=f"TASK-ENG-{tms.id.split('-')[-1]}",
                department=Department.ENGINEERING,
                defect_id=tms.id,
                requisition_id=req.id if req else None,
                section_id=tms.section_id,
                station_from=tms.station_from,
                station_to=tms.station_to,
                line=tms.line,
                start_km=tms.start_km,
                end_km=tms.end_km,
                title=f"Track Maintenance: {tms.defect_type.replace('_', ' ').title()}",
                description=tms.description,
                severity=tms.severity,
                required_duration_minutes=duration,
                required_machine=machine,
                manpower_gangs=gangs,
                safety_risk_index=scores["sri"],
                punctuality_impact_index=scores["pii"],
                asset_degradation_score=scores["advs"],
                regulatory_urgency_score=scores["rus"],
                composite_criticality_score=ccs,
                recommended_horizon=horizon,
                can_be_shadow_bundled=True
            )
            tasks.append(task)
            
        # 2. Process SMMS S&T defects
        for smms in smms_defects:
            scores = cls.calculate_smms_scores(smms)
            ccs = round(0.35 * scores["sri"] + 0.25 * scores["pii"] + 0.20 * scores["advs"] + 0.20 * scores["rus"], 1)
            
            if ccs >= 75.0 or smms.severity == Severity.EMERGENCY or smms.urgency_days_remaining <= 2:
                horizon = Horizon.DAILY
            elif ccs >= 50.0 or smms.urgency_days_remaining <= 7:
                horizon = Horizon.WEEKLY
            else:
                horizon = Horizon.MONTHLY
                
            req = req_map.get(smms.id)
            duration = req.requested_duration_minutes if req else 90
            
            task = PrioritizedTask(
                task_id=f"TASK-SNT-{smms.id.split('-')[-1]}",
                department=Department.SNT,
                defect_id=smms.id,
                requisition_id=req.id if req else None,
                section_id=smms.section_id,
                station_from=smms.station_from,
                station_to=smms.station_to,
                line=smms.line,
                start_km=round(smms.location_km - 0.5, 2),
                end_km=round(smms.location_km + 0.5, 2),
                title=f"Signalling Disconnection: {smms.defect_type.replace('_', ' ').title()}",
                description=smms.description,
                severity=smms.severity,
                required_duration_minutes=duration,
                required_machine=MachineType.NONE,
                manpower_gangs=1,
                safety_risk_index=scores["sri"],
                punctuality_impact_index=scores["pii"],
                asset_degradation_score=scores["advs"],
                regulatory_urgency_score=scores["rus"],
                composite_criticality_score=ccs,
                recommended_horizon=horizon,
                can_be_shadow_bundled=True
            )
            tasks.append(task)
            
        # 3. Process TDMS Traction defects
        for tdms in tdms_defects:
            scores = cls.calculate_tdms_scores(tdms)
            ccs = round(0.35 * scores["sri"] + 0.25 * scores["pii"] + 0.20 * scores["advs"] + 0.20 * scores["rus"], 1)
            
            if ccs >= 75.0 or tdms.severity == Severity.EMERGENCY or tdms.urgency_days_remaining <= 2:
                horizon = Horizon.DAILY
            elif ccs >= 50.0 or tdms.urgency_days_remaining <= 7:
                horizon = Horizon.WEEKLY
            else:
                horizon = Horizon.MONTHLY
                
            req = req_map.get(tdms.id)
            duration = req.requested_duration_minutes if req else 120
            
            task = PrioritizedTask(
                task_id=f"TASK-TRD-{tdms.id.split('-')[-1]}",
                department=Department.TRD,
                defect_id=tdms.id,
                requisition_id=req.id if req else None,
                section_id=tdms.section_id,
                station_from=tdms.station_from,
                station_to=tdms.station_to,
                line=tdms.line,
                start_km=tdms.start_km,
                end_km=tdms.end_km,
                title=f"25kV OHE Power Block: {tdms.defect_type.replace('_', ' ').title()}",
                description=tdms.description,
                severity=tdms.severity,
                required_duration_minutes=duration,
                required_machine=MachineType.TOWER_WAGON,
                manpower_gangs=2,
                safety_risk_index=scores["sri"],
                punctuality_impact_index=scores["pii"],
                asset_degradation_score=scores["advs"],
                regulatory_urgency_score=scores["rus"],
                composite_criticality_score=ccs,
                recommended_horizon=horizon,
                can_be_shadow_bundled=True
            )
            tasks.append(task)
            
        # Sort globally by composite criticality score descending (Highest priority first)
        tasks.sort(key=lambda t: t.composite_criticality_score, reverse=True)
        return tasks
