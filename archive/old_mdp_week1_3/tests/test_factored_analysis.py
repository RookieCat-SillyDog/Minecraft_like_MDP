"""四个 factored task anchors 与耦合分析测试。"""

import unittest

from env.factored_minecraft.environment import FactoredMinecraftMDP
from env.factored_minecraft.maps import beef, default_map, key, location
from env.factored_minecraft.tasks import task_rules
from analysis.coupling import structural_coupling
from analysis.analyze_factored_tasks import analyze_task
from analysis.shortest_paths import shortest_path_dag, shortest_path_ranges


class KeyChangesCookOutcomeMDP(FactoredMinecraftMDP):
    """用于验证同一动作在不同 Key context 下产生不同目标。"""

    def transitions(self, state, action):
        outcomes = super().transitions(state, action)

        if action == "cook" and state[1] == "blue" and state[2] == "raw":
            location, key, _ = state
            return [(1.0, (location, key, "well"))]

        return outcomes


EXPECTED_RESULTS = {
    "independent": {
        "schema_coupling": (0, 0),
        "template_coupling": (0, 0),
        "reachable": 81,
        "path_count": 840,
        "k_to_l_range": [0, 0],
        "l_to_b_range": [0, 0],
        "switch_range": [2, 7],
    },
    "key_gates_location": {
        "schema_coupling": (1, 0),
        "template_coupling": (1, 0),
        "reachable": 63,
        "path_count": 336,
        "k_to_l_range": [1, 1],
        "l_to_b_range": [0, 0],
        "switch_range": [2, 7],
    },
    "location_gates_beef": {
        "schema_coupling": (0, 1),
        "template_coupling": (0, 2),
        "reachable": 81,
        "path_count": 56,
        "k_to_l_range": [0, 0],
        "l_to_b_range": [2, 2],
        "switch_range": [3, 6],
    },
    "combined": {
        "schema_coupling": (1, 1),
        "template_coupling": (1, 2),
        "reachable": 63,
        "path_count": 30,
        "k_to_l_range": [1, 1],
        "l_to_b_range": [2, 2],
        "switch_range": [3, 6],
    },
}


class TestFactoredAnchorRules(unittest.TestCase):
    """检查门和功能区规则的实际动作可用性。"""

    def test_door_requires_blue_key(self):
        env = FactoredMinecraftMDP(default_map, task_rules["key_gates_location"])
        allowed_state = (default_map.landmarks["kitchen"], "blue", "raw")

        self.assertIn("right", env.actions(allowed_state))
        self.assertIn(
            "left",
            env.actions(((1, 2), "blue", "raw")),
        )

        for key in ("blank", "shallow blue"):
            with self.subTest(key=key):
                blocked_state = (default_map.landmarks["kitchen"], key, "raw")
                self.assertNotIn("right", env.actions(blocked_state))

    def test_cook_requires_kitchen(self):
        env = FactoredMinecraftMDP(default_map, task_rules["location_gates_beef"])

        for beef_state in default_map.factor_states[beef]:
            kitchen_state = (default_map.landmarks["kitchen"], "blank", beef_state)
            start_state = (default_map.landmarks["start"], "blank", beef_state)

            if beef_state != "well":
                self.assertIn("cook", env.actions(kitchen_state))
                self.assertNotIn("cook", env.actions(start_state))
            else:
                self.assertNotIn("cook", env.actions(kitchen_state))

    def test_all_anchor_actions_change_only_one_factor(self):
        for task_name, rules in task_rules.items():
            env = FactoredMinecraftMDP(default_map, rules)
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
        controlled_edge = ("raw", "cook", "medium")
        allowed_locations = {
            default_map.landmarks["start"],
            default_map.landmarks["kitchen"],
        }

        def allow_cook_at_two_locations(map_config, state, edge):
            if edge != controlled_edge:
                return True
            return state[location] in allowed_locations

        coupling = structural_coupling(
            FactoredMinecraftMDP(default_map, (allow_cook_at_two_locations,))
        )
        detail = coupling["metrics"][(location, beef)]

        self.assertEqual(detail["coupled_schemas"], 1)
        self.assertEqual(detail["total_schemas"], 1)
        self.assertEqual(detail["coupled_templates"], 1)
        self.assertEqual(detail["total_templates"], 2)
        self.assertEqual(detail["coupled_instances"], 2)
        self.assertEqual(detail["total_instances"], 11)
        self.assertAlmostEqual(detail["schema_proportion"], 1.0)
        self.assertAlmostEqual(detail["template_proportion"], 1 / 2)
        self.assertAlmostEqual(detail["instance_proportion"], 2 / 11)

    def test_result_change_creates_two_coupled_templates(self):
        env = KeyChangesCookOutcomeMDP(default_map)
        coupling = structural_coupling(env)
        detail = coupling["metrics"][(key, beef)]
        expected_templates = {
            ("raw", "cook", "medium"),
            ("raw", "cook", "well"),
        }

        self.assertEqual(coupling["template_counts"]["k_to_b"], 2)
        self.assertEqual(coupling["schema_counts"]["k_to_b"], 1)
        self.assertEqual(
            coupling["templates"][(key, beef)],
            expected_templates,
        )
        self.assertEqual(detail["total_schemas"], 1)
        self.assertEqual(detail["coupled_schemas"], 1)
        self.assertEqual(detail["total_templates"], 3)
        self.assertEqual(detail["coupled_instances"], 3)
        self.assertEqual(detail["total_instances"], 6)
        self.assertAlmostEqual(detail["schema_proportion"], 1.0)
        self.assertAlmostEqual(detail["template_proportion"], 2 / 3)
        self.assertAlmostEqual(detail["instance_proportion"], 3 / 6)


