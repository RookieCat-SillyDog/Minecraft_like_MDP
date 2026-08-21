"""Day 8 Minecraft 状态与转移枚举测试。"""

import unittest

from env.minecraft import MinecraftMDP
from experiments.enumerate_minecraft_states import analyze_states
from experiments.minecraft_state_graph import make_partial_graph_data


class TestMinecraftStateEnumeration(unittest.TestCase):
    """检查理论状态、实际可达状态和转移统计。"""

    def setUp(self):
        self.env = MinecraftMDP()
        self.result = analyze_states(self.env)

    def test_theoretical_and_reachable_state_counts(self):
        """理论空间应有 200 个组合，遍历应得到 96 个状态。"""
        theoretical = self.result["theoretical_states"]
        reachable = self.result["reachable_states"]
        unreachable = self.result["unreachable_states"]

        self.assertEqual(len(theoretical), 200)
        self.assertEqual(len(set(theoretical)), 200)
        self.assertEqual(len(reachable), 96)
        self.assertEqual(len(unreachable), 104)

    def test_traversal_matches_environment_states(self):
        """遍历结果应与环境声明的状态集合完全一致。"""
        self.assertEqual(
            set(self.result["reachable_states"]),
            set(self.env.states),
        )
        self.assertEqual(self.result["missing_from_declared"], [])
        self.assertEqual(self.result["declared_but_unreachable"], [])
        self.assertEqual(self.result["reachable_outside_theory"], [])

    def test_states_and_transitions_have_no_duplicates(self):
        """状态列表和完整转移记录均不应含重复项。"""
        self.assertEqual(self.result["declared_duplicate_count"], 0)
        self.assertEqual(self.result["reachable_duplicate_count"], 0)
        self.assertEqual(self.result["duplicate_transition_count"], 0)

    def test_transition_counts_and_probabilities(self):
        """95 个非终止状态各有四个确定性动作。"""
        transitions = self.result["transitions"]

        self.assertEqual(self.result["state_action_count"], 95 * 4)
        self.assertEqual(len(transitions), 95 * 4)

        probability_sums = {}

        for state, action, probability, next_state in transitions:
            key = (state, action)

            if key not in probability_sums:
                probability_sums[key] = 0.0

            probability_sums[key] += probability
            self.assertIn(
                next_state,
                self.result["reachable_states"],
            )

        for probability_sum in probability_sums.values():
            self.assertAlmostEqual(probability_sum, 1.0)

    def test_unreachable_states_are_completely_classified(self):
        """104 个不可达组合应由四类环境约束完整解释。"""
        categories = self.result["unreachable_categories"]
        category_counts = sorted(
            len(states)
            for states in categories.values()
        )
        classified_states = {
            state
            for states in categories.values()
            for state in states
        }

        self.assertEqual(category_counts, [1, 2, 2, 99])
        self.assertEqual(
            classified_states,
            set(self.result["unreachable_states"]),
        )
        self.assertNotIn(
            "未被现有状态约束解释",
            categories,
        )

    def test_partial_graph_uses_real_environment_transitions(self):
        """图中的每条边都应来自环境接口的实际转移。"""
        graph_data = make_partial_graph_data(self.env)

        self.assertEqual(len(graph_data["movement"]), 2)
        self.assertEqual(len(graph_data["resources"]), 4)
        self.assertEqual(len(graph_data["factory"]), 2)

        for transitions in graph_data.values():
            for _, state, action, next_state in transitions:
                actual_next_state = self.env.transitions(
                    state,
                    action,
                )[0][1]
                self.assertEqual(next_state, actual_next_state)
                self.assertIn(state, self.env.states)
                self.assertIn(next_state, self.env.states)


if __name__ == "__main__":
    unittest.main(verbosity=2)
