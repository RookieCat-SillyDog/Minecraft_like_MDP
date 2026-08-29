# Day 13

## 今日目标

实现四个 task anchors 和完整 structural coupling matrix（结构耦合矩阵），统一 transition template（转移模板）的计数口径，并验证门和功能区规则。

## 完成情况

- 将 template 严格定义为有向三元组 $(s_j,a_j,s'_j)$；`DirectedTransition` 本身就是模板，不再保存可任意填写的类别标签。
- `template_id` 只从三元组派生稳定展示字符串，不参与模板相等性和计数。
- Location、Key 和 Beef 分别包含 20、24 和 18 个模板。
- 实现 `key_gates_location`、`location_gates_beef` 和 `combined`，与现有 `independent` 共用三张基础图、初始状态、目标、成本和动作顺序。
- 钥匙门控制两个有向 Location 模板，只在 $k=(2,2)$ 时开放。
- Beef gate 只控制两条精确模板：`((0,0), heat, (1,0))` 只在 kitchen 开放，`((0,0), chop, (0,1))` 只在 cutting board 开放；其余 Beef 模板不受 Location 控制。
- 实现完整 $3\times3$ 结构耦合矩阵，并从环境实际动作与转移规律计算六个非对角方向的 $z$、$K$、$M$、模板比例和实例比例。
- 验证四个 anchors 的 $(K_{K\to L},K_{L\to B})$ 分别为 $(0,0)$、$(2,0)$、$(0,2)$ 和 $(2,2)$，其他四个非对角项均为 0。

## 实现说明

结构耦合按唯一有向三元组计数，不按动作名称、规则对象数、条件状态数或路径执行次数计数。双向门是方向相反的两个 Location 模板；Beef 的 18 条有向边也是 18 个不同模板。为使 $K_{L\to B}=2$，配置只控制上述 kitchen heat 和 board chop 两条模板，而不是控制整个 `heat` 或 `chop` 动作类别。

分析使用 reachable-context scope。比较两个 context 时固定目标因子的模板源状态和无关的第三个因子，只改变条件因子；模板在不同条件状态下的可执行性或结果发生变化时，才令 $z_{i\to j}(e_j)=1$。

为避免 PI 反复验证动作时重复扫描因子边，`FactorGraph` 建立只读查找表，环境缓存每个可达状态的合法动作。该修改不改变 MDP 接口、动作顺序或转移结果。



## 验证

```text
python -B -m unittest tests.test_factored_minecraft -v
```

结果为 8 项环境测试全部通过。模板数为 20/24/18，四个 anchor 的结构耦合和实例指标由 Day 14 分析测试共同验证。

## 遇到的问题

初版把 `cooking` 和 `cutting` 动作类别标签当成模板，错误地将 18 条 Beef 有向边合并成两个模板，使 $K_{L\to B}=2$ 只是标签合并产生的结果。提交前复审后删除独立标签字段，将三元组本身作为模板，并重新选择两条精确受控 Beef 模板。最终 $K_{L\to B}=2$ 表示两条真实的有向模板。
