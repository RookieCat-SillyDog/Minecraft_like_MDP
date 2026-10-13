"""Demo 任务配置的 Reward Machine 转移测试。"""

import unittest

from src.config import load_task_config
from src.task_fsm.reward_machine import RewardMachine


class TestTaskRewardMachine(unittest.TestCase):

    def make(self, condition):
        rm = RewardMachine(load_task_config(condition))
        return rm, rm.reset()

    def test_condition_a_sequence(self):
        rm, u = self.make("A")
        for event, expected_u, expected_reward in [
            ("GET_KEY", "u1", 0),
            ("OPEN_DOOR", "u2", 0),
            ("GET_BEEF", "u3", 0),
            ("COOK", "u4", 0),
            ("REACH_GOAL", "u5", 1),
        ]:
            u, reward = rm.next_state(u, {event})
            self.assertEqual((u, reward), (expected_u, expected_reward))
        self.assertTrue(rm.is_terminal(u))

    def test_condition_b_routes(self):
        # 条件 B 接受“钥匙路线”和“烹饪路线”中的任意一条。
        routes = [
            ["GET_KEY", "OPEN_DOOR", "REACH_GOAL"],
            ["GET_BEEF", "COOK", "REACH_GOAL"],
        ]
        for events in routes:
            with self.subTest(events=events):
                rm, u = self.make("B")
                for event in events:
                    u, reward = rm.next_state(u, {event})
                self.assertEqual((u, reward), ("v5", 1))
                self.assertTrue(rm.is_terminal(u))

    def test_unmatched_events_are_ignored(self):
        rm, u = self.make("A")
        for events in [{"GET_BEEF"}, set(), {"NOT_AN_EVENT"}]:
            self.assertEqual(rm.next_state(u, events), ("u0", 0))

    def test_condition_b_stays_on_chosen_route(self):
        rm, u = self.make("B")
        u, _ = rm.next_state(u, {"GET_KEY"})
        # 选定钥匙路线后，另一条路线的事件不应改变状态。
        u, _ = rm.next_state(u, {"GET_BEEF"})
        self.assertEqual(u, "v1")
        u, _ = rm.next_state(u, {"OPEN_DOOR"})
        u, _ = rm.next_state(u, {"COOK"})
        self.assertEqual(u, "v2")

    def test_reset_and_terminal_absorption(self):
        rm, u = self.make("A")
        for event in ["GET_KEY", "OPEN_DOOR", "GET_BEEF", "COOK", "REACH_GOAL"]:
            u, _ = rm.next_state(u, {event})
        # 终止状态吸收后续事件。
        u, reward = rm.next_state(u, {"GET_KEY"})
        self.assertEqual((u, reward), ("u5", 0))

        u = rm.reset()
        self.assertEqual(u, "u0")
        self.assertFalse(rm.is_terminal(u))
