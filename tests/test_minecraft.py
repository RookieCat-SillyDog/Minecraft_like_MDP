"""Minecraft-like Make Bridge 环境测试。"""

import unittest

from env.minecraft import MinecraftMDP


class TestMinecraftMDP(unittest.TestCase):

    def setUp(self):
        self.env = MinecraftMDP()

    def follow(self, actions):
        """从初始状态开始，依次执行一组动作。"""
        state = self.env.initial_state

        for action in actions:
            state = self.env.transitions(state, action)[0][1]

        return state

    def test_configuration_and_states(self):
        """检查地图配置、初始状态和可达状态。"""
        self.assertEqual(self.env.start, (0, 0))
        self.assertEqual(self.env.wood, (0, 4))
        self.assertEqual(self.env.iron, (4, 0))
        self.assertEqual(self.env.factory, (4, 4))
        self.assertEqual(self.env.initial_state, (0, 0, 0, 0, 0))
        self.assertAlmostEqual(self.env.discount_factor, 0.95)

        self.assertEqual(len(self.env.states), 96)
        self.assertEqual(len(set(self.env.states)), 96)
        self.assertIn(self.env.TERMINAL_STATE, self.env.states)

    def test_movement_and_boundary(self):
        """检查普通移动和越界后原地不动。"""
        self.assertEqual(
            self.env.transitions(self.env.initial_state, self.env.RIGHT),
            [(1.0, (0, 1, 0, 0, 0))],
        )
        self.assertEqual(
            self.env.transitions(self.env.initial_state, self.env.UP),
            [(1.0, self.env.initial_state)],
        )

    def test_collect_and_keep_resources(self):
        """检查自动收集资源，并确保资源不会丢失。"""
        state_before_wood = (0, 3, 0, 0, 0)
        state_at_wood = self.env.transitions(
            state_before_wood,
            self.env.RIGHT,
        )[0][1]
        self.assertEqual(state_at_wood, (0, 4, 1, 0, 0))

        state_after_leaving = self.env.transitions(
            state_at_wood,
            self.env.LEFT,
        )[0][1]
        self.assertEqual(state_after_leaving, (0, 3, 1, 0, 0))

        state_at_wood_again = self.env.transitions(
            state_after_leaving,
            self.env.RIGHT,
        )[0][1]
        self.assertEqual(state_at_wood_again, (0, 4, 1, 0, 0))

        state_at_iron = self.env.transitions(
            (3, 0, 0, 0, 0),
            self.env.DOWN,
        )[0][1]
        self.assertEqual(state_at_iron, (4, 0, 0, 1, 0))

    def test_both_collection_orders_finish_task(self):
        """检查 wood 和 iron 可以按任意顺序收集。"""
        wood_first = (
            [self.env.RIGHT] * 4
            + [self.env.LEFT] * 4
            + [self.env.DOWN] * 4
            + [self.env.RIGHT] * 4
        )
        iron_first = (
            [self.env.DOWN] * 4
            + [self.env.UP] * 4
            + [self.env.RIGHT] * 4
            + [self.env.DOWN] * 4
        )

        self.assertEqual(
            self.follow(wood_first),
            self.env.TERMINAL_STATE,
        )
        self.assertEqual(
            self.follow(iron_first),
            self.env.TERMINAL_STATE,
        )

    def test_factory_requires_both_resources(self):
        """检查资源不足时进入 factory 不会完成任务。"""
        no_resource_path = (
            [self.env.RIGHT] * 3
            + [self.env.DOWN] * 4
            + [self.env.RIGHT]
        )
        wood_only_path = (
            [self.env.RIGHT] * 4
            + [self.env.DOWN] * 4
        )

        no_resource_state = self.follow(no_resource_path)
        wood_only_state = self.follow(wood_only_path)

        self.assertEqual(no_resource_state, (4, 4, 0, 0, 0))
        self.assertEqual(wood_only_state, (4, 4, 1, 0, 0))
        self.assertFalse(self.env.is_terminal(no_resource_state))
        self.assertFalse(self.env.is_terminal(wood_only_state))

    def test_all_transitions(self):
        """检查所有合法转移均确定且结果属于状态空间。"""
        for state in self.env.states:
            for action in self.env.actions(state):
                transitions = self.env.transitions(state, action)

                self.assertEqual(len(transitions), 1)

                probability, next_state = transitions[0]
                self.assertEqual(probability, 1.0)
                self.assertIn(next_state, self.env.states)
                self.assertEqual(self.env.reward(state, action), -1.0)

    def test_terminal_state(self):
        """检查终止状态没有合法动作，也不能继续转移。"""
        terminal_state = self.env.TERMINAL_STATE

        self.assertTrue(self.env.is_terminal(terminal_state))
        self.assertEqual(self.env.actions(terminal_state), [])

        with self.assertRaises(ValueError):
            self.env.transitions(terminal_state, self.env.UP)

        with self.assertRaises(ValueError):
            self.env.reward(terminal_state, self.env.UP)

    def test_invalid_input(self):
        """检查非法状态和非法动作会报告错误。"""
        with self.assertRaises(ValueError):
            self.env.actions((99, 99, 0, 0, 0))

        with self.assertRaises(ValueError):
            self.env.transitions(self.env.initial_state, 999)


if __name__ == "__main__":
    unittest.main(verbosity=2)
