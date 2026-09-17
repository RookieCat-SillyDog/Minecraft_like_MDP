"""Task FSM 状态转移测试。"""

import unittest

from src.config import load_task_config
from src.task_fsm.fsm import TaskFSM


class TestTaskFSM(unittest.TestCase):

    def make(self, condition):
        return TaskFSM(load_task_config(condition))

    def test_condition_a_sequence(self):
        fsm = self.make("A")
        for event, expected in [
            ("GET_KEY", "u1"),
            ("OPEN_DOOR", "u2"),
            ("GET_BEEF", "u3"),
            ("COOK", "u4"),
            ("REACH_GOAL", "u5"),
        ]:
            self.assertEqual(fsm.step({event}), expected)
        self.assertTrue(fsm.is_terminal)

    def test_condition_b_routes(self):
        # 条件 B 接受“钥匙路线”和“烹饪路线”中的任意一条。
        routes = [
            ["GET_KEY", "OPEN_DOOR", "REACH_GOAL"],
            ["GET_BEEF", "COOK", "REACH_GOAL"],
        ]
        for events in routes:
            with self.subTest(events=events):
                fsm = self.make("B")
                for event in events:
                    fsm.step({event})
                self.assertEqual(fsm.current_state, "v5")
                self.assertTrue(fsm.is_terminal)

    def test_unmatched_events_are_ignored(self):
        fsm = self.make("A")
        for events in [{"GET_BEEF"}, set(), {"NOT_AN_EVENT"}]:
            self.assertEqual(fsm.step(events), "u0")

    def test_condition_b_stays_on_chosen_route(self):
        fsm = self.make("B")
        fsm.step({"GET_KEY"})
        # 选定钥匙路线后，另一条路线的事件不应改变状态。
        fsm.step({"GET_BEEF"})
        self.assertEqual(fsm.current_state, "v1")
        fsm.step({"OPEN_DOOR"})
        fsm.step({"COOK"})
        self.assertEqual(fsm.current_state, "v2")

    def test_reset_and_terminal_absorption(self):
        fsm = self.make("A")
        for event in ["GET_KEY", "OPEN_DOOR", "GET_BEEF", "COOK", "REACH_GOAL"]:
            fsm.step({event})
        # 终止状态吸收后续事件。
        fsm.step({"GET_KEY"})
        self.assertEqual(fsm.current_state, "u5")

        self.assertEqual(fsm.reset(), "u0")
        self.assertFalse(fsm.is_terminal)
