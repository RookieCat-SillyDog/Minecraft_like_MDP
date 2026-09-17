"""RewardMachine 核心转移测试。"""

import unittest

from src.config import load_reward_machine_config
from src.task_fsm.reward_machine import RewardMachine


def load_rm(name):
    return RewardMachine(load_reward_machine_config(name))


class TestRewardMachine(unittest.TestCase):

    def test_states(self):
        cases = [
            ("coffee_office", "u0", {"u0", "u1", "u2"}, {"u2"}),
            ("visit_abcd", "v0", {"v0", "v1", "v2", "v3", "v4"}, {"v4"}),
        ]
        for name, initial, states, terminal in cases:
            with self.subTest(name=name):
                rm = load_rm(name)
                self.assertEqual(rm.reset(), initial)
                self.assertEqual(rm.states, states)
                self.assertEqual(rm.terminal_states, terminal)

    def test_coffee_office_sequence(self):
        rm = load_rm("coffee_office")
        u = rm.reset()
        transitions = []
        for labels in [set(), {"coffee"}, set(), {"office"}]:
            u, reward = rm.next_state(u, labels)
            transitions.append((u, reward))
        self.assertEqual(transitions, [
            ("u0", 0),
            ("u1", 0),
            ("u1", 0),
            ("u2", 1),
        ])

    def test_visit_abcd_sequence(self):
        rm = load_rm("visit_abcd")
        u = rm.reset()
        transitions = []
        for label in ["A", "B", "C", "D"]:
            u, reward = rm.next_state(u, {label})
            transitions.append((u, reward))
        self.assertEqual(transitions, [
            ("v1", 0),
            ("v2", 0),
            ("v3", 0),
            ("v4", 1),
        ])

    def test_unmatched_labels_keep_state(self):
        # 标签存在但不符合当前任务进度时，RM 应停留在原状态。
        cases = [
            ("coffee_office", "u0", {"office"}),
            ("coffee_office", "u1", {"coffee"}),
            ("visit_abcd", "v0", {"B"}),
            ("visit_abcd", "v2", {"D"}),
        ]
        for name, u, labels in cases:
            with self.subTest(name=name, u=u, labels=labels):
                self.assertEqual(load_rm(name).next_state(u, labels), (u, 0))

    def test_terminal_states_are_absorbing(self):
        # 任务完成后，任何新标签都不能重新启动状态转移或产生奖励。
        cases = [
            ("coffee_office", "u2"),
            ("visit_abcd", "v4"),
        ]
        for name, terminal in cases:
            with self.subTest(name=name):
                rm = load_rm(name)
                self.assertEqual(rm.next_state(terminal, {"coffee"}), (terminal, 0))

    def test_reward_lookup(self):
        coffee = load_rm("coffee_office")
        abcd = load_rm("visit_abcd")
        self.assertEqual(coffee.reward("u1", "u2"), 1)
        self.assertEqual(coffee.reward("u0", "u0"), 0)
        self.assertEqual(abcd.reward("v3", "v4"), 1)
