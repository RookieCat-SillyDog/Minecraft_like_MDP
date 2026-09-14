
from psychopy import visual


class NavigationView:
    def __init__(self, window, map_config):
        self.window = window
        self.rows = map_config["rows"]
        self.cols = map_config["cols"]
        self.walls = {tuple(position) for position in map_config["walls"]}
        self.objects = {
            name: tuple(position)
            for name, position in map_config["objects"].items()
        }
        self.center_x = -0.38
        self.center_y = -0.03
        self.cell_size = 0.095

    def _cell_center(self, position):
        row, col = position
        x = self.center_x + (col - (self.cols - 1) / 2) * self.cell_size
        y = self.center_y + ((self.rows - 1) / 2 - row) * self.cell_size
        return x, y

    def _draw_cell_label(self, position, text, color):
        x, y = self._cell_center(position)
        visual.TextStim(
            self.window,
            text=text,
            pos=(x, y),
            height=0.034,
            color=color,
            bold=True,
        ).draw()

    def draw(self, state):
        visual.TextStim(
            self.window,
            text="Physical / Navigation State Space",
            pos=(self.center_x, 0.43),
            height=0.036,
            color="white",
        ).draw()

        for row in range(self.rows):
            for col in range(self.cols):
                x, y = self._cell_center((row, col))
                fill_color = "#38414d"
                if (row, col) in self.walls:
                    fill_color = "#171b21"
                visual.Rect(
                    self.window,
                    width=self.cell_size,
                    height=self.cell_size,
                    pos=(x, y),
                    fillColor=fill_color,
                    lineColor="#78808c",
                ).draw()

        self._draw_cell_label(self.objects["key"], "K", "#ffd166")
        self._draw_cell_label(self.objects["beef"], "B", "#ef8354")
        self._draw_cell_label(self.objects["kitchen"], "C", "#74c69d")
        self._draw_cell_label(self.objects["goal"], "G", "#90dbf4")

        door_x, door_y = self._cell_center(self.objects["door"])
        if state["door_open"]:
            door_color = "#70d6ff"
            visual.Line(
                self.window,
                start=(door_x - self.cell_size * 0.30, door_y - self.cell_size * 0.30),
                end=(door_x - self.cell_size * 0.30, door_y + self.cell_size * 0.30),
                lineColor=door_color,
                lineWidth=3,
            ).draw()
            visual.Line(
                self.window,
                start=(door_x + self.cell_size * 0.30, door_y - self.cell_size * 0.30),
                end=(door_x + self.cell_size * 0.30, door_y + self.cell_size * 0.30),
                lineColor=door_color,
                lineWidth=3,
            ).draw()
        else:
            door_color = "#d1495b"
            visual.Rect(
                self.window,
                width=self.cell_size * 0.18,
                height=self.cell_size * 0.72,
                pos=(door_x, door_y),
                fillColor=door_color,
                lineColor=door_color,
            ).draw()
        self._draw_cell_label(self.objects["door"], "D", "white")

        agent_x, agent_y = self._cell_center(state["position"])
        visual.Circle(
            self.window,
            radius=self.cell_size * 0.22,
            pos=(agent_x + self.cell_size * 0.22, agent_y - self.cell_size * 0.22),
            fillColor="#ffffff",
            lineColor="#20242b",
        ).draw()
