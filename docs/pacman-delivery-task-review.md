# Pacman Delivery 最小实验

## 任务范围

当前实验只保留原仓库的 `K1-01` 布局和 `free` 条件，用于研究层级 Q 学习。

智能体在 18×33 的静态网格中移动。环境状态只包含位置，Reward Machine（奖励机，RM）记录三件包裹的进度：

```text
z_i = 0    尚未取件
z_i = 1    已取件
z_i = 2    已送达
```

RM 状态写作 `v(z_a)(z_b)(z_c)`。初始状态是 `v000`，终止状态是 `v222`。只有进入 `v222` 的转移获得奖励 1。

`free` 条件允许取走任意尚未取走的包裹，也允许送达任意已经携带的包裹。该任务的最优路径长度是 92 步。

## 配置

实验只读取两个 YAML 文件：

```text
configs/maps/pacman_delivery.yaml
configs/reward_machines/pacman_delivery.yaml
```

地图文件用 18 行字符直接画出固定布局：`#` 表示墙，`.` 表示通路，`S` 表示起点，小写 `a/b/c` 表示取货点，大写 `A/B/C` 表示对应的送货点。加载函数将字符地图转换成 `OfficeWorld` 使用的墙体、起点和地标坐标。配置不依赖生成脚本或相邻的 `pacman-delivery` 仓库。

奖励机文件固定保存 `free` 条件的 27 个状态和 54 条有效转移。

## 实验条件与入口

以下命令均在仓库根目录执行。当前仓库提供表格型 h-DQN/QRM 对照；旧 BFS 奖励基线已转为本地归档，线性低层实验暂留本地。本地新增的历史结果、模型和图表不属于本次代码提交。各条件共享地图和 RM，但低层获得的信息不同，不能把它们当成同一条件的结果。

| 实验 | 入口 | 低层奖励与信息 | 高层目标 |
| --- | --- | --- | --- |
| 层级 Q 学习历史基线 | 仅本地 `archive/run_pacman_delivery.py`，不再维护 | BFS 距离奖励、步长代价和到达奖励 | 由 RM 出边限制 |
| 表格型 h-DQN / QRM 对照 | `experiments.run_pacman_delivery_hdqn_vs_qrm` | h-DQN 使用二值到达奖励，无 BFS 奖励 | h-DQN 选择六个固定地标，只排除脚下地标；QRM 无高层目标 |
| 线性低层 h-DQN | 仅本地实验，暂不提交 | 二值到达奖励，加完整地图 BFS 特征 | 与表格型 h-DQN 相同 |

### 层级 Q 学习历史基线

原 `experiments/run_pacman_delivery.py` 及其层级算法、训练模块已移入本地 `archive/`，不再作为仓库入口。历史低层使用 BFS 距离变化、每步 `-0.01` 和到达奖励 `1`，高层目标由 RM 出边限制。

本地已保存结果位于 `experiments/results/delivery/baselines/pacman_delivery_hq_learning.csv`。种子 5–9，每种子 5 万步预训练＋20 万步联合训练，最终均成功、平均评估步数均为 92。这些数据保留作历史参照，不属于当前二值奖励的 h-DQN 实验。

### 表格型 h-DQN / QRM 对照

```powershell
python -B -u -m experiments.run_pacman_delivery_hdqn_vs_qrm
```

共享任务接口在 `src/tasks/pacman_delivery.py`：高层状态为 `(position, rm_state)`，低层状态为位置，六个固定目标为 `p_a,p_b,p_c,d_a,d_b,d_c`。训练与完整任务评估都从固定起点 `(6,12)` 和 RM 初始状态开始，不按 RM 出边限制目标。

低层到达目标时奖励为 1，否则为 0；同一次移动为多个导航目标写入经验，再从经验池抽样更新。只有对应目标到达时停止低层 bootstrap；RM 完成或采样超时停止采样，但保留未到达目标的后续价值。高层按选项内基础步数折扣奖励，并以 `gamma ** duration` 折扣下一状态价值。

默认只运行 seed5。h-DQN 使用 5 万步低层预训练和 15 万步联合训练，QRM 使用 20 万步训练；预算仅统计真实环境交互。h-DQN 预训练回合上限为 1,000，联合训练和评估为 300；QRM 训练为 1,000、评估为 300。每 1,000 步评估 10 个回合。

主实验输出五列 CSV（算法、种子、训练步数、成功率、平均基础步数）、设置 JSON、两张曲线和最终 `_models.pkl`，每种方法完成后立即写入 CSV。数据和图表输出目录仍为 `experiments/results/` 和 `figures/`，不自动执行单目标导航诊断或记录逐步路线。

本地历史结果需要区分两个版本，以下分类数据未纳入本次提交：

| 版本 | 数据位置 | h-DQN 最终成功率 / 步数 | QRM 最终成功率 / 步数 |
| --- | --- | --- | --- |
| 高层按选项折扣的旧基线 | `experiments/results/delivery/` 中的 `*_qrm_train1000.csv` | 1.0 / 120 | 1.0 / 116 |
| 高层按基础步数折扣 | `experiments/results/` 中的 `*_duration_discount.csv` | 1.0 / 92 | 沿用旧结果作参照 |

最新保存的步数折扣实验只重新训练了 h-DQN，CSV 有 201 个评估点；设置中的 `qrm_reference_only=true` 表明 QRM 没有在该次运行中重训。当前主入口则会训练两种方法，并保存双方法模型。不能把历史单方法 `_checkpoint.pkl` 当成新入口生成的 `_models.pkl`。

需要逐步路线时，先运行主实验生成模型，再执行：

```powershell
$deliveryPrefix = 'pacman_delivery_hdqn_vs_qrm_seed5_200k_all_goals_navigation_bootstrap_pretrain1000_qrm_train1000_duration_discount'
python -B -m experiments.record_pacman_delivery_routes "experiments/results/${deliveryPrefix}_models.pkl"
```

路线命令只读取最终模型，输出同前缀 `_routes.json`，不训练或更新 Q 表。

### 本地 BFS 特征线性低层（暂不提交）

线性算法、实验入口和对应测试暂留本地，当前仓库不提供该实验的运行入口。

低层为每个动作学习五个权重，四动作共 20 个参数，六目标共享；高层仍使用表格。五个特征为偏置、归一化目标距离、动作前后距离差、撞墙和到达标记，通过完整地图的 BFS 距离与假想后继预计算。奖励仍是二值到达奖励。

默认 seed5、总预算 20 万步（5 万预训练＋15 万联合训练），低层学习率为 0.01，高层为 0.1。默认完整实验尚未运行。已保存的 `pacman_delivery_linear_hdqn_seed5_smoke_5k_bfs_features*` 是总预算 5,000 步、预训练和退火各 1,000 步的流程检查：最终完整任务 10/10 成功，平均 160 步，六目标导航共 360/360 成功。它不是默认 20 万步实验的结果，也不能单独证明函数近似优于表格表示，因为 BFS 特征提供了额外地图信息。

## 解释边界

当前结果来自小型确定性地图。表格 h-DQN 的最新成功结果仅覆盖 seed5，未完成多种子或单因素消融；它是带经验回放的表格型变体，不是神经网络 h-DQN 论文复现。各条件的奖励、地图信息、目标筛选和阶段回合上限不同，不能只根据最终步数或成功率推断一般性方法优势。
