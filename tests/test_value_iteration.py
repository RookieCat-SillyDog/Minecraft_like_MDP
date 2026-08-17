"""Value Iteration（价值迭代）的单元测试。
"""

import unittest

from algorithms.policy_iteration import PolicyIteration
from algorithms.value_iteration import (
    ValueIteration,
    find_best_actions,
    greedy_policy,
)
from env.gridworld import GridWorld


class TestValueIteration(unittest.TestCase):
    """检查价值迭代的主要组成部分和最终结果。"""

    def setUp(self):
        """每个测试开始前创建一个新的 GridWorld。"""
        self.env = GridWorld()

    def test_all_actions_are_tied_with_zero_values(self):
        """价值全为零时，起点的四个动作应当并列。"""
        values = {
            state: 0.0
            for state in self.env.states
        }

        best_actions, best_value = find_best_actions(
            mdp=self.env,
            values=values,
            state=self.env.initial_state,
        )

        self.assertEqual(
            best_actions,
            list(self.env.ACTIONS),
        )
        self.assertEqual(best_value, -1.0)

    def test_find_best_actions_selects_right(self):
        """右侧状态价值更高时，向右应当是唯一最优动作。"""
        values = {
            state: 0.0
            for state in self.env.states
        }
        values[(0, 1)] = 5.0

        best_actions, best_value = find_best_actions(
            mdp=self.env,
            values=values,
            state=(0, 0),
        )

        expected_value = -1.0 + 0.9 * 5.0
        self.assertEqual(best_actions, [self.env.RIGHT])
        self.assertAlmostEqual(best_value, expected_value)

    def test_greedy_policy_is_deterministic(self):
        """贪心策略应为每个非终止状态选择一个动作。"""
        values = {
            state: 0.0
            for state in self.env.states
        }

        policy = greedy_policy(
            mdp=self.env,
            values=values,
        )

        self.assertNotIn(self.env.goal, policy)

        for state in self.env.states:
            if self.env.is_terminal(state):
                continue

            action_probabilities = policy[state]
            self.assertEqual(len(action_probabilities), 1)
            self.assertEqual(
                list(action_probabilities.values()),
                [1.0],
            )

    def test_value_iteration_converges(self):
        """价值迭代应达到残差阈值，并保持终止价值为零。"""
        tolerance = 1e-10
        solver = ValueIteration(
            mdp=self.env,
            tolerance=tolerance,
        )

        _, values = solver.solve()

        self.assertTrue(solver.converged)
        self.assertLessEqual(
            solver.residuals[-1],
            tolerance,
        )
        self.assertEqual(
            len(solver.residuals),
            solver.iterations,
        )
        self.assertEqual(values[self.env.goal], 0.0)

    def test_start_value_matches_shortest_path(self):
        """起点价值应等于八步最短路径的折扣回报。"""
        solver = ValueIteration(
            mdp=self.env,
            tolerance=1e-12,
        )

        _, values = solver.solve()

        expected_value = 0.0
        for step in range(8):
            expected_value -= self.env.discount_factor ** step

        actual_value = values[self.env.initial_state]
        self.assertAlmostEqual(
            actual_value,
            expected_value,
            places=9,
        )

    def test_final_policy_is_greedy(self):
        """最终策略选择的动作应属于并列最优动作集合。"""
        solver = ValueIteration(
            mdp=self.env,
            tolerance=1e-10,
        )

        policy, values = solver.solve()

        for state in self.env.states:
            if self.env.is_terminal(state):
                continue

            selected_action = list(policy[state].keys())[0]
            best_actions, _ = find_best_actions(
                mdp=self.env,
                values=values,
                state=state,
            )

            self.assertIn(selected_action, best_actions)

    def test_pi_and_vi_values_are_consistent(self):
        """PI 与 VI 在全部状态上的最优价值应当一致。"""
        pi_solver = PolicyIteration(
            mdp=self.env,
            evaluation_tolerance=1e-10,
        )
        _, pi_values = pi_solver.solve()

        vi_solver = ValueIteration(
            mdp=self.env,
            tolerance=1e-10,
        )
        _, vi_values = vi_solver.solve()

        max_difference = max(
            abs(pi_values[state] - vi_values[state])
            for state in self.env.states
        )

        self.assertLessEqual(max_difference, 1e-8)

    def test_invalid_parameters(self):
        """非法容差和迭代次数应当报告错误。"""
        with self.assertRaises(ValueError):
            ValueIteration(
                mdp=self.env,
                tolerance=0,
            )

        with self.assertRaises(ValueError):
            ValueIteration(
                mdp=self.env,
                max_iterations=0,
            )

        with self.assertRaises(ValueError):
            ValueIteration(
                mdp=self.env,
                tie_tolerance=-1.0,
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
