# Day 12

> 后续修订：本页记录的是 Day 12 当时的 18 边 Beef 图。Day 15 已将其改为 `cook`/`cut` 两个单向动作模式、12 条具体模板；当前实现和结果见 `progress/day15.md`。

## 今日目标

实现 Day 11 规格中的三因子通用环境和 `independent` anchor，通过 BFS 枚举实际可达联合状态，并用自动测试验证三个因子、动作、奖励、终止条件和断连状态排除。

## 完成情况

- 创建 `env/factored_tasks.py`，定义 Location、Key 和 Beef 的状态、动作、有向因子图、展示标签、绘图坐标及通用任务配置。
- 三张因子图各包含 9 个节点；Location、Key 和 Beef 分别包含 20、24 和 18 条有向边。
- 创建 `env/factored_minecraft.py`，实现现有 `MDP` 接口。环境只解释 `FactoredTaskConfig`，没有根据任务名称或颜色标签执行专用转移逻辑。
- 创建 `tests/test_factored_minecraft.py`，包含 8 项测试，覆盖三张因子图、729 个可达状态、BFS 稳定顺序、后继闭合性、动作因子不变性、非法动作、Markov state、终止条件和断连因子图。
- 断连测试删除进入 Key 状态 `(2,2)` 的全部有向边。BFS 排除了包含该 Key 状态的 81 个联合组合，得到 $9\times8\times9=648$ 个实际可达状态。

## 三张因子图

以下字符图根据 `env/factored_tasks.py` 中的节点和转移生成，并使用 `MDP/show_factored_mdp.py` 核对。三张图各有 9 个节点；Location、Key 和 Beef 分别有 20、24 和 18 条有向边。

### Location factor

```text
             col=0       col=1       col=2

row=0        (0,0) ──── (0,1)   ×   (0,2)
               │           │           │
row=1        (1,0) ─── B (1,1) ─D─ K (1,2)
               │           │           │
row=2      S (2,0) ──── (2,1)   × G (2,2)
```

图中的连接均为双向，因此 10 组连接对应 20 条有向边。`S` 是起点，`G` 是目标，`B` 是案板，`K` 是灶台，`D` 是候选门边，`×` 表示被墙删除的连接。在 `independent` 中，`D` 与普通双向边相同，不读取 Key 状态。

### Key factor

```text
tail:          blank          black          white

head=blank     (0,0)  ───→    (0,1)    ⇄     (0,2)
                │              │               │
                ↓              ↓               ↓
head=black     (1,0)  ───→    (1,1)    ⇄     (1,2)
                ⇅              ⇅               ⇅
head=white     (2,0)  ───→    (2,1)    ⇄     (2,2)
```

横向第一段的右箭头是 `tail-black`；第二段向右是 `tail-white`，向左是 `tail-black`。纵向第一段的下箭头是 `head-black`；第二段向下是 `head-white`，向上是 `head-black`。此外还有图中未展开的跨级边：每一行都有 `(h,0) --tail-white--> (h,2)`，每一列都有 `(0,t) --head-white--> (2,t)`。

### Beef factor

```text
processing:       whole          sliced          minced

raw               (0,0) --chop--> (0,1) --stir--> (0,2)
                    ⇅              ⇅               ⇅
medium            (1,0) --chop--> (1,1) --stir--> (1,2)
                    ⇅              ⇅               ⇅
cooked            (2,0) --chop--> (2,1) --stir--> (2,2)
```

纵向向下是 `heat`，使 cooking 从 `raw` 依次变为 `medium`、`cooked`；向上是 `cool`。横向的 `chop` 和 `stir` 依次把 processing 从 `whole` 变为 `sliced`、`minced`。在 `independent` 中，这些 Beef 动作不读取 Location 状态。


## 验证结果

运行本地字符展示脚本：

```text
python -B MDP/show_factored_mdp.py
```

脚本报告三张图的节点数均为 9，有向边数分别为 20、24 和 18；同时执行了一条 10 步路径并到达终止状态。

单独运行 Day 11–12 测试：

```text
python -B -m unittest tests.test_factored_minecraft -v
```

结果为新增的 8 项测试全部通过。

运行完整测试：

```text
python -B -m unittest discover -s tests -v
```

结果为 56 项测试全部通过，其中包括第二周已有的 48 项测试和第三周新增的 8 项测试。当前验证结果包括：

- 三张因子图的节点数均为 9，有向边数分别为 20、24 和 18。
- `independent` 从初始状态可达全部 729 个理论联合状态，状态无重复且枚举顺序稳定。
- 每个合法转移的概率为 1，奖励为 `-1.0`，全部后继都属于 `states`。
- 每个动作恰好改变一个对应因子。
- 非法动作不会转化为 self-loop，终止状态没有动作。
- 两条不同动作历史到达同一联合状态后，得到相同的合法动作和转移结果。
- 断连 Key 图只产生 648 个可达联合状态，不会声明包含不可达 Key 节点的状态。

## 遇到的问题

BFS 建立 `states` 时需要调用环境自己的 `actions` 和 `transitions`，但完整的可达状态集合此时尚未建立。实现中把状态检查分为两个阶段：BFS 期间只检查三个因子节点是否合法，BFS 完成后再要求输入状态属于最终可达集合。这样既能复用真实环境接口，也不会把理论笛卡尔积误当成可达状态。

当前只实现 `independent`，因此 `AvailabilityRule` 的通用结构已经存在，但具体钥匙门和功能区规则尚未实例化，测试也没有把门谓词行为标记为已验证。这部分属于 Day 13 的其他 anchors 和耦合分析。

架构问题，不太清楚什么样的层级结构是好的，类嵌套、函数封装往往会为了功能实现而写得相当复杂，也会为了兼容未来可能添加的功能，写很多兼容性检查。目前这方面 AI 辅助也不能做得很好。



## 下一步

- 修正规格中的位置坐标记号和配置字段描述。
- 为 Day 13 实现 `key_gates_location`、`location_gates_beef` 和 `combined` 三个 anchors。
- 明确转移模板及耦合比例的计数口径，再实现结构耦合矩阵和最短路径区间分析。
- 复核 Milestone 1 的提交范围；提交和标签操作需单独确认。
