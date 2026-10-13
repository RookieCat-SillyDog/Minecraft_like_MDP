"""PsychoPy 输入、环境、Reward Machine、显示和日志的控制流程。"""

from psychopy import core
from psychopy.hardware.keyboard import Keyboard

from src.config import load_map_config, load_task_config
from src.envs.minecraft_grid import GridWorld
from src.task_fsm.labeling import detect_events
from src.task_fsm.reward_machine import RewardMachine
from task_fsm_demo.display.fsm_view import FSMView
from task_fsm_demo.display.hud import HUD
from task_fsm_demo.display.navigation_view import NavigationView
from task_fsm_demo.experiment.logger import ExperimentLogger


KEY_TO_ACTION = {
    "up": "U",
    "down": "D",
    "left": "L",
    "right": "R",
}
RESPONSE_KEYS = list(KEY_TO_ACTION) + ["r", "1", "2", "escape"]


class ExperimentController:
    def __init__(self, window, condition="A", participant="demo"):
        self.window = window
        self.condition = condition.upper()
        map_config = load_map_config()
        self.task_definition = load_task_config(self.condition)
        self.environment = GridWorld(map_config)
        self.rm = RewardMachine(self.task_definition)
        self.u = self.rm.reset()

        self.navigation_view = NavigationView(window, map_config)
        self.fsm_view = FSMView(window)
        self.hud = HUD(window)
        self.logger = ExperimentLogger(participant)

        self.response_clock = core.Clock()
        self.keyboard = Keyboard(clock=self.response_clock)
        self.trial = 1
        self.step = 0
        self.recent_event = ""
        self.last_transition = None

    def run(self):
        """运行实验循环，直到参与者按下 Esc。"""
        try:
            self._draw_frame()
            self._log_trial_start()

            while True:
                response = self.keyboard.waitKeys(
                    keyList=RESPONSE_KEYS,
                    waitRelease=False,
                    clear=False,
                )[0]
                self.keyboard.clearEvents()
                key = response.name

                if key == "escape":
                    self._log_control("exit", key)
                    break
                if key == "r":
                    self._start_new_trial(self.condition, "reset", key)
                elif key == "1":
                    self._start_new_trial("A", "switch", key)
                elif key == "2":
                    self._start_new_trial("B", "switch", key)
                elif key in KEY_TO_ACTION and not self.rm.is_terminal(self.u):
                    self._move(KEY_TO_ACTION[key], response.rt)
        finally:
            self.logger.close()

    def _move(self, action, rt):
        navigation_before = self.environment.state
        u_before = self.u

        navigation_after = self.environment.step(action)
        events = detect_events(
            navigation_before,
            navigation_after,
            self.environment.objects,
        )
        self.u, reward = self.rm.next_state(self.u, events)
        event_name = next(iter(events), "")
        self.recent_event = event_name
        self.last_transition = None
        if self.u != u_before:
            self.last_transition = (u_before, event_name, self.u)
        self.step += 1

        self._draw_frame()
        status = "completed" if self.rm.is_terminal(self.u) else "ongoing"
        self.logger.log(
            condition=self.condition,
            trial=self.trial,
            step=self.step,
            record_type="action",
            trial_status=status,
            navigation_state_before=navigation_before,
            navigation_state_after=navigation_after,
            rm_state_before=u_before,
            rm_state_after=self.u,
            action=action,
            event=event_name,
            reward=reward,
            rt=rt,
        )

        if self.rm.is_terminal(self.u):
            self._log_control("complete", "")

    def _start_new_trial(self, condition, record_type, action):
        self._log_control(record_type, action)

        self.trial += 1
        self.step = 0
        self.condition = condition
        self.task_definition = load_task_config(condition)
        self.environment.reset()
        self.rm = RewardMachine(self.task_definition)
        self.u = self.rm.reset()
        self.recent_event = ""
        self.last_transition = None

        self._draw_frame()
        self._log_trial_start()

    def _draw_frame(self):
        self.navigation_view.draw(self.environment.state)
        self.fsm_view.draw(
            self.task_definition,
            self.u,
            self.last_transition,
        )
        self.hud.draw(
            self.task_definition,
            self.recent_event,
            self.rm.is_terminal(self.u),
        )
        self.window.callOnFlip(self.response_clock.reset)
        self.window.callOnFlip(self.keyboard.clearEvents)
        self.window.flip()

    def _log_trial_start(self):
        self.logger.log(
            condition=self.condition,
            trial=self.trial,
            step=self.step,
            record_type="start",
            trial_status="ongoing",
            navigation_state_after=self.environment.state,
            rm_state_after=self.u,
        )

    def _log_control(self, record_type, action):
        status = "completed" if self.rm.is_terminal(self.u) else "aborted"
        state = self.environment.state
        self.logger.log(
            condition=self.condition,
            trial=self.trial,
            step=self.step,
            record_type=record_type,
            trial_status=status,
            navigation_state_before=state,
            navigation_state_after=state,
            rm_state_before=self.u,
            rm_state_after=self.u,
            action=action,
        )
