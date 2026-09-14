"""实验动作和控制记录的 CSV 写入。"""

import csv
import json
from datetime import datetime
from pathlib import Path


FIELDNAMES = [
    "participant",
    "session",
    "condition",
    "trial",
    "timestamp",
    "step",
    "record_type",
    "trial_status",
    "navigation_state_before",
    "navigation_state_after",
    "fsm_state_before",
    "fsm_state_after",
    "action",
    "event",
    "RT",
]


class ExperimentLogger:
    def __init__(self, participant="demo", data_dir=None):
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data"

        self.participant = participant
        self.session = datetime.now().strftime("%Y%m%dT%H%M%S%f")
        data_dir = Path(data_dir)
        data_dir.mkdir(parents=True, exist_ok=True)
        self.path = (
            data_dir
            / f"sub-{self.participant}_session-{self.session}.csv"
        )
        self.file = self.path.open("x", newline="", encoding="utf-8")
        self.writer = csv.DictWriter(self.file, fieldnames=FIELDNAMES)
        self.writer.writeheader()
        self.file.flush()

    def log(
        self,
        *,
        condition,
        trial,
        step,
        record_type,
        trial_status,
        navigation_state_before=None,
        navigation_state_after=None,
        fsm_state_before="",
        fsm_state_after="",
        action="",
        event="",
        rt=None,
    ):
        """写入一条动作或 trial 控制记录。"""
        row = {
            "participant": self.participant,
            "session": self.session,
            "condition": condition,
            "trial": trial,
            "timestamp": datetime.now().astimezone().isoformat(
                timespec="milliseconds"
            ),
            "step": step,
            "record_type": record_type,
            "trial_status": trial_status,
            "navigation_state_before": self._serialize_state(
                navigation_state_before
            ),
            "navigation_state_after": self._serialize_state(
                navigation_state_after
            ),
            "fsm_state_before": fsm_state_before,
            "fsm_state_after": fsm_state_after,
            "action": action,
            "event": event,
            "RT": "" if rt is None else f"{rt:.6f}",
        }
        self.writer.writerow(row)
        self.file.flush()

    def _serialize_state(self, state):
        if state is None:
            return ""
        return json.dumps(state, ensure_ascii=False, sort_keys=True)

    def close(self):
        self.file.close()
