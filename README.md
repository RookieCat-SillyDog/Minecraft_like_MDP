# Navigation × Reward Machine

当前仓库包含两部分工作：

- `src/`：与界面无关的环境、事件标注、Reward Machine 和学习算法；
- `task_fsm_demo/`：使用共享核心的 PsychoPy 双空间演示。

旧的 Week 1–3 MDP 练习、原层级 Q-learning 算法和 Delivery BFS 奖励基线只保存在本地 `archive/`，不再随仓库提供。

图和数据按任务整理：现存 `figures/` 图表纳入仓库，`experiments/results/` 全目录由 `.gitignore` 排除，CSV、JSON和模型仅保留在本地：

| 内容 | 数据目录 | 图表目录 |
| --- | --- | --- |
| Q-learning / QRM 基础示例 | `experiments/results/qrm_examples/` | `figures/qrm_examples/` |
| Book 原层级 Q-learning 历史 CSV | `experiments/results/book/` | `figures/book/` 仅保留地图和 RM |
| Delivery 高层步数折扣前基线及低层诊断 | `experiments/results/delivery/` | `figures/delivery/` 保留地图、RM和VI参考 |
| Delivery 最新高层步数折扣结果 | `experiments/results/` 中的 `*_duration_discount*` | `figures/` 中的同前缀曲线；过程图在 `figures/delivery/` |

脚本输出路径暂未修改，重跑仍写入 `experiments/results/` 和 `figures/`，不会自动分类。Delivery 的地图、实验条件和本地历史结果说明见 [任务文档](docs/pacman-delivery-task-review.md)。

2026-10-13第一轮本地清理删除81个旧结果和图表；随后按用户指定删除高层决策、局部绕路、路线对比的6个PNG/SVG和专用路线诊断JSON。当前保留18个数据/模型文件和22个PNG/SVG，包括最新92步结果、必要的120/116步基线、最终低层诊断、基础QRM结果、旧Book CSV和线性5k检查。上述三类图没有独立CSV，共享的学习曲线、模型和轨迹仍保留。`tmp/`中的模型和验证记录本轮未清理。

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

该命令重新执行笔记本，包括基础 Q-learning/QRM 实验，并生成新的结果与图表。

## Book 表格型 h-DQN 实验

```powershell
python -B -u -m experiments.run_hrm_craftworld_book
```

当前入口比较 Q-learning、QRM 和表格型 h-DQN。沿用种子 0–4、每种子每方法 50k 交互预算、每 1k 步评估 20 回合，回合上限为 200。h-DQN 不做独立预训练，从第一步开始联合训练；低层为四个地标目标生成经验，两层使用现有 `tabular_hdqn.py` 的回放更新。

新 CSV 为 `experiments/results/hrm_craftworld_book_tabular_hdqn_learning_curves.csv`，图表为 `figures/hrm_craftworld_book_tabular_hdqn_learning_curve.{png,svg}`。`experiments/results/book/` 中保留的是旧层级 Q-learning 的历史CSV；`figures/book/` 只保留任务地图和RM图。旧曲线与过程图已删除，历史CSV不能当作新版h-DQN结果。新版完整50k实验尚未运行。

## Delivery h-DQN 实验

在仓库根目录运行表格型 h-DQN/QRM 对照：

```powershell
python -B -u -m experiments.run_pacman_delivery_hdqn_vs_qrm
```

共享的六目标与二值奖励任务接口在 `src/tasks/pacman_delivery.py`。表格主实验的训练和完整任务评估均从固定起点 `(6, 12)` 开始。默认保存五列CSV（算法、种子、训练步数、成功率、平均基础步数）、两张曲线、地图/RM/数值参数和最终 `_models.pkl`；每种方法完成后立即写入CSV。

主实验不做单目标导航检查，也不保存逐步过程。`evaluate_low_goals` 已移到路线诊断模块，仅供单独诊断和历史脚本调用；它检查起点及其他地标的导航，不改变训练起点。第一轮清理保留必要的历史CSV和诊断结果，其余旧产物已删除。

逐步路线记录使用独立命令。先运行上述表格主实验生成 `_models.pkl`，再从最终模型记录路线；路线命令本身不训练：

```powershell
$deliveryPrefix = 'pacman_delivery_hdqn_vs_qrm_seed5_200k_all_goals_navigation_bootstrap_pretrain1000_qrm_train1000_duration_discount'
python -B -m experiments.record_pacman_delivery_routes "experiments/results/${deliveryPrefix}_models.pkl"
```

路线JSON保存在模型所在目录，沿用同前缀 `_routes.json` 格式。此入口读取新的双方法 `_models.pkl`，不读取旧单方法 `_checkpoint.pkl`。训练和图表输出目录保持原设置。

Delivery路径/目标时间线位于 `figures/delivery/`；地图、RM与VI最优价值/策略图也纳入仓库。高层决策、路线对比、局部绕路图及其专用路线诊断JSON已删除。Book旧过程图已删除，旧模型和绘图脚本仍留在本地 `tmp/`。线性低层算法、实验入口及测试也暂留本地，不属于当前仓库入口。

## 当前结构

```text
src/
├── config.py
├── envs/{minecraft_grid,officeworld}.py
├── tasks/pacman_delivery.py
├── task_fsm/{fsm,labeling,reward_machine}.py
└── algorithms/
    ├── {product_mdp,value_iteration,q_learning,qrm}.py
    └── tabular_hdqn.py

configs/
├── maps/{map_01,officeworld_minimal,hrm_craftworld_book,pacman_delivery}.yaml
├── tasks/{task_01,task_02}.yaml
└── reward_machines/{coffee_office,visit_abcd,hrm_craftworld_book,pacman_delivery}.yaml

tests/   test_gridworld, test_event_detector, test_fsm, test_routes,
         test_reward_machine, test_officeworld, test_value_iteration,
         test_q_learning, test_qrm, test_book_task,
         test_tabular_hdqn

experiments/make_policy_figure.py    重建策略对比图
experiments/make_learning_curves.py  重建学习曲线与逐种子 CSV
experiments/run_hrm_craftworld_book.py    Book 表格 h-DQN 对照
experiments/run_pacman_delivery_hdqn_vs_qrm.py   表格 h-DQN/QRM 对照
experiments/record_pacman_delivery_routes.py    从最终模型记录路线
notebooks/01_reward_machine.ipynb    RM 复现笔记本
experiments/results/  重跑时生成的数据与模型
figures/              重跑时生成的图表
notes/paper_01_reward_machine.md      实验定义与验收

task_fsm_demo/   PsychoPy 演示（依赖 week4-demo 环境）
```
