"""配置驱动的有限状态 Reward Machine。"""


class RewardMachine:
    def __init__(self, definition):
        self.initial_state = definition["initial_state"]
        self.terminal_states = set(definition["terminal_states"])
        self.transitions = definition["transitions"]
        self.states = {self.initial_state}
        self.states.update(self.terminal_states)
        for transition in self.transitions:
            self.states.add(transition["from"])
            self.states.add(transition["to"])

    def reset(self):
        return self.initial_state

    def is_terminal(self, u):
        return u in self.terminal_states

    def next_state(self, u, label_set):
        """终止状态吸收；没有匹配事件时保持原状态。"""
        if u in self.terminal_states:
            return u, 0
        labels = set(label_set)
        for t in self.transitions:
            if t["from"] == u and set(t["match"]) == labels:
                return t["to"], t["reward"]
        return u, 0

    def reward(self, u, u_next):
        for t in self.transitions:
            if t["from"] == u and t["to"] == u_next:
                return t["reward"]
        return 0
