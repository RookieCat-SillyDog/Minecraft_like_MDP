# Minecraft-like MDP

本项目将 Minecraft-like Make Bridge 任务建模为有限 MDP，并使用动态规划算法求解。

已实现：

- 统一有限 MDP 接口。
- 确定性 `5×5` GridWorld。
- Policy Evaluation（策略评估）。
- Policy Iteration（策略迭代，PI）。
- Value Iteration（价值迭代，VI）。
- Minecraft-like Make Bridge 环境、状态枚举、实验和自动测试。
- 三因子 Factored MDP、四个 coupling anchors 和 tie-aware 最短路径分析。

第三周的模型定义、实验方法、结果与解释边界见 [三因子 Factored MDP 报告](docs/week3_report.md)。

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

当前预期结果：

```text
Ran 66 tests
OK
```

## 运行实验

| 实验 | 命令 | 关键预期结果 |
| --- | --- | --- |
| GridWorld 随机策略评估 | `python -B -m experiments.run_gridworld` | 164 次迭代后收敛 |
| GridWorld PI | `python -B -m experiments.run_policy_iteration` | 9 轮收敛，最优路径 8 步 |
| GridWorld VI | `python -B -m experiments.run_value_iteration` | 9 轮收敛，与 PI 的最大价值差为 0 |
| Minecraft 状态枚举 | `python -B -m experiments.enumerate_minecraft_states` | 理论状态 200、可达状态 96、转移 380 |
| Minecraft PI/VI | `python -B -m experiments.run_minecraft` | 最大价值差为 0，两条路径均为 16 步 |
| Minecraft 对照地图 | `python -B -m experiments.run_minecraft_challenge` | 92 个可达状态，最大价值差为 0，最优路径为 16 步 |
| 三因子 coupling 分析 | `python -B -m experiments.analyze_factored_tasks` | 四个 anchors 的 $L^*=10$，PI/VI 最大价值差为 0 |
| 三因子结果绘图 | `python -B -m experiments.plot_factored_tasks` | 在 `figures/` 中生成 PNG 和 SVG 两种格式的结果图 |

三因子分析同时报告两种结构计数：$S_{i\to j}$ 是受条件因子影响的 action schema（动作模式）数量，$K_{i\to j}$ 是受影响的 grounded transition template（具体有向转移模板）数量。

| anchor | $(S_{K\to L},S_{L\to B})$ | $(K_{K\to L},K_{L\to B})$ | $L^*$ | $N_{K\to L}$ | $N_{L\to B}$ | $D$ | reachable states | shortest paths |
| --- | --- | --- | ---: | --- | --- | --- | ---: | ---: |
| `independent` | (0, 0) | (0, 0) | 10 | [0, 0] | [0, 0] | [2, 9] | 729 | 75600 |
| `key_gates_location` | (2, 0) | (2, 0) | 10 | [1, 1] | [0, 0] | [2, 9] | 594 | 30240 |
| `location_gates_beef` | (0, 2) | (0, 12) | 10 | [0, 0] | [4, 4] | [5, 8] | 729 | 90 |
| `combined` | (2, 2) | (2, 12) | 10 | [1, 1] | [4, 4] | [5, 8] | 594 | 56 |


第三周正式报告使用以下三组图，每组同时提供 PNG 和 SVG：

- `week3_three_factor_graph.*`：三张因子图和 active coupling rules。
- `week3_joint_value_slices.*`：固定三个 Beef states 的联合最优价值切片。
- `week3_anchor_comparison.*`：四个 anchors 的结构耦合与最短路径指标。

另外两组 distance-delta 图比较相同联合状态到目标的最短距离：`week3_key_gate_distance_delta.*` 展示加入 $K\to L$ 规则后的变化，`week3_location_beef_distance_delta.*` 展示加入 $L\to B$ 规则后的变化。



实验图保存在 `figures/`，同时生成 PNG 和 SVG 文件。




## 项目结构

```text
minecraft-mdp/
├── algorithms/    # Policy Evaluation、PI 和 VI
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
- 当前命令已在上述开发环境中验证。
