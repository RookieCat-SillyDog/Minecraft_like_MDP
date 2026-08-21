"""测试 PI 和 VI 在 Minecraft-like MDP 上的实验结果。"""

import unittest

from algorithms.policy_iteration import PolicyIteration
from algorithms.value_iteration import ValueIteration
from env.minecraft import MinecraftMDP
from experiments.run_minecraft import compare_policies, follow_policy


SOLVER_TOLERANCE = 1e-10
VALUE_TOLERANCE = 1e-8
EXPECTED_STATE_COUNT = 96
EXPECTED_PATH_STEPS = 16


class TestMinecraftPolicyAndValueIteration(unittest.TestCase):
    """检查两个算法能否直接复用，并得到一致的最优结果。"""

    @classmethod
    def setUpClass(cls):
        """所有测试共用一次求解结果，避免重复运行算法。"""
        cls.env = MinecraftMDP()

        cls.pi_solver = PolicyIteration(
            mdp=cls.env,
            evaluation_tolerance=SOLVER_TOLERANCE,
        )
        cls.vi_solver = ValueIteration(
            mdp=cls.env,
            tolerance=SOLVER_TOLERANCE,
        )

        cls.pi_policy, cls.pi_values = cls.pi_solver.solve()
        cls.vi_policy, cls.vi_values = cls.vi_solver.solve()

        cls.pi_result = follow_policy(cls.env, cls.pi_policy)
        cls.vi_result = follow_policy(cls.env, cls.vi_policy)

    def test_both_algorithms_converge(self):
        """PI 和 VI 都应在迭代上限内收敛。"""
        self.assertTrue(self.pi_solver.converged)
        self.assertTrue(self.vi_solver.converged)

    def test_values_match_on_all_reachable_states(self):
        """两个算法在 96 个可达状态上的价值应当一致。"""
        differences = [
            abs(self.pi_values[state] - self.vi_values[state])
            for state in self.env.states
        ]

        self.assertEqual(len(self.env.states), EXPECTED_STATE_COUNT)
        self.assertLessEqual(max(differences), VALUE_TOLERANCE)

    def test_paths_finish_in_sixteen_steps_without_loops(self):
        """两个最优策略都应沿无循环的 16 步路径完成任务。"""
        for name, result in (
            ("PI", self.pi_result),
            ("VI", self.vi_result),
        ):
            with self.subTest(algorithm=name):
                path = result["path"]

                self.assertEqual(len(result["actions"]), EXPECTED_PATH_STEPS)
                self.assertEqual(len(path), EXPECTED_PATH_STEPS + 1)
                self.assertEqual(len(path), len(set(path)))
                self.assertTrue(self.env.is_terminal(path[-1]))
                self.assertCountEqual(
                    result["resource_order"],
                    ["wood", "iron"],
                )

    def test_start_values_match_path_returns(self):
        """算法得到的起点价值应等于实际路径的折扣回报。"""
        for name, values, result in (
            ("PI", self.pi_values, self.pi_result),
            ("VI", self.vi_values, self.vi_result),
        ):
            with self.subTest(algorithm=name):
                self.assertAlmostEqual(
                    values[self.env.initial_state],
                    result["discounted_return"],
                    delta=VALUE_TOLERANCE,
                )

    def test_different_actions_are_tied_optimal(self):
        """PI/VI 动作不同时，两个动作都应属于并列最优动作。"""
        differences = compare_policies(
            self.env,
            self.pi_policy,
            self.vi_policy,
            self.vi_values,
        )

        # 当前对称地图应当确实产生策略差异，避免测试在空列表上通过。
        self.assertTrue(differences)

        for item in differences:
            with self.subTest(state=item["state"]):
                self.assertTrue(item["both_optimal"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
