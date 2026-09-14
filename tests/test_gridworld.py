"""GridWorld 的逻辑测试：移动、碰撞、门、物品事实和重置。不依赖 PsychoPy。"""

import unittest

from src.config import load_map_config
from src.envs.minecraft_grid import GridWorld


class TestGridWorld(unittest.TestCase):

    def setUp(self):
        self.env = GridWorld(load_map_config())

    def follow(self, actions):
        """从当前状态开始依次执行动作，返回最终状态快照。"""
        for action in actions:
            self.env.step(action)
        return self.env.state

    def test_initial_state(self):
        state = self.env.state
        self.assertEqual(state["position"], (2, 0))
        self.assertFalse(state["has_key"])
        self.assertFalse(state["door_open"])
        self.assertFalse(state["has_beef"])
        self.assertFalse(state["cooked"])

    def test_basic_movement(self):
        self.assertEqual(self.follow(["up", "up", "right"])["position"], (0, 1))
        self.env.reset()
        self.assertEqual(self.follow(["down", "down", "right"])["position"], (4, 1))

    def test_wall_blocks_movement(self):
        state = self.follow(["right"])  # (2,1) 是墙
        self.assertEqual(state["position"], (2, 0))

    def test_boundary_blocks_movement(self):
        state = self.follow(["left"])  # 越出左边界
        self.assertEqual(state["position"], (2, 0))
        state = self.follow(["up", "up", "up"])  # 越出上边界
        self.assertEqual(state["position"], (0, 0))

    def test_get_key(self):
        state = self.follow(["up", "up", "right"])
        self.assertEqual(state["position"], (0, 1))
        self.assertTrue(state["has_key"])

    def test_door_blocked_without_key(self):
        # 从下方通道绕到门正下方，全程避开钥匙格
        state = self.follow(["down", "down", "right", "right", "up", "up", "up"])
        self.assertEqual(state["position"], (1, 2))
        state = self.follow(["up"])  # 没钥匙，被关着的门挡住
        self.assertEqual(state["position"], (1, 2))
        self.assertFalse(state["door_open"])

    def test_door_opens_with_key(self):
        state = self.follow(["up", "up", "right", "right"])
        self.assertEqual(state["position"], (0, 2))
        self.assertTrue(state["door_open"])

    def test_open_door_is_normal_cell(self):
        # 门打开后可以正常通行，门保持打开
        self.follow(["up", "up", "right", "right"])  # 开门，站在门格
        state = self.follow(["down", "up"])  # 离开再回来
        self.assertEqual(state["position"], (0, 2))
        self.assertTrue(state["door_open"])

    def test_get_beef_and_cook(self):
        state = self.follow(["down", "down", "right", "right"])  # 牛肉格
        self.assertTrue(state["has_beef"])
        self.assertFalse(state["cooked"])
        state = self.follow(["right"])  # 厨房
        self.assertTrue(state["cooked"])

    def test_kitchen_without_beef_does_not_cook(self):
        # 拿钥匙开门后，从右侧经目标格绕到厨房，全程不碰牛肉格
        state = self.follow([
            "up", "up", "right", "right", "right",  # 钥匙、门，走到 (0,3)
            "right", "down", "down", "down", "down", "left",  # 绕行到厨房 (4,3)
        ])
        self.assertEqual(state["position"], (4, 3))
        self.assertFalse(state["has_beef"])
        self.assertFalse(state["cooked"])

    def test_reset_restores_all_facts(self):
        self.follow(["up", "up", "right", "right", "down", "down", "down"])
        self.assertTrue(self.env.state["door_open"])
        self.env.reset()
        self.assertEqual(self.env.state, {
            "position": (2, 0),
            "has_key": False,
            "door_open": False,
            "has_beef": False,
            "cooked": False,
        })

    def test_state_snapshot_is_independent(self):
        before = self.env.state
        self.env.step("up")
        after = self.env.state
        self.assertEqual(before["position"], (2, 0))
        self.assertEqual(after["position"], (1, 0))


if __name__ == "__main__":
    unittest.main()
