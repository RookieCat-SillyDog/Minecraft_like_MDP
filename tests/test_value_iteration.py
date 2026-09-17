"""乘积 MDP 上的价值迭代测试。"""

import unittest

from src.algorithms.product_mdp import transition
from src.algorithms.value_iteration import value_iteration
from src.config import load_officeworld_config, load_reward_machine_config
from src.envs.officeworld import OfficeWorld
from src.task_fsm.reward_machine import RewardMachine


def load_task(name):
    env = OfficeWorld(load_officeworld_config())
    rm = RewardMachine(load_reward_machine_config(name))
    return env, rm


def rollout(env, rm, policy, gamma=0.99, max_steps=200):
    s, u = env.start, rm.initial_state
    total = 0.0
    discount = 1.0
    for _ in range(max_steps):
        if rm.is_terminal(u):
            return total, True
        action = policy[(s, u)][0]
        s, u, reward, _ = transition(env, rm, s, u, action)
        total += discount * reward
        discount *= gamma
    return total, False


class TestValueIteration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.env, cls.rm = load_task("coffee_office")
        (cls.values, cls.action_values, cls.policy, cls.iterations,
         cls.residual, cls.converged) = value_iteration(cls.env, cls.rm)

    def test_convergence_and_terminal_values(self):
        self.assertTrue(self.converged)
        self.assertGreater(self.iterations, 0)
        self.assertLess(self.residual, 1e-8)
        # 终止状态没有后续动作，其价值固定为零。
        for position in self.env.positions:
            self.assertEqual(self.values[(position, "u2")], 0.0)
            self.assertEqual(self.action_values[(position, "u2")], {})

    def test_known_start_value(self):
        # 最优路线在第 4 次转移获得奖励，因此起点价值为 gamma^3。
        self.assertAlmostEqual(
            self.values[(self.env.start, "u0")], 0.99 ** 3
        )

    def test_same_position_has_different_policy_by_rm_state(self):
        # 位置相同，但任务历史不同：未取咖啡时向左，取到后向右。
        position = (4, 3)
        self.assertEqual(self.policy[(position, "u0")], ["L"])
        self.assertEqual(self.policy[(position, "u1")], ["R"])
        self.assertAlmostEqual(
            self.action_values[(position, "u0")]["L"], 0.99 ** 2
        )
        self.assertAlmostEqual(
            self.action_values[(position, "u1")]["R"], 1.0
        )

    def test_policy_rollout_matches_value(self):
        total, done = rollout(self.env, self.rm, self.policy)
        self.assertTrue(done)
        self.assertAlmostEqual(total, self.values[(self.env.start, "u0")])

    def test_visit_abcd(self):
        env, rm = load_task("visit_abcd")
        values, _, policy, _, residual, converged = value_iteration(env, rm)
        self.assertTrue(converged)
        self.assertLess(residual, 1e-8)
        # 最优路线在第 16 次转移完成任务。
        self.assertAlmostEqual(values[(env.start, "v0")], 0.99 ** 15)
        total, done = rollout(env, rm, policy)
        self.assertTrue(done)
        self.assertAlmostEqual(total, values[(env.start, "v0")])
