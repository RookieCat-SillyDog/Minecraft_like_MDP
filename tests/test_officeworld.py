"""OfficeWorld 环境与 RM 组合测试。"""

import unittest

from src.config import load_officeworld_config, load_reward_machine_config
from src.envs.officeworld import OfficeWorld
from src.task_fsm.reward_machine import RewardMachine


def load_env():
    return OfficeWorld(load_officeworld_config())


def load_rm():
    return RewardMachine(load_reward_machine_config("coffee_office"))


def run(env, rm, actions):
    # 同时记录环境位置和 RM 状态，便于核对整条轨迹。
    s, u = env.start, rm.initial_state
    rows = []
    for action in actions:
        s_next = env.next_position(s, action)
        labels = env.label(s_next)
        u_next, reward = rm.next_state(u, labels)
        rows.append((action, s_next, labels, u_next, reward))
        s, u = s_next, u_next
    return rows


class TestOfficeWorld(unittest.TestCase):

    def setUp(self):
        self.env = load_env()

    def test_movement_rules(self):
        cases = [
            ((2, 2), "D", (3, 2)),
            ((2, 2), "L", (2, 1)),
            ((2, 2), "R", (2, 2)),  # 墙
            ((0, 0), "U", (0, 0)),  # 边界
            ((4, 4), "R", (4, 4)),  # 边界
        ]
        for position, action, expected in cases:
            with self.subTest(position=position, action=action):
                self.assertEqual(
                    self.env.next_position(position, action), expected
                )

    def test_positions_and_labels(self):
        self.assertEqual(len(self.env.positions), 21)
        self.assertNotIn((2, 3), self.env.positions)
        self.assertEqual(self.env.label((0, 0)), {"A"})
        self.assertEqual(self.env.label((4, 2)), {"coffee"})
        self.assertEqual(self.env.label((4, 4)), {"office"})
        self.assertEqual(self.env.label((2, 2)), set())

        # 撞到边界后仍停在 coffee 格，因此标签不能丢失。
        stayed = self.env.next_position((4, 2), "D")
        self.assertEqual(stayed, (4, 2))
        self.assertEqual(self.env.label(stayed), {"coffee"})

    def test_query_and_stateful_step(self):
        # next_position 只查询转移，step 才修改环境内部状态。
        self.env.next_position((2, 2), "D")
        self.assertEqual(self.env.position, (2, 2))
        self.assertEqual(self.env.step("D"), (3, 2))
        self.assertEqual(self.env.position, (3, 2))

    def test_coffee_office_trajectory(self):
        rows = run(self.env, load_rm(), ["D", "D", "R", "R"])
        self.assertEqual(rows, [
            ("D", (3, 2), set(),       "u0", 0),
            ("D", (4, 2), {"coffee"},  "u1", 0),
            ("R", (4, 3), set(),       "u1", 0),
            ("R", (4, 4), {"office"},  "u2", 1),
        ])

    def test_policy_comparison_states_are_reachable(self):
        rm = load_rm()
        cases = [
            (["U", "U", "R", "R", "D", "D", "D", "D", "L"], "u0"),
            (["D", "D", "R"], "u1"),
        ]
        for actions, expected_u in cases:
            with self.subTest(expected_u=expected_u):
                last = run(self.env, rm, actions)[-1]
                self.assertEqual(last[1], (4, 3))
                self.assertEqual(last[3], expected_u)
                self.assertFalse(rm.is_terminal(last[3]))
