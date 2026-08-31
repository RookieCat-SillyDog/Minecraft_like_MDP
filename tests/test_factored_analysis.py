"""四个 factored task anchors 与耦合分析测试。"""

import unittest
from dataclasses import replace

from env.factored_minecraft import FactoredMinecraftMDP
from env.factored_tasks import (
    AvailabilityRule,
    BEEF_FACTOR,
    BEEF_STATES,
    BOARD_LOCATION,
    COOK,
    CUT,
    DirectedTransition,
    INDEPENDENT_TASK,
    KEY_FACTOR,
    KEY_GATES_LOCATION_TASK,
    KITCHEN_LOCATION,
    LEFT,
    LOCATION_FACTOR,
    LOCATION_GATES_BEEF_TASK,
    RIGHT,
    TASK_CONFIGS,
)
from experiments.analyze_factored_tasks import (
    analyze_task,
    shortest_path_dag,
    shortest_path_ranges,
    structural_coupling,
)


class KeyChangesCookOutcomeMDP(FactoredMinecraftMDP):
    """用于验证同一动作在不同 Key context 下产生不同目标。"""

    def transitions(self, state, action):
        outcomes = super().transitions(state, action)

        if action == COOK and state[1] == (2, 2) and state[2] == (0, 0):
            location, key, _ = state
            return [(1.0, (location, key, (2, 0)))]

        return outcomes


EXPECTED_RESULTS = {
    "independent": {
        "schema_coupling": (0, 0),
        "template_coupling": (0, 0),
        "reachable": 729,
        "path_count": 75600,
        "k_to_l_range": [0, 0],
        "l_to_b_range": [0, 0],
        "switch_range": [2, 9],
    },
    "key_gates_location": {
        "schema_coupling": (2, 0),
        "template_coupling": (2, 0),
        "reachable": 594,
        "path_count": 30240,
        "k_to_l_range": [1, 1],
        "l_to_b_range": [0, 0],
        "switch_range": [2, 9],
    },
    "location_gates_beef": {
        "schema_coupling": (0, 2),
        "template_coupling": (0, 12),
        "reachable": 729,
        "path_count": 90,
        "k_to_l_range": [0, 0],
        "l_to_b_range": [4, 4],
        "switch_range": [5, 8],
    },
    "combined": {
        "schema_coupling": (2, 2),
        "template_coupling": (2, 12),
        "reachable": 594,
        "path_count": 56,
        "k_to_l_range": [1, 1],
        "l_to_b_range": [4, 4],
        "switch_range": [5, 8],
    },
}


class TestFactoredAnchorRules(unittest.TestCase):
    """检查门和功能区规则的实际动作可用性。"""

    def test_door_requires_both_key_attributes(self):
        env = FactoredMinecraftMDP(KEY_GATES_LOCATION_TASK)
        allowed_state = (KITCHEN_LOCATION, (2, 2), (0, 0))

        self.assertIn(RIGHT, env.actions(allowed_state))
        self.assertIn(
            LEFT,
            env.actions(((1, 2), (2, 2), (0, 0))),
        )

        for key in ((2, 1), (1, 2)):
            with self.subTest(key=key):
                blocked_state = (KITCHEN_LOCATION, key, (0, 0))
                self.assertNotIn(RIGHT, env.actions(blocked_state))

    def test_all_beef_actions_require_their_locations(self):
        env = FactoredMinecraftMDP(LOCATION_GATES_BEEF_TASK)

        for beef in BEEF_STATES:
            kitchen_state = (KITCHEN_LOCATION, (0, 0), beef)
            board_state = (BOARD_LOCATION, (0, 0), beef)

            if beef[0] < 2:
                self.assertIn(COOK, env.actions(kitchen_state))
                self.assertNotIn(COOK, env.actions(board_state))
            else:
                self.assertNotIn(COOK, env.actions(kitchen_state))

            if beef[1] < 2:
                self.assertIn(CUT, env.actions(board_state))
                self.assertNotIn(CUT, env.actions(kitchen_state))
            else:
                self.assertNotIn(CUT, env.actions(board_state))

    def test_all_anchor_actions_change_only_one_factor(self):
        for task_name, config in TASK_CONFIGS.items():
            env = FactoredMinecraftMDP(config)
            for state in env.states:
                for action in env.actions(state):
                    next_state = env.transitions(state, action)[0][1]
                    changed_factors = sum(
                        before != after
                        for before, after in zip(state, next_state)
                    )
                    with self.subTest(task=task_name, state=state, action=action):
                        self.assertEqual(changed_factors, 1)


