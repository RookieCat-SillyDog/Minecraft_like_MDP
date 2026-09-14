
import unittest

from src.config import load_task_config
from src.task_fsm.fsm import TaskFSM


class TestTaskFSM(unittest.TestCase):

    def make(self, condition):
        return TaskFSM(load_task_config(condition))

    def test_condition_a_full_sequence(self):
        """Condition A：按顺序完成全部事件，到达终止状态 u5。"""
        fsm = self.make("A")
        self.assertEqual(fsm.current_state, "u0")
        for event, expected in [
            ("GET_KEY", "u1"),
            ("OPEN_DOOR", "u2"),
            ("GET_BEEF", "u3"),
            ("COOK", "u4"),
            ("REACH_GOAL", "u5"),
        ]:
            fsm.step({event})
            self.assertEqual(fsm.current_state, expected)
        self.assertTrue(fsm.is_terminal)

    def test_condition_a_out_of_order_events_are_ignored(self):
        """顺序任务里的事件乱序出现：FSM 停留原状态。"""
        fsm = self.make("A")
        fsm.step({"GET_BEEF"})  # u0 不认识 GET_BEEF
        self.assertEqual(fsm.current_state, "u0")
        fsm.step({"REACH_GOAL"})
        self.assertEqual(fsm.current_state, "u0")
        fsm.step({"GET_KEY"})
        fsm.step({"REACH_GOAL"})  # u1 也不能直接到终点
        self.assertEqual(fsm.current_state, "u1")

    def test_condition_b_key_route(self):
        """Condition B：钥匙—门—目标路线。"""
        fsm = self.make("B")
        self.assertEqual(fsm.current_state, "v0")
        fsm.step({"GET_KEY"})
        fsm.step({"OPEN_DOOR"})
        self.assertEqual(fsm.current_state, "v2")
        fsm.step({"REACH_GOAL"})
        self.assertEqual(fsm.current_state, "v5")
        self.assertTrue(fsm.is_terminal)

    def test_condition_b_beef_route(self):
        """Condition B：牛肉—烹饪—目标路线，全程不需要钥匙。"""
        fsm = self.make("B")
        fsm.step({"GET_BEEF"})
        fsm.step({"COOK"})
        fsm.step({"REACH_GOAL"})
        self.assertEqual(fsm.current_state, "v5")
        self.assertTrue(fsm.is_terminal)

    def test_condition_b_first_event_chooses_route(self):
        """B 的第一个事件决定路线，另一条路线的事件被忽略。"""
        fsm = self.make("B")
        fsm.step({"GET_KEY"})  # 进入钥匙路线
        fsm.step({"GET_BEEF"})  # 与当前路线无关
        self.assertEqual(fsm.current_state, "v1")
        fsm.step({"OPEN_DOOR"})
        fsm.step({"COOK"})  # 同样被忽略
        self.assertEqual(fsm.current_state, "v2")

    def test_empty_and_unknown_events_keep_state(self):
        fsm = self.make("A")
        fsm.step(set())
        self.assertEqual(fsm.current_state, "u0")
        fsm.step({"NOT_AN_EVENT"})
        self.assertEqual(fsm.current_state, "u0")

    def test_reset(self):
        fsm = self.make("A")
        fsm.step({"GET_KEY"})
        fsm.step({"OPEN_DOOR"})
        self.assertEqual(fsm.reset(), "u0")
        self.assertEqual(fsm.current_state, "u0")
        self.assertFalse(fsm.is_terminal)

    def test_terminal_state_absorbs_events(self):
        """到达终止状态后，继续传入事件也停留在终止状态。"""
        fsm = self.make("A")
        for event in ["GET_KEY", "OPEN_DOOR", "GET_BEEF", "COOK", "REACH_GOAL"]:
            fsm.step({event})
        fsm.step({"GET_KEY"})
        self.assertEqual(fsm.current_state, "u5")
        self.assertTrue(fsm.is_terminal)


if __name__ == "__main__":
    unittest.main()
