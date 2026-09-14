"""5x5 网格世界环境。
"""

ACTIONS = {
    "up": (-1, 0),
    "down": (1, 0),
    "left": (0, -1),
    "right": (0, 1),
}


class GridWorld:
    def __init__(self, map_config):
        self.rows = map_config["rows"]
        self.cols = map_config["cols"]
        self.start = tuple(map_config["start"])
        self.walls = {tuple(pos) for pos in map_config["walls"]}
        self.objects = {
            name: tuple(pos) for name, pos in map_config["objects"].items()
        }
        self.reset()

    def reset(self):
        """回到起点"""
        self.position = self.start
        self.has_key = False
        self.door_open = False
        self.has_beef = False
        self.cooked = False
        return self.state

    def step(self, action):
        """执行一次移动并更新"""
        drow, dcol = ACTIONS[action]
        target = (self.position[0] + drow, self.position[1] + dcol)

        if not self._can_enter(target):
            return self.state
        self.position = target

        if target == self.objects["door"] and self.has_key:
            self.door_open = True
        if target == self.objects["key"]:
            self.has_key = True
        if target == self.objects["beef"]:
            self.has_beef = True
        if target == self.objects["kitchen"] and self.has_beef:
            self.cooked = True

        return self.state

    def _can_enter(self, cell):
        row, col = cell
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            return False
        if cell in self.walls:
            return False
        if cell == self.objects["door"]:
            return self.door_open or self.has_key
        return True

    @property
    def state(self):
        return {
            "position": self.position,
            "has_key": self.has_key,
            "door_open": self.door_open,
            "has_beef": self.has_beef,
            "cooked": self.cooked,
        }
