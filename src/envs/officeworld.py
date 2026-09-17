"""确定性四邻接 OfficeWorld。"""

ACTION_DELTAS = {
    "U": (-1, 0),
    "D": (1, 0),
    "L": (0, -1),
    "R": (0, 1),
}


class OfficeWorld:
    actions = tuple(ACTION_DELTAS)

    def __init__(self, map_config):
        self.rows = map_config["rows"]
        self.cols = map_config["cols"]
        self.start = tuple(map_config["start"])
        self.walls = {tuple(pos) for pos in map_config["walls"]}
        self._prop_at = {
            tuple(pos): prop for prop, pos in map_config["landmarks"].items()
        }
        self.position = self.start

    @property
    def positions(self):
        return [
            (r, c)
            for r in range(self.rows)
            for c in range(self.cols)
            if (r, c) not in self.walls
        ]

    def reset(self):
        self.position = self.start
        return self.position

    def next_position(self, pos, action):
        drow, dcol = ACTION_DELTAS[action]
        target = (pos[0] + drow, pos[1] + dcol)
        if self._can_enter(target):
            return target
        return pos

    def step(self, action):
        self.position = self.next_position(self.position, action)
        return self.position

    def label(self, pos):
        """命中地标的命题集合；普通格返回空集。"""
        prop = self._prop_at.get(tuple(pos))
        return {prop} if prop else set()

    def _can_enter(self, cell):
        r, c = cell
        if not (0 <= r < self.rows and 0 <= c < self.cols):
            return False
        if cell in self.walls:
            return False
        return True
