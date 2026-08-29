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
Ran 64 tests
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

三因子分析的关键预期结果：

| anchor | $K_{K\to L}$ | $K_{L\to B}$ | $L^*$ | $N_{K\to L}$ | $N_{L\to B}$ | $D$ | reachable states | shortest paths |
| --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: |
| `independent` | 0 | 0 | 10 | [0, 0] | [0, 0] | [2, 9] | 729 | 75600 |
| `key_gates_location` | 2 | 0 | 10 | [1, 1] | [0, 0] | [2, 9] | 594 | 30240 |
| `location_gates_beef` | 0 | 2 | 10 | [0, 0] | [1, 1] | [3, 9] | 729 | 10800 |
| `combined` | 2 | 2 | 10 | [1, 1] | [1, 1] | [3, 9] | 594 | 4068 |

三张因子图分别包含 20、24 和 18 个有向转移模板。两个活跃方向的 reachable-context 明细为：$M_{K\to L}=2$、总实例数 144，$M_{L\to B}=2$、总实例数 146；对应的模板比例为 $2/20$ 和 $2/18$，实例比例为 $2/144$ 和 $2/146$。

Minecraft PI/VI 实验的当前结果：

- PI 16 轮、VI 17 轮。
- 起点价值均为 `-11.1974666270`。
- 两个策略有 23 个动作不同的状态，均由并列最优动作造成。
- 两条路径都按 `iron -> wood` 收集资源，并在 16 步后终止。

实验图保存在 `figures/`，同时生成 PNG 和 SVG 文件。

## 对照地图展示

对照地图是对基线实验的补充展示，不替代 Day 6–9 的结果。它在 `(1, 0)` 放置一个障碍，并把 factory 移至 `(0, 2)`。`MinecraftMDP()` 仍加载原有无障碍基线；使用 `MinecraftMDP(CHALLENGE_MAP)` 才会加载对照地图。对照实验会验证障碍碰撞、条件终止、PI/VI 价值一致性，并生成 PI、VI 四层价值与策略图和最优路径图；图中的障碍格显示为 `X`，与资源规则导致的“不可达”格区分。



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
