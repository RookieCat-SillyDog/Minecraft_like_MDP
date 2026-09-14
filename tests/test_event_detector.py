"""事件检测层的测试：五种事件、无效动作无事件、重复进入可再触发。

测试通过真实 GridWorld 驱动 detect_events，模拟控制器的调用顺序。
"""

import unittest

from src.config import load_map_config
from src.envs.minecraft_grid import GridWorld
from src.task_fsm.labeling import detect_events


class TestEventDetector(unittest.TestCase):

    def setUp(self):
        self.env = GridWorld(load_map_config())

    def step_and_detect(self, action):
        """执行一步并返回事件，与控制器的调用顺序一致。"""
        before = self.env.state
        after = self.env.step(action)
        return detect_events(before, after, self.env.objects)

    def follow(self, actions):
        """依次执行动作，返回每一步的事件列表。"""
        return [self.step_and_detect(action) for action in actions]

    def test_plain_move_has_no_event(self):
        self.assertEqual(self.follow(["up", "up"]), [set(), set()])

    def test_wall_bump_has_no_event(self):
        self.assertEqual(self.step_and_detect("right"), set())

    def test_get_key_event_and_reentry(self):
        events = self.follow(["up", "up", "right"])
        self.assertEqual(events[-1], {"GET_KEY"})
        # 站在钥匙格原地撞边界：不产生事件
        self.assertEqual(self.step_and_detect("up"), set())
        # 离开（左边）后再回来，事件可以再次产生
        events = self.follow(["left", "right"])
        self.assertEqual(events, [set(), {"GET_KEY"}])

    def test_open_door_event(self):
        events = self.follow(["up", "up", "right", "right"])
        self.assertEqual(events[2], {"GET_KEY"})
        self.assertEqual(events[3], {"OPEN_DOOR"})
        # 门已打开，再进出不产生事件
        events = self.follow(["down", "up"])
        self.assertEqual(events, [set(), set()])

    def test_door_blocked_without_key_has_no_event(self):
        # 从下方通道绕到门正下方（避开钥匙格，只拿到牛肉）
        self.follow(["down", "down", "right", "right", "up", "up", "up"])
        self.assertEqual(self.step_and_detect("up"), set())

    def test_get_beef_and_cook_events(self):
        events = self.follow(["down", "down", "right", "right", "right"])
        self.assertEqual(events[3], {"GET_BEEF"})
        self.assertEqual(events[4], {"COOK"})
        # 离开厨房再回来：路过牛肉格再次 GET_BEEF，进厨房再次 COOK
        events = self.follow(["left", "right"])
        self.assertEqual(events, [{"GET_BEEF"}, {"COOK"}])

    def test_kitchen_without_beef_has_no_event(self):
        # 拿钥匙开门后，从右侧经目标格绕到厨房，全程不碰牛肉格
        events = self.follow([
            "up", "up", "right", "right", "right",
            "right", "down", "down", "down", "down", "left",
        ])
        self.assertEqual(events[-1], set())

    def test_reach_goal_event(self):
        # 走牛肉路线到目标：牛肉、烹饪、目标三个事件依次出现
        events = self.follow([
            "down", "down", "right", "right", "right", "right", "up", "up",
        ])
        self.assertEqual(events[3], {"GET_BEEF"})
        self.assertEqual(events[4], {"COOK"})
        self.assertEqual(events[7], {"REACH_GOAL"})


if __name__ == "__main__":
    unittest.main()
