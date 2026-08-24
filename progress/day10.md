# Day 10

## 今日目标

完成第二周的测试、报告和文档整理，并准备最终演示。在不替换基线地图和 Day 9 PI/VI 实验的前提下，增加一张带障碍的对照地图，用于检验现有 MDP 接口和通用算法能否适应地图布局变化。

## 完成情况

- 新增 `env/minecraft_maps.py`，分别定义 `BASELINE_MAP` 和 `CHALLENGE_MAP`。`MinecraftMDP()` 默认行为不变，只有显式传入 `CHALLENGE_MAP` 时才加载对照地图。
- 调整 `env/minecraft.py`，使起点、资源、factory 和障碍来自地图配置。越界或撞到障碍时 agent 留在原位，障碍位置不进入状态空间。
- 新增 `experiments/run_minecraft_challenge.py`，直接复用已有 PI 和 VI，输出可达状态数、价值差、执行路径、资源顺序、终止情况和折扣回报。
- 新增 `tests/test_minecraft_challenge.py`，检查障碍碰撞、条件终止、两种资源顺序、PI/VI 价值一致性，以及最优路径能否无循环终止。
- 完成 `docs/week2_questions.md`，整理第二周思考题和现场验收问题的书面回答。
- 完成 `docs/week2_report.md`，记录 Minecraft MDP 定义、状态空间、马尔可夫性质、PI/VI 结果、状态信息层次、模型限制和下一阶段方向。
- 更新 README 中的对照地图说明、实验命令和当前测试数量。

## Challenge 地图文本示例

坐标格式为 `(row, col)`，`row` 从上到下增加，`col` 从左到右增加。`CHALLENGE_MAP` 的布局可以表示为：

```text
       col0  col1  col2  col3  col4
row0    S     .     F     .     W
row1    X     .     .     .     .
row2    .     .     .     .     .
row3    .     .     .     .     .
row4    I     .     .     .     .
```

其中，`S` 表示起点 `(0,0)`，`F` 表示 factory `(0,2)`，`W` 表示 wood `(0,4)`，`I` 表示 iron `(4,0)`，`X` 表示障碍 `(1,0)`，`.` 表示普通可通行位置。该文本布局与 `env/minecraft_maps.py` 中的 `CHALLENGE_MAP` 配置一致。

## 验证结果

对照地图测试命令为：

```text
python -B -m unittest tests.test_minecraft_challenge -v
```

5 项对照地图测试全部通过。完整测试命令为：

```text
python -B -m unittest discover -s tests -v
```

完整测试共 48 项，全部通过。对照地图实验的验证结果为：可达状态数 92，PI 与 VI 的最大价值差为 0；PI 经过 13 轮稳定，VI 经过 17 轮收敛；两个策略都按 `iron -> wood` 收集资源，在 16 步后终止，没有出现状态循环；起点价值和实际路径折扣回报均为 `-11.1974666270`。手工构造的 `wood -> iron` 合法路径需要 18 步，说明对照地图打破了基线地图中的资源顺序对称性。


## 遇到的问题

对照地图最初可能要求修改环境中的固定坐标。为避免复制环境或算法，最终只增加简单地图配置，并让原有环境从配置读取布局；默认基线地图保持不变。

曾尝试把 PI/VI 的多轮求解过程画成二维热力图，但五元状态需要按w,i标志分开，同一张图同时包含颜色、价值和动作后不够直观。该展示方案随后放弃。

## 下一步

- 复核 Day 10 提交范围，排除无关的本地文件和重新生成的旧图。
- 完成最终提交和 `week2-submission` 标签；Git 操作需要事先确认。
