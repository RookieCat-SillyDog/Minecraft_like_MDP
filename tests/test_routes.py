"""环境、事件检测和 Task FSM 的端到端路线测试。"""

import unittest

from src.config import load_map_config, load_task_config
from src.envs.minecraft_grid import GridWorld
from src.task_fsm.fsm import TaskFSM
from src.task_fsm.labeling import detect_events


class TestRoutes(unittest.TestCase):

    def run_route(self, condition, actions):
        env = GridWorld(load_map_config())
        fsm = TaskFSM(load_task_config(condition))
        events_seen = []
        for action in actions:
            before = env.state
            after = env.step(action)
            events = detect_events(before, after, env.objects)
            fsm.step(events)
            events_seen.extend(events)
        return fsm, events_seen

    def test_condition_a_route(self):
        # 完整路线同时覆盖环境交互、事件生成和 FSM 状态推进。
        actions = [
            "up", "up", "right", "right",
            "down", "down", "down", "down",
            "right", "right", "up", "up",
        ]
        fsm, events = self.run_route("A", actions)
        self.assertEqual(
            events,
            ["GET_KEY", "OPEN_DOOR", "GET_BEEF", "COOK", "REACH_GOAL"],
        )
        self.assertTrue(fsm.is_terminal)

    def test_condition_b_routes(self):
        routes = [
            (
                ["up", "up", "right", "right", "right", "right", "down", "down"],
                ["GET_KEY", "OPEN_DOOR", "REACH_GOAL"],
            ),
            (
                ["down", "down", "right", "right", "right", "right", "up", "up"],
                ["GET_BEEF", "COOK", "REACH_GOAL"],
            ),
        ]
        for actions, expected_events in routes:
            with self.subTest(expected_events=expected_events):
                fsm, events = self.run_route("B", actions)
                self.assertEqual(events, expected_events)
                self.assertTrue(fsm.is_terminal)

    def test_reaching_goal_early_does_not_finish_condition_a(self):
        # 条件 A 强制执行完整顺序，提前到达目标不算完成。
        actions = [
            "up", "up", "right", "right", "right", "right", "down", "down",
        ]
        fsm, events = self.run_route("A", actions)
        self.assertEqual(events, ["GET_KEY", "OPEN_DOOR", "REACH_GOAL"])
        self.assertEqual(fsm.current_state, "u2")
        self.assertFalse(fsm.is_terminal)
