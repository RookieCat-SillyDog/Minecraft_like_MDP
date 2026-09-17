"""状态变化到事件标签的映射测试。"""

import unittest

from src.config import load_map_config
from src.task_fsm.labeling import detect_events


class TestEventDetector(unittest.TestCase):

    def setUp(self):
        config = load_map_config()
        self.objects = {
            name: tuple(position) for name, position in config["objects"].items()
        }
        # 从普通地块出发，每个用例只改动触发事件所需的字段。
        self.base = {
            "position": (2, 0),
            "has_key": False,
            "door_open": False,
            "has_beef": False,
            "cooked": False,
        }

    def test_detects_each_event(self):
        cases = [
            ({"position": self.objects["key"]}, {"GET_KEY"}),
            ({"position": self.objects["door"], "door_open": True}, {"OPEN_DOOR"}),
            ({"position": self.objects["beef"]}, {"GET_BEEF"}),
            ({"position": self.objects["kitchen"], "has_beef": True}, {"COOK"}),
            ({"position": self.objects["goal"]}, {"REACH_GOAL"}),
        ]
        for changes, expected in cases:
            with self.subTest(expected=expected):
                current = {**self.base, **changes}
                self.assertEqual(
                    detect_events(self.base, current, self.objects), expected
                )

    def test_same_position_has_no_event(self):
        # 事件来自位置变化，不能仅根据物品状态的差异重复触发。
        current = {**self.base, "has_key": True}
        self.assertEqual(detect_events(self.base, current, self.objects), set())

    def test_kitchen_requires_beef(self):
        current = {**self.base, "position": self.objects["kitchen"]}
        self.assertEqual(detect_events(self.base, current, self.objects), set())
