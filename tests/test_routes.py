"""路线测试
"""

import unittest

from src.config import load_map_config, load_task_config
from src.envs.minecraft_grid import GridWorld
from src.task_fsm.fsm import TaskFSM
from src.task_fsm.labeling import detect_events


class TestRoutes(unittest.TestCase):

    def setUp(self):
        self.map_config = load_map_config()

    def run_route(self, condition, actions):
        """新建环境和 FSM，按数据流执行动作，返回 (fsm, 出现过的事件列表)。"""
        env = GridWorld(self.map_config)
        fsm = TaskFSM(load_task_config(condition))
        events_seen = []
        for action in actions:
            before = env.state
            after = env.step(action)
            events = detect_events(before, after, env.objects)
            fsm.step(events)
            if events:
                events_seen.append(next(iter(events)))
        return fsm, events_seen

    def test_condition_a_full_route(self):
        """A：钥匙 → 门 → 牛肉 → 厨房 → 目标，五个事件按序出现。"""
        actions = [
            "up", "up", "right",             # 拿钥匙
            "right",                         # 开门
            "down", "down", "down", "down",  # 沿门下方通道去牛肉
            "right",                         # 厨房烹饪
            "right", "up", "up",             # 到目标
        ]
        fsm, events = self.run_route("A", actions)
        self.assertEqual(events, ["GET_KEY", "OPEN_DOOR", "GET_BEEF", "COOK", "REACH_GOAL"])
        self.assertEqual(fsm.current_state, "u5")
        self.assertTrue(fsm.is_terminal)

    def test_condition_b_key_route(self):
        """B 钥匙路线：不需要碰牛肉和厨房。"""
        actions = [
            "up", "up", "right",   # 拿钥匙
            "right",               # 开门
            "right", "right",      # 沿上边缘走
            "down", "down",        # 下到目标
        ]
        fsm, events = self.run_route("B", actions)
        self.assertEqual(events, ["GET_KEY", "OPEN_DOOR", "REACH_GOAL"])
        self.assertEqual(fsm.current_state, "v5")
        self.assertTrue(fsm.is_terminal)

    def test_condition_b_beef_route(self):
        """B 牛肉路线：全程不需要钥匙和门。"""
        actions = [
            "down", "down", "right", "right",  # 拿牛肉
            "right",                           # 厨房烹饪
            "right", "up", "up",               # 到目标
        ]
        fsm, events = self.run_route("B", actions)
        self.assertEqual(events, ["GET_BEEF", "COOK", "REACH_GOAL"])
        self.assertEqual(fsm.current_state, "v5")
        self.assertTrue(fsm.is_terminal)

    def test_condition_a_reaching_goal_early_does_not_finish(self):
        """未完成任务就走到目标：事件有、环境不终止、FSM 不动。"""
        actions = [
            "up", "up", "right", "right",      # 拿钥匙、开门
            "right", "right", "down", "down",  # 沿上边缘走到目标 (2,4)
        ]
        fsm, events = self.run_route("A", actions)
        self.assertEqual(events, ["GET_KEY", "OPEN_DOOR", "REACH_GOAL"])
        self.assertEqual(fsm.current_state, "u2")  # REACH_GOAL 在 u2 没有对应边
        self.assertFalse(fsm.is_terminal)


if __name__ == "__main__":
    unittest.main()
