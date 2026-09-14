"""Task FSM Demo 启动入口。"""

import argparse
import sys
from pathlib import Path


if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the Navigation and Task FSM demo."
    )
    parser.add_argument(
        "--condition",
        type=str.upper,
        choices=["A", "B"],
        default="A",
        help="initial task condition (default: A)",
    )
    parser.add_argument(
        "--participant",
        default="demo",
        help="participant identifier used in the CSV filename (default: demo)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    from psychopy import core, visual

    from task_fsm_demo.experiment.controller import ExperimentController

    window = visual.Window(
        size=(1080, 720),
        color="#20242b",
        units="height",
        fullscr=False,
    )

    try:
        controller = ExperimentController(
            window,
            condition=args.condition,
            participant=args.participant,
        )
        controller.run()
    finally:
        window.close()

    core.quit()


if __name__ == "__main__":
    main()
