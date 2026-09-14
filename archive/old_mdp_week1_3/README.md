# Minecraft-like MDP

本项目将 Minecraft-like Make Bridge 任务建模为有限 MDP，并使用动态规划算法求解。

已实现：

- 统一有限 MDP 接口。
- 确定性 `5×5` GridWorld。
- Policy Evaluation（策略评估）。
- Policy Iteration（策略迭代，PI）。
- Value Iteration（价值迭代，VI）。
- Minecraft-like Make Bridge 环境、状态枚举、实验和自动测试。
- 81-state 三因子 Factored GridWorld、两张 cost-matched 地图和未折扣最短路径分析。

当前 Factored GridWorld 的地图、规则和指标实现分别位于
[`env/factored_minecraft/`](env/factored_minecraft/)、
[`analysis/analyze_factored_tasks.py`](analysis/analyze_factored_tasks.py) 和
[`analysis/shortest_paths.py`](analysis/shortest_paths.py)。

Minecraft 状态为 `(row, col, wood, iron, bridge)`。每步奖励为 `-1`，折扣因子为 `0.95`。完整定义见 [Minecraft MDP 规格](docs/minecraft_mdp_spec.md)。

## 环境安装

已验证环境：

- Windows PowerShell
- Python 3.11.7
- NumPy 1.26.4
- Matplotlib 3.8.0

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

macOS 或 Linux：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

以下命令均在项目根目录运行。`-B` 表示不生成 `.pyc` 缓存，`-m` 表示按模块运行。

## 运行测试

```powershell
python -B -m unittest discover -s tests -v
```

Factored GridWorld 已更换为 Map A/B 设计，相关旧测试仍在迁移，不应作为当前指标的验收结果。

## 运行实验

| 实验 | 命令 | 关键预期结果 |
| --- | --- | --- |
| GridWorld 随机策略评估 | `python -B -m experiments.run_gridworld` | 164 次迭代后收敛 |
| GridWorld PI | `python -B -m experiments.run_policy_iteration` | 9 轮收敛，最优路径 8 步 |
| GridWorld VI | `python -B -m experiments.run_value_iteration` | 9 轮收敛，与 PI 的最大价值差为 0 |
| Minecraft 状态枚举 | `python -B -m experiments.enumerate_minecraft_states` | 理论状态 200、可达状态 96、转移 380 |
| Minecraft PI/VI | `python -B -m experiments.run_minecraft` | 最大价值差为 0，两条路径均为 16 步 |
| Minecraft 对照地图 | `python -B -m experiments.run_minecraft_challenge` | 92 个可达状态，最大价值差为 0，最优路径为 16 步 |
| Factored GridWorld 分析 | `python -m analysis.analyze_factored_tasks` | 两张地图均有 81 个可达状态且 $C_D=C_B=7$ |
| 三因子结果绘图 | `python -m analysis.plot_factored_tasks` | 在 `figures/` 中生成 PNG 和 SVG 两种格式的结果图 |

## 当前 Factored GridWorld

联合状态为：

$$
s=(l,k,b)\in L\times K\times B,
\qquad |\mathcal S|=9\times3\times3=81.
$$

- Location：3×3 网格，坐标格式为 `(row, col)`。
- Key：`blank → shallow blue → blue`，使用 `dye` 转移。
- Beef：`raw → medium → well`，只有在 Kitchen 才能使用 `cook`。
- Door 只有在 Key=`blue` 时开放，因此依赖关系为 $K\to L\to B$。
- 两张地图共享 wall edge $\{(1,1),(1,2)\}$、Start $(0,0)$、Kitchen $(0,1)$ 和 Goal $(2,1)$。
- Map A 的 Door 位于 $\{(0,0),(0,1)\}$；Map B 位于 $\{(1,1),(2,1)\}$。

分析保留三个量：

$$
\Delta C=C_D-C_B
$$

控制必须经过 Door 与禁止经过 Door 的路线成本差；

$$
D_{K\to L}
=
\frac1{|\Omega|}
\sum_{(l,b)\in\Omega}
\mathbf1[\Pi_L^*(l,\mathrm{blank},b)\ne\Pi_L^*(l,\mathrm{blue},b)]
$$

衡量 Key 改变后最优 Location 动作集合发生变化的上下文比例；

$$
\Gamma_D(l,b)
=
V^*_{M^{-D}}(l,\mathrm{blue},b)-V^*_M(l,\mathrm{blue},b)
$$

表示永久删除 Door 后增加的最优步数。

当前结果：

| Map | $C_D$ | $C_B$ | $\Delta C$ | $D_{K\to L}$ | $\bar\Gamma_D$ | reachable states |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A | 7 | 7 | 0 | $5/26$ | $4/26$ | 81 |
| B | 7 | 7 | 0 | $7/26$ | $44/26$ | 81 |


结果图保存在 `figures/`，每张图同时提供 450 DPI PNG 和 SVG：

- [`factored_gridworld_maps.*`](figures/factored_gridworld_maps.png)：地图、Door、Wall 和依赖关系。
- [`factored_gridworld_policy_changes.*`](figures/factored_gridworld_policy_changes.png)：$D_{K\to L}$ 的状态分布。
- [`factored_gridworld_door_leverage.*`](figures/factored_gridworld_door_leverage.png)：$\Gamma_D$ 热图。




## 项目结构

```text
minecraft-mdp/
├── algorithms/    # Policy Evaluation、PI 和 VI
├── analysis/      # Factored GridWorld 的最短路径、指标和绘图
├── docs/          # MDP 定义和报告
├── env/           # MDP 接口、GridWorld 和 Minecraft
├── experiments/   # 实验入口
├── figures/       # 实验结果图
├── progress/      # 每日进展记录
├── tests/         # 自动测试
├── README.md
└── requirements.txt
```

## 复现说明

- 当前环境和算法均为确定性的，相同版本应得到相同结果。
- PI、VI 仅通过统一 MDP 接口访问环境，没有 Minecraft 专用算法。
- Factored GridWorld 的指标使用单位步成本下的未折扣 BFS distance，不与 PI/VI 的折扣价值混用。