class TestCouplingCounterexamples(unittest.TestCase):
    """用独立反例检查模板数、实例数和结果变化。"""

    def test_one_template_can_have_two_legal_location_instances(self):
        controlled_edge = DirectedTransition((0, 0), COOK, (1, 0))
        rule = AvailabilityRule(
            name="two-location-cook-gate",
            conditioning_factor=LOCATION_FACTOR,
            target_factor=BEEF_FACTOR,
            controlled_transitions=(controlled_edge,),
            allowed_condition_states=frozenset(
                {BOARD_LOCATION, KITCHEN_LOCATION}
            ),
        )
        config = replace(
            INDEPENDENT_TASK,
            task_name="two-location-instance-test",
            beef_gates=(rule,),
        )

        coupling = structural_coupling(FactoredMinecraftMDP(config))
        detail = coupling["metrics"][(LOCATION_FACTOR, BEEF_FACTOR)]

        self.assertEqual(detail["coupled_schemas"], 1)
        self.assertEqual(detail["total_schemas"], 2)
        self.assertEqual(detail["coupled_templates"], 1)
        self.assertEqual(detail["total_templates"], 12)
        self.assertEqual(detail["coupled_instances"], 2)
        self.assertEqual(detail["total_instances"], 101)
        self.assertAlmostEqual(detail["schema_proportion"], 1 / 2)
        self.assertAlmostEqual(detail["template_proportion"], 1 / 12)
        self.assertAlmostEqual(detail["instance_proportion"], 2 / 101)

    def test_result_change_creates_two_coupled_templates(self):
        env = KeyChangesCookOutcomeMDP(INDEPENDENT_TASK)
        coupling = structural_coupling(env)
        detail = coupling["metrics"][(KEY_FACTOR, BEEF_FACTOR)]
        expected_templates = {
            DirectedTransition((0, 0), COOK, (1, 0)),
            DirectedTransition((0, 0), COOK, (2, 0)),
        }

        self.assertEqual(coupling["template_counts"]["k_to_b"], 2)
        self.assertEqual(coupling["schema_counts"]["k_to_b"], 1)
        self.assertEqual(
            coupling["templates"][(KEY_FACTOR, BEEF_FACTOR)],
            expected_templates,
        )
        self.assertEqual(detail["total_schemas"], 2)
        self.assertEqual(detail["coupled_schemas"], 1)
        self.assertEqual(detail["total_templates"], 13)
        self.assertEqual(detail["coupled_instances"], 9)
        self.assertEqual(detail["total_instances"], 108)
        self.assertAlmostEqual(detail["schema_proportion"], 1 / 2)
        self.assertAlmostEqual(detail["template_proportion"], 2 / 13)
        self.assertAlmostEqual(detail["instance_proportion"], 9 / 108)


