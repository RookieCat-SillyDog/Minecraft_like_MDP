# Navigation × Task-FSM / Reward Machine

当前仓库包含两部分工作：

- `src/`：与界面无关的环境、事件标注和任务状态机核心；
- `task_fsm_demo/`：使用共享核心的 PsychoPy 双空间演示。

旧的 Week 1–3 MDP 练习保存在 `archive/old_mdp_week1_3/`。

## 运行 Demo

在仓库根目录执行：

```powershell
conda activate week4-demo
python -m task_fsm_demo.main
```

指定条件和参与者：

```powershell
python -m task_fsm_demo.main --condition B --participant sub001
```

## 运行测试

```powershell
python -B -m unittest discover -s tests -p "test_*.py"
```

当前测试覆盖 GridWorld、事件标注、Task FSM 和 A/B 两类完整路线，不依赖 PsychoPy。

## 当前结构

```text
src/
├── config.py
├── envs/minecraft_grid.py
└── task_fsm/
    ├── fsm.py
    └── labeling.py

configs/
├── maps/map_01.yaml
└── tasks/
    ├── task_01.yaml
    └── task_02.yaml

task_fsm_demo/
├── main.py
├── display/
├── experiment/
└── data/

tests/
```

后续 Reward Machine、Product MDP 和 QRM 实现在 `src/` 中扩展；PsychoPy 显示与实验记录继续留在 `task_fsm_demo/`。
