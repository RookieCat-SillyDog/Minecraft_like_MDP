"""四个 factored task anchors 与耦合分析测试。"""

import unittest

from env.factored_minecraft import FactoredMinecraftMDP
from env.factored_tasks import (
    BOARD_LOCATION,
    CHOP,
    COOL,
    HEAT,
    INDEPENDENT_TASK,
    KEY_GATES_LOCATION_TASK,
    KITCHEN_LOCATION,
    LEFT,
    LOCATION_GATES_BEEF_TASK,
    RIGHT,
    STIR,
    TASK_CONFIGS,
)
from experiments.analyze_factored_tasks import (
    analyze_task,
    shortest_path_dag,
    shortest_path_ranges,
    structural_coupling,
)


EXPECTED_RESULTS = {
    "independent": {
        "coupling": (0, 0),
        "reachable": 729,
        "path_count": 75600,
        "k_to_l_range": [0, 0],
        "l_to_b_range": [0, 0],
        "switch_range": [2, 9],
    },
    "key_gates_location": {
        "coupling": (2, 0),
        "reachable": 594,
        "path_count": 30240,
        "k_to_l_range": [1, 1],
        "l_to_b_range": [0, 0],
        "switch_range": [2, 9],
    },
    "location_gates_beef": {
        "coupling": (0, 2),
        "reachable": 729,
        "path_count": 10800,
        "k_to_l_range": [0, 0],
        "l_to_b_range": [1, 1],
        "switch_range": [3, 9],
    },
    "combined": {
        "coupling": (2, 2),
        "reachable": 594,
        "path_count": 4068,
        "k_to_l_range": [1, 1],
        "l_to_b_range": [1, 1],
        "switch_range": [3, 9],
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

    def test_two_specific_beef_templates_require_their_locations(self):
        env = FactoredMinecraftMDP(LOCATION_GATES_BEEF_TASK)

        kitchen_heat = (KITCHEN_LOCATION, (0, 0), (0, 0))
        board_heat = (BOARD_LOCATION, (0, 0), (0, 0))
        self.assertIn(HEAT, env.actions(kitchen_heat))
        self.assertNotIn(HEAT, env.actions(board_heat))

        board_chop = (BOARD_LOCATION, (0, 0), (0, 0))
        kitchen_chop = (KITCHEN_LOCATION, (0, 0), (0, 0))
        self.assertIn(CHOP, env.actions(board_chop))
        self.assertNotIn(CHOP, env.actions(kitchen_chop))

        # 其他 Beef templates 不受地点控制。
        self.assertIn(HEAT, env.actions((BOARD_LOCATION, (0, 0), (1, 0))))
        self.assertIn(CHOP, env.actions((KITCHEN_LOCATION, (0, 0), (1, 0))))

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
            counts = result["structural_coupling"]
            with self.subTest(task=name):
                self.assertEqual(
                    (counts["k_to_l"], counts["l_to_b"]),
                    expected["coupling"],
                )
                for key in inactive_keys:
                    self.assertEqual(counts[key], 0)
                metrics = result["coupling_metrics"]
                self.assertEqual(
                    result["query_initial_state"],
                    TASK_CONFIGS[name].query_set[0],
                )
                key_location = metrics[("K", "L")]
                location_beef = metrics[("L", "B")]
                self.assertEqual(key_location["total_templates"], 20)
                self.assertEqual(location_beef["total_templates"], 18)
                self.assertEqual(key_location["analysis_scope"], "reachable_contexts")
                self.assertEqual(location_beef["analysis_scope"], "reachable_contexts")
                if counts["k_to_l"]:
                    self.assertEqual(
                        (
                            key_location["coupled_templates"],
                            key_location["coupled_instances"],
                            key_location["total_instances"],
                        ),
                        (2, 2, 144),
                    )
                    self.assertAlmostEqual(
                        key_location["template_proportion"],
                        2 / 20,
                    )
                    self.assertAlmostEqual(
                        key_location["instance_proportion"],
                        2 / 144,
                    )
                if counts["l_to_b"]:
                    self.assertEqual(
                        (
                            location_beef["coupled_templates"],
                            location_beef["coupled_instances"],
                            location_beef["total_instances"],
                        ),
                        (2, 2, 146),
                    )
                    self.assertAlmostEqual(
                        location_beef["template_proportion"],
                        2 / 18,
                    )
                    self.assertAlmostEqual(
                        location_beef["instance_proportion"],
                        2 / 146,
                    )
                for key in inactive_keys:
                    source, target = key.split("_to_")
                    values = metrics[(source.upper(), target.upper())]
                    self.assertEqual(values["coupled_instances"], 0)
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