class TestFactoredAnalysis(unittest.TestCase):
    """检查矩阵、全部最短路径范围和 PI/VI 交叉验证。"""

    @classmethod
    def setUpClass(cls):
        cls.results = {
            name: analyze_task(name, rules)
            for name, rules in task_rules.items()
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
                key_location = details["k_to_l"]
                location_beef = details["l_to_b"]
                self.assertEqual(key_location["total_schemas"], 4)
                self.assertEqual(location_beef["total_schemas"], 1)
                self.assertEqual(key_location["total_templates"], 20)
                self.assertEqual(location_beef["total_templates"], 2)
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
                        (1, 1, 1, 48),
                    )
                    self.assertAlmostEqual(key_location["schema_proportion"], 1 / 4)
                    self.assertAlmostEqual(key_location["template_proportion"], 1 / 20)
                    self.assertAlmostEqual(key_location["instance_proportion"], 1 / 48)
                if template_counts["l_to_b"]:
                    self.assertEqual(
                        (
                            location_beef["coupled_schemas"],
                            location_beef["coupled_templates"],
                            location_beef["coupled_instances"],
                            location_beef["total_instances"],
                        ),
                        (1, 2, 2, 2),
                    )
                    self.assertAlmostEqual(location_beef["schema_proportion"], 1.0)
                    self.assertAlmostEqual(location_beef["template_proportion"], 1.0)
                    self.assertAlmostEqual(location_beef["instance_proportion"], 1.0)
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
                self.assertEqual(result["optimal_length"], 8)
                self.assertEqual(result["reachable_states"], expected["reachable"])
                self.assertEqual(result["shortest_path_count"], expected["path_count"])
                self.assertEqual(ranges["k_to_l"], expected["k_to_l_range"])
                self.assertEqual(ranges["l_to_b"], expected["l_to_b_range"])
                self.assertEqual(result["switch_range"], expected["switch_range"])

    def test_path_ranges_use_the_dag_query_start(self):
        env = FactoredMinecraftMDP(default_map)
        query_start = ((1, 0), "blank", "raw")
        dag = shortest_path_dag(env, query_start)
        coupling = structural_coupling(env)
        result = shortest_path_ranges(env, dag, coupling["templates"])

        self.assertEqual(dag["initial_state"], query_start)
        self.assertEqual(dag["optimal_length"], 7)
        self.assertGreater(result["path_count"], 0)
        self.assertEqual(result["ranges"]["k_to_l"], [0, 0])
        self.assertEqual(result["ranges"]["l_to_b"], [0, 0])

    def test_pi_vi_values_and_tied_actions(self):
        for name, result in self.results.items():
            comparison = result["solver_comparison"]
            with self.subTest(task=name):
                self.assertLess(comparison["pi_vi_max_diff"], 1e-8)
                self.assertGreater(comparison["policy_difference_count"], 0)

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
