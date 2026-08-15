"""迭代式策略评估测试。"""

import unittest

from algorithms.policy_evaluation import PolicyEvaluation, uniform_random_policy
from env.gridworld import GridWorld


class TestPolicyEvaluation(unittest.TestCase):

    def setUp(self):
        """每项测试开始前创建新的环境和策略。"""
        self.env = GridWorld()
        self.policy = uniform_random_policy(self.env)

    def test_uniform_random_policy(self):
        """检查均匀随机策略的动作概率。"""
        for state in self.env.states:
            if self.env.is_terminal(state):
                self.assertNotIn(state, self.policy)
                continue

            action_probabilities = self.policy[state]

            self.assertEqual(
                set(action_probabilities),
                set(self.env.actions(state)),
            )
            self.assertAlmostEqual(
                sum(action_probabilities.values()),
                1.0,
            )

            for probability in action_probabilities.values():
                self.assertAlmostEqual(probability, 0.25)

    def test_first_iteration(self):
        """检查从全零价值开始的第一轮 Bellman 更新。"""
        evaluator = PolicyEvaluation(
            mdp=self.env,
            policy=self.policy,
            tolerance=1e-12,
            max_iterations=1,
        )

        values = evaluator.evaluate()

        for state in self.env.states:
            if self.env.is_terminal(state):
                self.assertEqual(values[state], 0.0)
            else:
                self.assertEqual(values[state], -1.0)

        self.assertEqual(evaluator.iterations, 1)
        self.assertFalse(evaluator.converged)
        self.assertEqual(evaluator.residuals, [1.0])

    def test_convergence_and_terminal_value(self):
        """检查算法能够收敛，并保持终止状态价值为 0。"""
        tolerance = 1e-8
        evaluator = PolicyEvaluation(
            mdp=self.env,
            policy=self.policy,
            tolerance=tolerance,
            max_iterations=10_000,
        )

        values = evaluator.evaluate()

        self.assertTrue(evaluator.converged)
        self.assertLess(evaluator.iterations, evaluator.max_iterations)
        self.assertEqual(len(evaluator.residuals), evaluator.iterations)
        self.assertLessEqual(evaluator.residuals[-1], tolerance)
        self.assertEqual(values[self.env.goal], 0.0)

    def test_invalid_policy_probability_sum(self):
        """检查动作概率之和不为 1 时能够报告错误。"""
        bad_policy = {
            state: action_probabilities.copy()
            for state, action_probabilities in self.policy.items()
        }

        bad_policy[self.env.initial_state][self.env.UP] = 0.5

        with self.assertRaises(ValueError):
            PolicyEvaluation(
                mdp=self.env,
                policy=bad_policy,
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
