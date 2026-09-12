"""
Automated Test Suite for RailBlock AI (IR-ABPS)
Validates Data Generation, AI Prioritization, Optimizer, Multi-Horizon Plans, and Simulator
"""

import unittest
from backend.models import (
    Department, Severity, LineType, MachineType, Horizon,
    WhatIfScenarioType, WhatIfScenarioRequest
)
from backend.data_generator import DataStore
from backend.ai_prioritizer import AIPrioritizer
from backend.optimizer import BlockOptimizer
from backend.multi_horizon_planner import MultiHorizonPlanner
from backend.simulator import WhatIfSimulator
from backend.report_generator import ReportGenerator


class TestRailBlockAI(unittest.TestCase):
    
    def setUp(self):
        self.store = DataStore()
        self.store.initialize()

    def test_data_ingestion_and_feeds(self):
        """Test multi-source data generation from TMS, SMMS, TDMS, COA, BDMS"""
        self.assertGreaterEqual(len(self.store.tms_defects), 20)
        self.assertGreaterEqual(len(self.store.smms_defects), 20)
        self.assertGreaterEqual(len(self.store.tdms_defects), 20)
        self.assertGreaterEqual(len(self.store.coa_trains), 15)
        self.assertGreaterEqual(len(self.store.bdms_requisitions), 15)
        
        # Verify TMS defects structure
        tms0 = self.store.tms_defects[0]
        self.assertTrue(tms0.id.startswith("TMS-2026-"))
        self.assertIn(tms0.severity, list(Severity))
        self.assertGreater(tms0.end_km, tms0.start_km)

    def test_ai_prioritization_engine(self):
        """Test multi-criteria scoring and composite criticality score ranking"""
        tasks = AIPrioritizer.prioritize_all_feeds(
            tms_defects=self.store.tms_defects,
            smms_defects=self.store.smms_defects,
            tdms_defects=self.store.tdms_defects,
            bdms_reqs=self.store.bdms_requisitions
        )
        self.assertGreater(len(tasks), 50)
        
        # Check sorted order (descending criticality score)
        for i in range(len(tasks) - 1):
            self.assertGreaterEqual(
                tasks[i].composite_criticality_score,
                tasks[i+1].composite_criticality_score,
                "Tasks must be strictly ordered by composite criticality score descending"
            )
            
        # Verify score ranges
        for t in tasks:
            self.assertTrue(0 <= t.safety_risk_index <= 100)
            self.assertTrue(0 <= t.punctuality_impact_index <= 100)
            self.assertTrue(0 <= t.asset_degradation_score <= 100)
            self.assertTrue(0 <= t.composite_criticality_score <= 100)
            self.assertIn(t.recommended_horizon, list(Horizon))

    def test_optimizer_and_shadow_blocking(self):
        """Test corridor optimizer, traffic headway gap finding and shadow block bundling"""
        tasks = AIPrioritizer.prioritize_all_feeds(
            tms_defects=self.store.tms_defects,
            smms_defects=self.store.smms_defects,
            tdms_defects=self.store.tdms_defects,
            bdms_reqs=self.store.bdms_requisitions
        )
        blocks = BlockOptimizer.optimize_horizon_schedule(
            tasks=tasks,
            trains=self.store.coa_trains,
            target_horizon=Horizon.DAILY,
            plan_date="2026-08-27"
        )
        self.assertGreater(len(blocks), 0)
        
        # Check shadow-blocking existence
        mega_blocks = [b for b in blocks if b.is_integrated_mega_block]
        self.assertGreater(len(mega_blocks), 0, "Optimizer must create integrated mega blocks")
        
        first_mega = mega_blocks[0]
        self.assertGreaterEqual(len(first_mega.bundled_tasks), 1)
        self.assertGreaterEqual(first_mega.coordination_efficiency_gain_pct, 0.0)

    def test_multi_horizon_planner(self):
        """Test generation of DAILY, WEEKLY, and MONTHLY master plans"""
        tasks = AIPrioritizer.prioritize_all_feeds(
            tms_defects=self.store.tms_defects,
            smms_defects=self.store.smms_defects,
            tdms_defects=self.store.tdms_defects,
            bdms_reqs=self.store.bdms_requisitions
        )
        plans = MultiHorizonPlanner.generate_all_horizon_plans(
            tasks=tasks,
            trains=self.store.coa_trains,
            base_date="2026-08-27"
        )
        self.assertIn("DAILY", plans)
        self.assertIn("WEEKLY", plans)
        self.assertIn("MONTHLY", plans)
        
        daily_summary = plans["DAILY"]
        self.assertGreater(daily_summary.total_blocks_scheduled, 0)
        self.assertGreater(daily_summary.projected_asset_availability_pct, 80.0)
        
        # Benchmark metrics
        benchmarks = MultiHorizonPlanner.compute_system_benchmark(daily_summary)
        self.assertGreater(benchmarks.asset_availability_gain_pct, 5.0)
        self.assertGreater(benchmarks.multi_department_block_utilization_after_ai, 50.0)

    def test_what_if_simulator(self):
        """Test simulation of emergency rail fracture, freight surge, machine breakdown"""
        tasks = AIPrioritizer.prioritize_all_feeds(
            tms_defects=self.store.tms_defects,
            smms_defects=self.store.smms_defects,
            tdms_defects=self.store.tdms_defects,
            bdms_reqs=self.store.bdms_requisitions
        )
        blocks = BlockOptimizer.optimize_horizon_schedule(
            tasks=tasks,
            trains=self.store.coa_trains,
            target_horizon=Horizon.DAILY
        )
        
        # Scenario 1: Emergency Rail Fracture
        req1 = WhatIfScenarioRequest(
            scenario_type=WhatIfScenarioType.EMERGENCY_RAIL_FRACTURE,
            station_from="TDL",
            station_to="ETW",
            km_location=214.5,
            line=LineType.UP_MAIN
        )
        res1 = WhatIfSimulator.run_simulation(req1, self.store.coa_trains, blocks)
        self.assertIsNotNone(res1.emergency_block_granted)
        self.assertEqual(res1.emergency_block_granted.primary_department, Department.ENGINEERING)
        self.assertGreater(len(res1.affected_trains), 0)
        
        # Scenario 2: Freight Surge
        req2 = WhatIfScenarioRequest(
            scenario_type=WhatIfScenarioType.FREIGHT_TRAFFIC_SURGE,
            freight_increase_pct=40
        )
        res2 = WhatIfSimulator.run_simulation(req2, self.store.coa_trains, blocks)
        self.assertIn("Freight Traffic Surge", res2.scenario_title)

    def test_form_b_memo_generation(self):
        """Test official Indian Railways Form B Joint Block Sanction Memo formatting"""
        tasks = AIPrioritizer.prioritize_all_feeds(
            tms_defects=self.store.tms_defects,
            smms_defects=self.store.smms_defects,
            tdms_defects=self.store.tdms_defects,
            bdms_reqs=self.store.bdms_requisitions
        )
        blocks = BlockOptimizer.optimize_horizon_schedule(
            tasks=tasks,
            trains=self.store.coa_trains,
            target_horizon=Horizon.DAILY
        )
        self.assertGreater(len(blocks), 0)
        memo = ReportGenerator.generate_form_b_memo(blocks[0])
        self.assertIn("memo_number", memo)
        self.assertIn("NORTH CENTRAL RAILWAY", memo["railway_zone"])
        self.assertIn("safety_certifications", memo)
        self.assertEqual(len(memo["joint_signatories"]), 4)


if __name__ == "__main__":
    unittest.main()
