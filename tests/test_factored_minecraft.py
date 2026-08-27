"""三因子 Minecraft MDP 的 Day 11–12 测试。"""

import unittest
from dataclasses import replace

from env.factored_minecraft import FactoredMinecraftMDP
from env.factored_tasks import (
    BEEF_FACTOR,
    BEEF_GRAPH,
    CHOP,
    GOAL_STATE,
    HEAD_BLACK,
    HEAD_WHITE,
    HEAT,
    INDEPENDENT_TASK,
    KEY_FACTOR,
    KEY_GRAPH,
    LEFT,
    LOCATION_FACTOR,
    LOCATION_GRAPH,
    RIGHT,
    TAIL_BLACK,
    TAIL_WHITE,
    UP,
)


class TestFactoredMinecraftMDP(unittest.TestCase):

    def setUp(self):
        self.env = FactoredMinecraftMDP()

    def follow(self, actions):
        """从初始状态开始，依次执行一组动作。"""
        state = self.env.initial_state
        for action in actions:
            state = self.env.transitions(state, action)[0][1]
        return state

    def test_three_factor_graphs(self):
        """检查三张基础图的节点、边和展示信息。"""
        graphs = (LOCATION_GRAPH, KEY_GRAPH, BEEF_GRAPH)

        self.assertEqual([len(graph.nodes) for graph in graphs], [9, 9, 9])
        self.assertEqual(
            [len(graph.transitions) for graph in graphs],
            [20, 24, 18],
        )

        for graph in graphs:
            self.assertEqual(set(graph.labels), set(graph.nodes))
            self.assertEqual(set(graph.coordinates), set(graph.nodes))

    def test_bfs_reachable_states(self):
        """检查 independent 的 BFS 结果完整、无重复且顺序稳定。"""
        second_env = FactoredMinecraftMDP()

        self.assertEqual(len(self.env.states), 729)
        self.assertEqual(len(set(self.env.states)), 729)
        self.assertEqual(self.env.states[0], self.env.initial_state)
        self.assertEqual(self.env.states, second_env.states)
        self.assertIn(GOAL_STATE, self.env.states)

    def test_all_successors_stay_reachable(self):
        """检查合法转移确定、奖励正确，且后继仍在 states 中。"""
        reachable_states = set(self.env.states)

        for state in self.env.states:
            for action in self.env.actions(state):
                outcomes = self.env.transitions(state, action)
                self.assertEqual(len(outcomes), 1)

                probability, next_state = outcomes[0]
                self.assertEqual(probability, 1.0)
                self.assertIn(next_state, reachable_states)
                self.assertEqual(self.env.reward(state, action), -1.0)

    def test_each_action_changes_only_its_own_factor(self):
        """检查 Location、Key、Beef 动作只改变对应因子。"""
        factor_index = {
            LOCATION_FACTOR: 0,
            KEY_FACTOR: 1,
            BEEF_FACTOR: 2,
        }

        for state in self.env.states:
            for action in self.env.actions(state):
                next_state = self.env.transitions(state, action)[0][1]

                changed_indexes = []
                for index in range(3):
                    if state[index] != next_state[index]:
                        changed_indexes.append(index)

                factor = self.env.config.factor_for_action(action)
                self.assertEqual(changed_indexes, [factor_index[factor]])

    def test_action_order_and_invalid_actions(self):
        """检查动作顺序固定，无效动作不会变成 self-loop。"""
        expected_actions = [
            UP,
            RIGHT,
            HEAD_BLACK,
            HEAD_WHITE,
            TAIL_BLACK,
            TAIL_WHITE,
            HEAT,
            CHOP,
        ]
        self.assertEqual(self.env.actions(self.env.initial_state), expected_actions)
        self.assertAlmostEqual(self.env.discount_factor, 0.95)

        self.assertNotIn(LEFT, self.env.actions(self.env.initial_state))
        with self.assertRaises(ValueError):
            self.env.transitions(self.env.initial_state, LEFT)
        with self.assertRaises(ValueError):
            self.env.transitions(self.env.initial_state, "unknown-action")

    def test_markov_state_does_not_depend_on_history(self):
        """两条历史到达同一状态后，应得到相同动作和转移。"""
        state_head_first = self.follow([HEAD_WHITE, TAIL_WHITE])
        state_tail_first = self.follow([TAIL_WHITE, HEAD_WHITE])

        self.assertEqual(state_head_first, state_tail_first)
        self.assertEqual(
            self.env.actions(state_head_first),
            self.env.actions(state_tail_first),
        )
        self.assertEqual(
            self.env.transitions(state_head_first, UP),
            self.env.transitions(state_tail_first, UP),
        )

    def test_terminal_state(self):
        """检查目标状态终止，并且不能继续执行动作。"""
        self.assertTrue(self.env.is_terminal(GOAL_STATE))
        self.assertEqual(self.env.actions(GOAL_STATE), [])

        with self.assertRaises(ValueError):
            self.env.transitions(GOAL_STATE, UP)
        with self.assertRaises(ValueError):
            self.env.reward(GOAL_STATE, UP)

    def test_bfs_excludes_disconnected_key_state(self):
        """删除 Key=(2,2) 的入边后，BFS 不应声明该状态可达。"""
        remaining_edges = []
        for edge in KEY_GRAPH.transitions:
            if edge.target != (2, 2):
                remaining_edges.append(edge)

        # replace 会复制 dataclass，只替换这里指定的字段。
        disconnected_key_graph = replace(
            KEY_GRAPH,
            transitions=tuple(remaining_edges),
        )
        disconnected_config = replace(
            INDEPENDENT_TASK,
            task_name="disconnected_key_test",
            key_graph=disconnected_key_graph,
        )
        disconnected_env = FactoredMinecraftMDP(disconnected_config)

        # 9 个 Location × 8 个可达 Key × 9 个 Beef = 648。
        self.assertEqual(len(disconnected_env.states), 648)
        for state in disconnected_env.states:
            self.assertNotEqual(state[1], (2, 2))

        unreachable_state = (
            disconnected_env.initial_state[0],
            (2, 2),
            disconnected_env.initial_state[2],
        )
        with self.assertRaises(ValueError):
            disconnected_env.actions(unreachable_state)


if __name__ == "__main__":
    unittest.main(verbosity=2)
