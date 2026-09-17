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

## Reward Machine 最小复现

已实现RM 表示、OfficeWorld、Product MDP、Value Iteration、策略对比图，以及 Q-learning 与 QRM 学习对照。

### 依赖

```powershell
python -m pip install -r requirements.txt
```

核心依赖：PyYAML、numpy、matplotlib、pytest、nbconvert 和 ipykernel。PsychoPy 仅 Demo 需要，使用独立 `week4-demo` 环境。

### 重建策略图

```powershell
python -m experiments.make_policy_figure   # 输出 figures/policy_comparison.svg 和 .png
```

### 重建学习曲线与原始结果

```powershell
python -m experiments.make_learning_curves
```

该命令运行10个随机种子、两个任务和两种方法，输出：

- `experiments/results/learning_curves.csv`
- `figures/learning_curves_coffee_office.{svg,png}`
- `figures/learning_curves_visit_abcd.{svg,png}`

### 从头执行笔记本

```powershell
cd notebooks
python -m nbconvert --to notebook --execute --inplace 01_reward_machine.ipynb
```


## 当前结构

```text
src/
├── config.py
├── envs/{minecraft_grid,officeworld}.py
├── task_fsm/{fsm,labeling,reward_machine}.py
└── algorithms/{product_mdp,value_iteration,q_learning,qrm}.py

configs/
├── maps/{map_01,officeworld_minimal}.yaml
├── tasks/{task_01,task_02}.yaml
└── reward_machines/{coffee_office,visit_abcd}.yaml

tests/   test_gridworld, test_event_detector, test_fsm, test_routes,
         test_reward_machine, test_officeworld, test_value_iteration,
         test_q_learning, test_qrm

experiments/make_policy_figure.py    重建策略对比图
experiments/make_learning_curves.py  重建学习曲线与逐种子 CSV
notebooks/01_reward_machine.ipynb    RM 复现笔记本
figures/policy_comparison.{svg,png}   状态价值热力图与最优策略对比
figures/learning_curves_*.{svg,png}   Q-learning 与 QRM 学习曲线
notes/paper_01_reward_machine.md      实验定义与验收

task_fsm_demo/   PsychoPy 演示（依赖 week4-demo 环境）
```
