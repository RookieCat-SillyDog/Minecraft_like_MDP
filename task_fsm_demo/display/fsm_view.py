"""右侧 Task FSM 的 PsychoPy 绘制。"""

from math import atan2, cos, sin

from psychopy import visual


class FSMView:
    def __init__(self, window):
        self.window = window
        self.left = 0.08
        self.right = 0.62
        self.bottom = -0.34
        self.top = 0.27
        self.node_radius = 0.042

    def _node_positions(self, definition):
        states = definition["states"]
        x_values = [state["position"][0] for state in states]
        y_values = [state["position"][1] for state in states]
        min_x, max_x = min(x_values), max(x_values)
        min_y, max_y = min(y_values), max(y_values)
        positions = {}

        for state in states:
            x, y = state["position"]
            if min_x == max_x:
                screen_x = (self.left + self.right) / 2
            else:
                screen_x = self.left + (x - min_x) / (max_x - min_x) * (self.right - self.left)
            if min_y == max_y:
                screen_y = (self.bottom + self.top) / 2
            else:
                screen_y = self.top - (y - min_y) / (max_y - min_y) * (self.top - self.bottom)
            positions[state["id"]] = (screen_x, screen_y)
        return positions

    def _draw_arrow(self, start, end, label, highlighted):
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        angle = atan2(dy, dx)
        start_x = start[0] + cos(angle) * self.node_radius
        start_y = start[1] + sin(angle) * self.node_radius
        end_x = end[0] - cos(angle) * self.node_radius
        end_y = end[1] - sin(angle) * self.node_radius
        edge_color = "#f4d35e" if highlighted else "#aab4c3"
        edge_width = 4 if highlighted else 2

        visual.Line(
            self.window,
            start=(start_x, start_y),
            end=(end_x, end_y),
            lineColor=edge_color,
            lineWidth=edge_width,
        ).draw()

        arrow_size = 0.014
        for offset in (0.55, -0.55):
            arrow_x = end_x - cos(angle + offset) * arrow_size
            arrow_y = end_y - sin(angle + offset) * arrow_size
            visual.Line(
                self.window,
                start=(end_x, end_y),
                end=(arrow_x, arrow_y),
                lineColor=edge_color,
                lineWidth=edge_width,
            ).draw()

        label_x = (start_x + end_x) / 2 - sin(angle) * 0.025
        label_y = (start_y + end_y) / 2 + cos(angle) * 0.025
        visual.TextStim(
            self.window,
            text=label,
            pos=(label_x, label_y),
            height=0.027,
            color=edge_color,
            bold=highlighted,
            anchorHoriz="center",
        ).draw()

    def draw(self, definition, current_state, last_transition=None):
        """根据任务定义绘制 FSM"""
        visual.Line(
            self.window,
            start=(0, -0.48),
            end=(0, 0.48),
            lineColor="#4b5563",
            lineWidth=1,
        ).draw()
        visual.TextStim(
            self.window,
            text="Abstract Task State Space / FSM",
            pos=((self.left + self.right) / 2, 0.43),
            height=0.036,
            color="white",
        ).draw()

        positions = self._node_positions(definition)
        for transition in definition["transitions"]:
            transition_key = (
                transition["from"],
                transition["event"],
                transition["to"],
            )
            self._draw_arrow(
                positions[transition["from"]],
                positions[transition["to"]],
                transition["event"],
                transition_key == last_transition,
            )

        terminal_states = set(definition["terminal_states"])
        for state in definition["states"]:
            state_id = state["id"]
            position = positions[state_id]
            is_current = state_id == current_state
            is_terminal = state_id in terminal_states

            if is_terminal:
                visual.Circle(
                    self.window,
                    radius=self.node_radius + 0.009,
                    pos=position,
                    fillColor=None,
                    lineColor="#74c69d",
                    lineWidth=2,
                ).draw()
            if is_current:
                visual.Circle(
                    self.window,
                    radius=self.node_radius + 0.016,
                    pos=position,
                    fillColor=None,
                    lineColor="#f4d35e",
                    lineWidth=3,
                ).draw()

            if is_current:
                fill_color = "#f4d35e"
                line_color = "#ffffff"
                text_color = "#20242b"
            else:
                fill_color = "#3d5a80"
                line_color = "#b8c0cc"
                text_color = "white"
            visual.Circle(
                self.window,
                radius=self.node_radius,
                pos=position,
                fillColor=fill_color,
                lineColor=line_color,
                lineWidth=3 if is_current else 1,
            ).draw()
            visual.TextStim(
                self.window,
                text=state_id,
                pos=position,
                height=0.029,
                color=text_color,
                bold=True,
            ).draw()
            visual.TextStim(
                self.window,
                text=state["label"],
                pos=(position[0], position[1] - 0.075),
                height=0.026,
                color="white",
                wrapWidth=0.16,
                alignText="center",
                anchorHoriz="center",
            ).draw()
