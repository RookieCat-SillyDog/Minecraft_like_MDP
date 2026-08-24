"""带障碍挑战地图的针对性测试。"""

import unittest

from algorithms.policy_iteration import PolicyIteration
from algorithms.value_iteration import ValueIteration
from env.minecraft import MinecraftMDP
from env.minecraft_maps import CHALLENGE_MAP
from experiments.run_minecraft_challenge import compare_values, follow_policy


SOLVER_TOLERANCE = 1e-10
VALUE_TOLERANCE = 1e-8


class TestMinecraftChallenge(unittest.TestCase):
    """确认挑战地图不改变 MDP 接口，并满足预期规则。"""

    @classmethod
    def setUpClass(cls):
        cls.env = MinecraftMDP(CHALLENGE_MAP)
        cls.pi_solver = PolicyIteration(
            cls.env,
            evaluation_tolerance=SOLVER_TOLERANCE,
        )
        cls.vi_solver = ValueIteration(cls.env, tolerance=SOLVER_TOLERANCE)
        cls.pi_policy, cls.pi_values = cls.pi_solver.solve()
        cls.vi_policy, cls.vi_values = cls.vi_solver.solve()
        cls.pi_result = follow_policy(cls.env, cls.pi_policy)
        cls.vi_result = follow_policy(cls.env, cls.vi_policy)

    def follow(self, actions):
        state = self.env.initial_state
        for action in actions:
            state = self.env.transitions(state, action)[0][1]
        return state

    def test_obstacle_collision_and_state_exclusion(self):
        """起点向下撞到障碍，障碍格也不在状态空间中。"""
        self.assertEqual(
            self.env.transitions(self.env.initial_state, self.env.DOWN),
            [(1.0, self.env.initial_state)],
        )
        self.assertFalse(any(state[:2] == (1, 0) for state in self.env.states))
        self.assertIn(" X ", self.env.render())

    def test_factory_requires_resources(self):
        """资源不足时，经过 factory 不应终止。"""
        factory_without_resources = self.follow([self.env.RIGHT] * 2)
        self.assertEqual(factory_without_resources, (0, 2, 0, 0, 0))
        self.assertFalse(self.env.is_terminal(factory_without_resources))

    def test_both_collection_orders_can_finish(self):
        """两种资源顺序均可绕开障碍并在 factory 完成任务。"""
        iron_first = (
            [self.env.RIGHT] + [self.env.DOWN] * 4 + [self.env.LEFT]
            + [self.env.RIGHT] * 4 + [self.env.UP] * 4 + [self.env.LEFT] * 2
        )
        wood_first = (
            [self.env.RIGHT] * 4 + [self.env.DOWN] * 4 + [self.env.LEFT] * 4
            + [self.env.UP] * 2 + [self.env.RIGHT] * 2 + [self.env.UP] * 2
        )
        self.assertEqual(len(iron_first), 16)
        self.assertEqual(len(wood_first), 18)
        self.assertEqual(self.follow(iron_first), self.env.TERMINAL_STATE)
        self.assertEqual(self.follow(wood_first), self.env.TERMINAL_STATE)

    def test_algorithms_match_and_paths_finish_without_loops(self):
        """PI 和 VI 价值一致，且展示路径都终止而不循环。"""
        max_difference, _ = compare_values(
            self.env,
            self.pi_values,
            self.vi_values,
        )
        self.assertEqual(len(self.env.states), 92)
        self.assertLessEqual(max_difference, VALUE_TOLERANCE)

        for result in (self.pi_result, self.vi_result):
            self.assertTrue(result["terminated"])
            self.assertFalse(result["has_loop"])
            self.assertTrue(self.env.is_terminal(result["path"][-1]))
            self.assertEqual(len(result["actions"]), 16)
            self.assertEqual(result["resource_order"], ["iron", "wood"])

    def test_start_values_match_executed_path_returns(self):
        """两个算法的起点价值应与实际执行路径的折扣回报一致。"""
        for values, result in (
            (self.pi_values, self.pi_result),
            (self.vi_values, self.vi_result),
        ):
            self.assertAlmostEqual(
                values[self.env.initial_state],
                result["discounted_return"],
                delta=VALUE_TOLERANCE,
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