class TestFactoredTaskAnalysis(unittest.TestCase):
    """检查矩阵、全部最短路径范围和 PI/VI 交叉验证。"""

    @classmethod
    def setUpClass(cls):
        # 四个环境只求解一次，后续测试复用同一批分析结果。
        cls.results = {
            name: analyze_task(config)
            for name, config in TASK_CONFIGS.items()
        }

    def test_structural_coupling_matrices(self):
        inactive_keys = ("l_to_k", "k_to_b", "b_to_l", "b_to_k")

        for name, expected in EXPECTED_RESULTS.items():
            result = self.results[name]
            schema_counts = result["schema_coupling"]
            template_counts = result["template_coupling"]
            with self.subTest(task=name):
                self.assertEqual(
                    (schema_counts["k_to_l"], schema_counts["l_to_b"]),
                    expected["schema_coupling"],
                )
                self.assertEqual(
                    (
                        template_counts["k_to_l"],
                        template_counts["l_to_b"],
                    ),
                    expected["template_coupling"],
                )
                for key in inactive_keys:
                    self.assertEqual(schema_counts[key], 0)
                    self.assertEqual(template_counts[key], 0)
                details = result["coupling_detail"]
                self.assertEqual(
                    result["query_initial_state"],
                    TASK_CONFIGS[name].query_set[0],
                )
                key_location = details["k_to_l"]
                location_beef = details["l_to_b"]
                self.assertEqual(key_location["total_schemas"], 4)
                self.assertEqual(location_beef["total_schemas"], 2)
                self.assertEqual(key_location["total_templates"], 20)
                self.assertEqual(location_beef["total_templates"], 12)
                self.assertEqual(key_location["analysis_scope"], "reachable_contexts")
                self.assertEqual(location_beef["analysis_scope"], "reachable_contexts")
                if template_counts["k_to_l"]:
                    self.assertEqual(
                        (
                            key_location["coupled_schemas"],
                            key_location["coupled_templates"],
                            key_location["coupled_instances"],
                            key_location["total_instances"],
                        ),
                        (2, 2, 2, 144),
                    )
                    self.assertAlmostEqual(
                        key_location["schema_proportion"],
                        2 / 4,
                    )
                    self.assertAlmostEqual(
                        key_location["template_proportion"],
                        2 / 20,
                    )
                    self.assertAlmostEqual(
                        key_location["instance_proportion"],
                        2 / 144,
                    )
                if template_counts["l_to_b"]:
                    self.assertEqual(
                        (
                            location_beef["coupled_schemas"],
                            location_beef["coupled_templates"],
                            location_beef["coupled_instances"],
                            location_beef["total_instances"],
                        ),
                        (2, 12, 12, 12),
                    )
                    self.assertAlmostEqual(
                        location_beef["schema_proportion"],
                        2 / 2,
                    )
                    self.assertAlmostEqual(
                        location_beef["template_proportion"],
                        12 / 12,
                    )
                    self.assertAlmostEqual(
                        location_beef["instance_proportion"],
                        12 / 12,
                    )
                for key in inactive_keys:
                    values = details[key]
                    self.assertEqual(values["coupled_schemas"], 0)
                    self.assertEqual(values["coupled_instances"], 0)
                    self.assertEqual(values["schema_proportion"], 0.0)
                    self.assertEqual(values["template_proportion"], 0.0)
                    self.assertEqual(values["instance_proportion"], 0.0)

    def test_matched_length_and_shortest_path_ranges(self):
        for name, expected in EXPECTED_RESULTS.items():
            result = self.results[name]
            ranges = result["path_coupling_range"]
            with self.subTest(task=name):
                self.assertEqual(result["optimal_length"], 10)
                self.assertEqual(
                    result["reachable_states"],
                    expected["reachable"],
                )
                self.assertEqual(
                    result["shortest_path_count"],
                    expected["path_count"],
                )
                self.assertEqual(
                    ranges["k_to_l"],
                    expected["k_to_l_range"],
                )
                self.assertEqual(
                    ranges["l_to_b"],
                    expected["l_to_b_range"],
                )
                self.assertEqual(result["switch_range"], expected["switch_range"])

    def test_path_ranges_use_the_dag_query_start(self):
        env = FactoredMinecraftMDP(INDEPENDENT_TASK)
        query_start = ((1, 0), (0, 0), (0, 0))
        dag = shortest_path_dag(env, query_start)
        coupling = structural_coupling(env)
        result = shortest_path_ranges(env, dag, coupling["templates"])

        self.assertEqual(dag["initial_state"], query_start)
        self.assertEqual(dag["optimal_length"], 9)
        self.assertGreater(result["path_count"], 0)
        self.assertEqual(result["ranges"]["k_to_l"], [0, 0])
        self.assertEqual(result["ranges"]["l_to_b"], [0, 0])

    def test_pi_vi_values_and_tied_actions(self):
        for name, result in self.results.items():
            comparison = result["solver_comparison"]
            with self.subTest(task=name):
                self.assertLess(comparison["pi_vi_max_diff"], 1e-8)
                self.assertGreater(comparison["policy_difference_count"], 0)
                self.assertEqual(
                    comparison["unexplained_policy_differences"],
                    [],
                )

    def test_action_statistics_are_reported(self):
        for name, result in self.results.items():
            statistics = result["action_statistics"]
            with self.subTest(task=name):
                self.assertGreater(statistics["total_available_actions"], 0)
                self.assertGreater(statistics["average_branching_factor"], 0)
                self.assertLessEqual(
                    statistics["minimum_branching_factor"],
                    statistics["maximum_branching_factor"],
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
