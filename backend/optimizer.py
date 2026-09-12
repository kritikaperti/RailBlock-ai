"""
Integrated Multi-Department Corridor Block Co-Optimizer
Solves the Joint Shadow-Blocking, Machine Scheduling & Train Delay Minimization Problem
"""

from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
import math
from backend.models import (
    Department, Severity, LineType, MachineType, Horizon,
    PrioritizedTask, COATrainSchedule, OptimizedBlock, BundledDepartmentTask
)


class BlockOptimizer:
    """
    Multi-Department Shadow Block Co-Optimization Solver.
    Maximizes asset availability by bundling Engineering, S&T, and TRD tasks
    into optimized traffic headway windows with minimal train delay.
    """
    
    @staticmethod
    def _parse_time_to_minutes(timestr: str) -> int:
        """Converts 'HH:MM' string to minutes from midnight"""
        h, m = map(int, timestr.split(":"))
        return h * 60 + m

    @staticmethod
    def _minutes_to_timestr(minutes: int) -> str:
        """Converts minutes from midnight to 'HH:MM' string"""
        minutes = minutes % (24 * 60)
        h = minutes // 60
        m = minutes % 60
        return f"{h:02d}:{m:02d}"

    @classmethod
    def find_traffic_windows_for_section(
        cls,
        section_id: str,
        line: LineType,
        station_from: str,
        station_to: str,
        trains: List[COATrainSchedule],
        target_duration_min: int = 150
    ) -> List[Dict]:
        """
        Finds open train headway windows on a specific section and line.
        """
        direction = "DOWN" if line in [LineType.DOWN_MAIN] else "UP"
        
        # Collect train occupation intervals on this section
        occupations = []
        for train in trains:
            # Check if train runs on this section in this direction
            if train.direction == direction:
                timings = train.station_timings
                if station_from in timings and station_to in timings:
                    t1 = cls._parse_time_to_minutes(timings[station_from]["dep"])
                    t2 = cls._parse_time_to_minutes(timings[station_to]["arr"])
                    start = min(t1, t2)
                    end = max(t1, t2)
                    occupations.append({
                        "train_no": train.train_number,
                        "priority": train.priority,
                        "start": start,
                        "end": end + 10 # 10 min signaling buffer
                    })
                    
        occupations.sort(key=lambda x: x["start"])
        
        # Identify gaps throughout the 24h cycle
        candidate_windows = []
        
        # Primary standard Indian Railways corridor block windows:
        # Window 1: Early morning night mega block (00:30 to 05:00) -> 270 mins
        # Window 2: Afternoon maintenance corridor (11:30 to 15:30) -> 240 mins
        # Window 3: Late evening secondary (20:00 to 22:30) -> 150 mins
        
        predefined_slots = [
            {"name": "NIGHT_MEGA_BLOCK", "start": 60, "end": 270},    # 01:00 to 04:30
            {"name": "DAY_CORRIDOR_SLOT", "start": 700, "end": 910},   # 11:40 to 15:10
            {"name": "TWILIGHT_WINDOW", "start": 1200, "end": 1350},  # 20:00 to 22:30
            {"name": "MORNING_OFFPEAK", "start": 480, "end": 630},    # 08:00 to 10:30
        ]
        
        for slot in predefined_slots:
            slot_start = slot["start"]
            slot_end = slot["end"]
            slot_dur = slot_end - slot_start
            
            # Count trains during this slot
            conflicting_trains = []
            for occ in occupations:
                if not (occ["end"] <= slot_start or occ["start"] >= slot_end):
                    conflicting_trains.append(occ)
                    
            # Calculate impact score
            impact_score = sum(10 - min(c["priority"], 9) for c in conflicting_trains)
            
            candidate_windows.append({
                "slot_name": slot["name"],
                "start_min": slot_start,
                "end_min": slot_end,
                "duration_min": slot_dur,
                "start_time": cls._minutes_to_timestr(slot_start),
                "end_time": cls._minutes_to_timestr(slot_end),
                "conflicting_trains": conflicting_trains,
                "impact_score": impact_score
            })
            
        # Sort by least impact score
        candidate_windows.sort(key=lambda w: w["impact_score"])
        return candidate_windows

    @classmethod
    def optimize_horizon_schedule(
        cls,
        tasks: List[PrioritizedTask],
        trains: List[COATrainSchedule],
        target_horizon: Horizon,
        plan_date: str = "2026-08-27"
    ) -> List[OptimizedBlock]:
        """
        Executes multi-department shadow block co-optimization for a given planning horizon.
        """
        # Filter tasks matching this horizon (or high urgency tasks rolled over)
        if target_horizon == Horizon.DAILY:
            horizon_tasks = [t for t in tasks if t.recommended_horizon == Horizon.DAILY or t.composite_criticality_score >= 70.0]
        elif target_horizon == Horizon.WEEKLY:
            horizon_tasks = [t for t in tasks if t.recommended_horizon in [Horizon.DAILY, Horizon.WEEKLY]]
        else: # MONTHLY
            horizon_tasks = tasks
            
        scheduled_blocks: List[OptimizedBlock] = []
        assigned_task_ids = set()
        machine_usage_timeline: Dict[MachineType, List[Tuple[int, int, str]]] = {m: [] for m in MachineType}
        block_counter = 1
        
        # Spatial grouping for Shadow Blocking: (section_id, line)
        tasks_by_section_line: Dict[Tuple[str, LineType], List[PrioritizedTask]] = {}
        for t in horizon_tasks:
            key = (t.section_id, t.line)
            if key not in tasks_by_section_line:
                tasks_by_section_line[key] = []
            tasks_by_section_line[key].append(t)
            
        # Iterate over section-line groupings to create co-scheduled Integrated Mega Blocks
        for (sec_id, line), group in tasks_by_section_line.items():
            # Sort group tasks by criticality
            group.sort(key=lambda t: t.composite_criticality_score, reverse=True)
            
            for primary_task in group:
                if primary_task.task_id in assigned_task_ids:
                    continue
                    
                # Find best traffic window
                candidate_windows = cls.find_traffic_windows_for_section(
                    section_id=sec_id,
                    line=line,
                    station_from=primary_task.station_from,
                    station_to=primary_task.station_to,
                    trains=trains,
                    target_duration_min=primary_task.required_duration_minutes
                )
                
                if not candidate_windows:
                    continue
                    
                chosen_window = candidate_windows[0]
                
                # Check machine conflict if primary task needs a machine
                if primary_task.required_machine != MachineType.NONE:
                    m_type = primary_task.required_machine
                    conflict = False
                    for (m_start, m_end, m_sec) in machine_usage_timeline[m_type]:
                        if not (chosen_window["end_min"] <= m_start or chosen_window["start_min"] >= m_end):
                            conflict = True
                            break
                    if conflict:
                        # Try next available window
                        if len(candidate_windows) > 1:
                            chosen_window = candidate_windows[1]
                            
                # Primary department and machines
                primary_dept = primary_task.department
                allocated_machines = [primary_task.required_machine] if primary_task.required_machine != MachineType.NONE else []
                
                # SHADOW BLOCKING: Find complementary tasks from other departments in the same section
                bundled_tasks: List[BundledDepartmentTask] = [
                    BundledDepartmentTask(
                        department=primary_task.department,
                        task_id=primary_task.task_id,
                        title=primary_task.title,
                        required_machine=primary_task.required_machine,
                        manpower_gangs=primary_task.manpower_gangs,
                        work_scope=primary_task.description
                    )
                ]
                assigned_task_ids.add(primary_task.task_id)
                participating_depts = {primary_task.department}
                
                # Search for co-locatable tasks in the same section & line
                for other_task in group:
                    if other_task.task_id in assigned_task_ids:
                        continue
                    if not other_task.can_be_shadow_bundled:
                        continue
                        
                    # Bundle if spatial overlap and duration fits within block
                    if abs(other_task.start_km - primary_task.start_km) <= 15.0: # Within 15 km
                        if other_task.required_duration_minutes <= chosen_window["duration_min"]:
                            bundled_tasks.append(
                                BundledDepartmentTask(
                                    department=other_task.department,
                                    task_id=other_task.task_id,
                                    title=other_task.title,
                                    required_machine=other_task.required_machine,
                                    manpower_gangs=other_task.manpower_gangs,
                                    work_scope=other_task.description
                                )
                            )
                            assigned_task_ids.add(other_task.task_id)
                            participating_depts.add(other_task.department)
                            if other_task.required_machine != MachineType.NONE and other_task.required_machine not in allocated_machines:
                                allocated_machines.append(other_task.required_machine)
                                
                # Calculate coordination efficiency gain
                standalone_time = sum(
                    t.required_duration_minutes for t in horizon_tasks if t.task_id in [b.task_id for b in bundled_tasks]
                )
                actual_block_time = chosen_window["duration_min"]
                eff_gain = round(max(0.0, ((standalone_time - actual_block_time) / max(1, standalone_time)) * 100), 1)
                
                # Calculate train regulation impact
                regulated = []
                diverted = []
                total_delay = 0
                for ct in chosen_window["conflicting_trains"]:
                    t_obj = next((tr for tr in trains if tr.train_number == ct["train_no"]), None)
                    if t_obj:
                        if t_obj.priority <= 2: # Premium (Vande Bharat / Rajdhani) -> Divert / Minimum Delay
                            total_delay += min(8, t_obj.delay_minutes + 5)
                            regulated.append(f"{t_obj.train_number} ({t_obj.train_name}) [Priority Clearance: +5m]")
                        elif t_obj.priority <= 4: # Express / Passenger -> Regulate on loop
                            total_delay += min(20, t_obj.max_acceptable_delay_min)
                            regulated.append(f"{t_obj.train_number} ({t_obj.train_name}) [Loop Regulated: +15m]")
                        else: # Freight -> Hold / Reversible single line
                            total_delay += 30
                            diverted.append(f"{t_obj.train_number} ({t_obj.train_name}) [Freight Path Held: +30m]")
                            
                # Record machine occupancy
                for m in allocated_machines:
                    if m != MachineType.NONE:
                        machine_usage_timeline[m].append((chosen_window["start_min"], chosen_window["end_min"], sec_id))
                        
                is_mega = len(participating_depts) > 1 or len(bundled_tasks) > 1
                discon_no = f"IR-NCR-ABPS-{target_horizon.value[:3]}-{plan_date.replace('-', '')}-{block_counter:03d}"
                
                opt_block = OptimizedBlock(
                    block_id=f"BLK-{target_horizon.value[:3]}-{block_counter:03d}",
                    plan_horizon=target_horizon,
                    date=plan_date,
                    station_from=primary_task.station_from,
                    station_to=primary_task.station_to,
                    section_id=sec_id,
                    line=line,
                    start_km=min(t.start_km for t in group if t.task_id in assigned_task_ids),
                    end_km=max(t.end_km for t in group if t.task_id in assigned_task_ids),
                    start_time=chosen_window["start_time"],
                    end_time=chosen_window["end_time"],
                    duration_minutes=chosen_window["duration_min"],
                    primary_department=primary_dept,
                    allocated_machines=allocated_machines,
                    is_integrated_mega_block=is_mega,
                    participating_departments=list(participating_depts),
                    bundled_tasks=bundled_tasks,
                    coordination_efficiency_gain_pct=eff_gain,
                    impacted_trains_count=len(chosen_window["conflicting_trains"]),
                    total_train_delay_minutes=total_delay,
                    regulated_trains=regulated,
                    diverted_trains=diverted,
                    cancellations_count=0,
                    safety_margin_minutes=15,
                    disconnection_notice_number=discon_no,
                    sanction_status="SANCTIONED",
                    remarks=f"Integrated Block: {len(participating_depts)} depts co-working ({', '.join([d.value for d in participating_depts])}). Shadow gain: {eff_gain}%."
                )
                scheduled_blocks.append(opt_block)
                block_counter += 1
                
        return scheduled_blocks
