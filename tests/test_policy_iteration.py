"""Policy Iteration（策略迭代）的单元测试。

每个测试都按照以下顺序编写：

1. 准备输入数据。
2. 调用需要检查的函数。
3. 使用断言比较实际结果和预期结果。
"""

import unittest

from algorithms.policy_iteration import (
    PolicyIteration,
    action_value,
    first_action_policy,
    improve_policy,
)
from env.gridworld import GridWorld


class TestPolicyIteration(unittest.TestCase):
    """检查策略迭代的主要组成部分和最终结果。"""

    def setUp(self):
        """每个测试开始前创建一个新的 GridWorld。"""
        self.env = GridWorld()

    def test_first_action_policy(self):
        """初始策略应为每个非终止状态选择第一个合法动作。"""
        # 运行需要检查的函数。
        policy = first_action_policy(self.env)

        # 终止状态没有动作，因此不应该出现在策略中。
        self.assertNotIn(self.env.goal, policy)

        # 每个非终止状态都应该只有一个动作，且概率为 1。
        for state in self.env.states:
            if self.env.is_terminal(state):
                continue

            first_action = self.env.actions(state)[0]
            expected = {first_action: 1.0}
            self.assertEqual(policy[state], expected)

    def test_action_value(self):
        """一步前瞻价值应包含即时奖励和折扣后的下一状态价值。"""
        # 先令全部状态价值为 0，再单独设置右侧状态的价值。
        values = {}
        for state in self.env.states:
            values[state] = 0.0
        values[(0, 1)] = 5.0

        # 从 (0, 0) 向右会确定性地到达 (0, 1)。
        actual_value = action_value(
            mdp=self.env,
            values=values,
            state=(0, 0),
            action=self.env.RIGHT,
        )

        expected_value = -1.0 + 0.9 * 5.0
        self.assertAlmostEqual(actual_value, expected_value)

    def test_policy_improvement_changes_bad_action(self):
        """如果另一个动作价值更高，策略改进应替换原动作。"""
        policy = first_action_policy(self.env)

        values = {}
        for state in self.env.states:
            values[state] = 0.0
        values[(0, 1)] = 5.0

        new_policy, stable, changes = improve_policy(
            mdp=self.env,
            policy=policy,
            values=values,
        )

        # 初始策略选择 UP；右侧状态价值较高，所以应该改为 RIGHT。
        self.assertEqual(
            new_policy[(0, 0)],
            {self.env.RIGHT: 1.0},
        )
        self.assertFalse(stable)
        self.assertIn(
            ((0, 0), self.env.UP, self.env.RIGHT),
            changes,
        )

    def test_policy_improvement_keeps_tied_action(self):
        """原动作并列最优时，策略改进应保留原动作。"""
        # 当所有状态价值均为 0 时，四个动作的一步前瞻价值都是 -1。
        values = {}
        for state in self.env.states:
            values[state] = 0.0

        policy = first_action_policy(self.env)
        policy[(0, 0)] = {self.env.RIGHT: 1.0}

        new_policy, _, changes = improve_policy(
            mdp=self.env,
            policy=policy,
            values=values,
        )

        self.assertEqual(
            new_policy[(0, 0)],
            {self.env.RIGHT: 1.0},
        )

        changed_states = []
        for state, _, _ in changes:
            changed_states.append(state)

        self.assertNotIn((0, 0), changed_states)

    def test_policy_iteration_converges(self):
        """完整策略迭代应停止在稳定且贪心的策略。"""
        solver = PolicyIteration(
            mdp=self.env,
            evaluation_tolerance=1e-10,
            evaluation_max_iterations=10_000,
            max_iterations=100,
        )

        policy, values = solver.solve()

        # 检查算法确实因为策略稳定而停止。
        self.assertTrue(solver.converged)
        self.assertTrue(solver.history[-1]["stable"])
        self.assertEqual(solver.history[-1]["changed_states"], 0)
        self.assertEqual(values[self.env.goal], 0.0)

        # 最终策略在每个状态选择的动作都应该具有最大动作价值。
        for state in self.env.states:
            if self.env.is_terminal(state):
                continue

            selected_action = list(policy[state].keys())[0]
            selected_value = action_value(
                self.env,
                values,
                state,
                selected_action,
            )

            best_value = None
            for action in self.env.actions(state):
                current_value = action_value(
                    self.env,
                    values,
                    state,
                    action,
                )

                if best_value is None or current_value > best_value:
                    best_value = current_value

            self.assertAlmostEqual(
                selected_value,
                best_value,
                places=8,
            )

    def test_start_value_matches_shortest_path(self):
        """起点价值应等于八步最短路径的折扣回报。"""
        solver = PolicyIteration(
            mdp=self.env,
            evaluation_tolerance=1e-12,
        )

        _, values = solver.solve()

        # 八步路径会依次获得 -1、-0.9、...、-0.9^7。
        expected_value = 0.0
        for step in range(8):
            expected_value -= self.env.discount_factor ** step

        actual_value = values[self.env.initial_state]
        self.assertAlmostEqual(
            actual_value,
            expected_value,
            places=9,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
