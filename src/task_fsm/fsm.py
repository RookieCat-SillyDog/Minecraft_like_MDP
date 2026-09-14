"""Task FSM
"""

class TaskFSM:
    def __init__(self, definition):

        self.definition = definition
        self.initial_state = definition["initial_state"]
        self.terminal_states = set(definition["terminal_states"])
        self.transitions = {
            (item["from"], item["event"]): item["to"]
            for item in definition["transitions"]
        }
        self.current_state = self.initial_state

    def reset(self):
        """回到初始状态。"""
        self.current_state = self.initial_state
        return self.current_state

    def step(self, events):
        """接收事件集合，按定义转移，返回新状态。
        """
        for event in events:
            transition = (self.current_state, event)
            if transition in self.transitions:
                self.current_state = self.transitions[transition]
        return self.current_state

    @property
    def is_terminal(self):
        return self.current_state in self.terminal_states
