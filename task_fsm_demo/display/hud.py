"""条件、操作说明和任务反馈的 PsychoPy 绘制。"""

from psychopy import visual


class HUD:
    def __init__(self, window):
        self.window = window

    def draw(self, task_definition, recent_event="", completed=False):
        condition_text = (
            f"Condition {task_definition['condition']}: "
            f"{task_definition['name']}"
        )
        visual.TextStim(
            self.window,
            text=condition_text,
            pos=(-0.38, 0.35),
            height=0.029,
            color="#dbe4ee",
            wrapWidth=0.55,
        ).draw()

        event_text = f"Last event: {recent_event or '-'}"
        visual.TextStim(
            self.window,
            text=event_text,
            pos=(-0.38, -0.32),
            height=0.028,
            color="#f4d35e",
            bold=True,
        ).draw()

        visual.TextStim(
            self.window,
            text="Arrow keys: move    R: reset    1/2: condition    Esc: quit",
            pos=(-0.38, -0.37),
            height=0.025,
            color="#b8c0cc",
            wrapWidth=0.62,
        ).draw()

        visual.TextStim(
            self.window,
            text=task_definition["instruction"],
            pos=(0, -0.46),
            height=0.025,
            color="white",
            wrapWidth=1.25,
        ).draw()

        if completed:
            visual.TextStim(
                self.window,
                text="Task complete - press R to restart or 1/2 to switch",
                pos=(0.38, 0.36),
                height=0.029,
                color="#74c69d",
                bold=True,
                wrapWidth=0.60,
            ).draw()
