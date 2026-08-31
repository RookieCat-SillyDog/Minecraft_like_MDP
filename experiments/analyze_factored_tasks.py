"""分析四个三因子 task anchors 的耦合与最短路径。"""

from collections import deque
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from algorithms.policy_iteration import PolicyIteration
from algorithms.value_iteration import ValueIteration, find_best_actions
from env.factored_minecraft import FactoredMinecraftMDP
from env.factored_tasks import (
    BEEF_FACTOR,
    DirectedTransition,
    FACTOR_ORDER,
    KEY_FACTOR,
    LOCATION_FACTOR,
    TASK_CONFIGS,
)


SOLVER_TOLERANCE = 1e-10
VALUE_TOLERANCE = 1e-8
TIE_TOLERANCE = 1e-8

COUPLING_KEYS = (
    "l_to_k",
    "l_to_b",
    "k_to_l",
    "k_to_b",
    "b_to_l",
    "b_to_k",
)
PATH_COUPLING_KEYS = ("k_to_l", "l_to_b")
PATH_METRICS = PATH_COUPLING_KEYS + ("switches",)
FACTOR_INDEX = {factor: index for index, factor in enumerate(FACTOR_ORDER)}


def edge_outcome(
    env,
    edge,
    conditioning_factor,
    target_factor,
    conditioning_state,
    other_state,
):
    """从环境转移律取得边在指定 context 下的结果。"""
    target_index = FACTOR_INDEX[target_factor]
    conditioning_index = FACTOR_INDEX[conditioning_factor]
    other_index = 3 - target_index - conditioning_index
    factor_states = [None, None, None]
    factor_states[target_index] = edge.source
    factor_states[conditioning_index] = conditioning_state
    factor_states[other_index] = other_state

    state = tuple(factor_states)
    if edge.action not in env.actions(state):
        return None
    return env.transitions(state, edge.action)[0][1][target_index]


def reachable_context_groups(env, conditioning_factor, target_factor, edge):
    """按第三因子分组，收集模板源状态的可达条件 context。"""
    conditioning_index = FACTOR_INDEX[conditioning_factor]
    target_index = FACTOR_INDEX[target_factor]
    other_index = 3 - conditioning_index - target_index
    groups = {}

    for state in env.states:
        if env.is_terminal(state) or state[target_index] != edge.source:
            continue
        other_state = state[other_index]
        groups.setdefault(other_state, set()).add(state[conditioning_index])

    return groups


def deterministic_successor(env, state, action):
    """取得确定性动作的唯一后继。"""
    transitions = env.transitions(state, action)
    if len(transitions) != 1 or transitions[0][0] != 1.0:
        raise ValueError("factored task 分析要求确定性转移")
    return transitions[0][1]


def actual_templates_by_factor(env):
    """从全部可达转移收集三个因子的实际有向模板。"""
    templates = {factor: [] for factor in FACTOR_ORDER}
    seen = {factor: set() for factor in FACTOR_ORDER}

    for state in env.states:
        if env.is_terminal(state):
            continue

        for action in env.actions(state):
            factor = env.config.factor_for_action(action)
            factor_index = FACTOR_INDEX[factor]
            next_state = deterministic_successor(env, state, action)
            edge = DirectedTransition(
                source=state[factor_index],
                action=action,
                target=next_state[factor_index],
            )

            if edge not in seen[factor]:
                seen[factor].add(edge)
                templates[factor].append(edge)

    return {
        factor: tuple(edges)
        for factor, edges in templates.items()
    }


def structural_coupling(env):
    """计算六个方向的规则模式和具体模板耦合。"""
    actual_templates = actual_templates_by_factor(env)
    template_matrix = {}
    schema_matrix = {}
    direction_metrics = {}
    coupled_templates = {}

    for conditioning in FACTOR_ORDER:
        template_matrix[conditioning] = {}
        schema_matrix[conditioning] = {}

        for target in FACTOR_ORDER:
            if conditioning == target:
                template_matrix[conditioning][target] = 0
                schema_matrix[conditioning][target] = 0
                continue

            direction = (conditioning, target)
            coupled_edges = set()
            coupled_instances = 0
            total_instances = 0

            for edge in actual_templates[target]:
                context_groups = reachable_context_groups(
                    env,
                    conditioning,
                    target,
                    edge,
                )
                legal_contexts = set()
                is_coupled = False

                for other_state, condition_states in context_groups.items():
                    outcomes = set()
                    for condition_state in condition_states:
                        outcome = edge_outcome(
                            env,
                            edge,
                            conditioning,
                            target,
                            condition_state,
                            other_state,
                        )
                        outcomes.add(outcome)
                        if outcome == edge.target:
                            legal_contexts.add(condition_state)
                    if len(outcomes) > 1:
                        is_coupled = True

                total_instances += len(legal_contexts)
                if is_coupled:
                    coupled_edges.add(edge)
                    coupled_instances += len(legal_contexts)

            total_templates = len(actual_templates[target])
            # 一个动作是一个可跨源状态复用的规则模式；每个不同的
            # source-action-target 仍然保留为具体模板。
            coupled_schemas = {edge.action for edge in coupled_edges}
            total_schemas = len(
                {edge.action for edge in actual_templates[target]}
            )
            coupled_templates[direction] = coupled_edges
            template_matrix[conditioning][target] = len(coupled_edges)
            schema_matrix[conditioning][target] = len(coupled_schemas)
            direction_metrics[direction] = {
                "coupled_schemas": len(coupled_schemas),
                "total_schemas": total_schemas,
                "schema_proportion": len(coupled_schemas) / total_schemas,
                "coupled_templates": len(coupled_edges),
                "total_templates": total_templates,
                "coupled_instances": coupled_instances,
                "total_instances": total_instances,
                "template_proportion": len(coupled_edges) / total_templates,
                "instance_proportion": (
                    coupled_instances / total_instances
                    if total_instances
                    else 0.0
                ),
                "analysis_scope": "reachable_contexts",
            }

    template_counts = {}
    schema_counts = {}
    for key in COUPLING_KEYS:
        source, target = key.split("_to_")
        source = source.upper()
        target = target.upper()
        template_counts[key] = template_matrix[source][target]
        schema_counts[key] = schema_matrix[source][target]

    return {
        "template_matrix": template_matrix,
        "schema_matrix": schema_matrix,
        "metrics": direction_metrics,
        "templates": coupled_templates,
        "template_counts": template_counts,
        "schema_counts": schema_counts,
    }


def shortest_path_dag(env, initial_state):
    """用 BFS 建立从初始状态到最近终止状态的最短路径 DAG。"""
    distances = {initial_state: 0}
    edges = {initial_state: []}
    queue = deque([initial_state])
    optimal_length = None
    terminal_states = []

    while queue:
        state = queue.popleft()
        distance = distances[state]

        if optimal_length is not None and distance >= optimal_length:
            continue

        for action in env.actions(state):
            next_state = deterministic_successor(env, state, action)
            next_distance = distance + 1

            if next_state not in distances:
                distances[next_state] = next_distance
                edges[next_state] = []
                queue.append(next_state)

            if distances[next_state] != next_distance:
                continue

            edges[state].append((action, next_state))

            if env.is_terminal(next_state):
                if optimal_length is None:
                    optimal_length = next_distance
                if next_distance == optimal_length:
                    terminal_states.append(next_state)

    if optimal_length is None:
        raise RuntimeError("初始状态不能到达任何终止状态")

    unique_terminal_states = []
    for state in terminal_states:
        if state not in unique_terminal_states:
            unique_terminal_states.append(state)

    return {
        "initial_state": initial_state,
        "distances": distances,
        "edges": edges,
        "optimal_length": optimal_length,
        "terminal_states": tuple(unique_terminal_states),
    }


def component_edge(env, state, action):
    """根据环境的实际后继取得联合动作对应的因子模板。"""
    factor = env.config.factor_for_action(action)
    factor_index = FACTOR_ORDER.index(factor)
    next_state = deterministic_successor(env, state, action)
    return DirectedTransition(
        source=state[factor_index],
        action=action,
        target=next_state[factor_index],
    )


def path_coupling_increments(env, state, action, coupled_templates):
    """返回一次实际动作对两个路径耦合指标的增量。"""
    increments = {"k_to_l": 0, "l_to_b": 0}
    edge = component_edge(env, state, action)

    for key in PATH_COUPLING_KEYS:
        conditioning, target = key.split("_to_")
        direction = (conditioning.upper(), target.upper())
        if edge in coupled_templates[direction]:
            increments[key] = 1

    return increments


def initial_path_record():
    """创建一条零长度路径的动态规划记录。"""
    return {
        "path_count": 1,
        "minimums": {metric: 0 for metric in PATH_METRICS},
        "maximums": {metric: 0 for metric in PATH_METRICS},
    }


def extended_path_record(source_record, increments):
    """把一组路径统一扩展一个动作。"""
    new_record = {
        "path_count": source_record["path_count"],
        "minimums": {},
        "maximums": {},
    }

    for metric in PATH_METRICS:
        increment = increments[metric]
        new_record["minimums"][metric] = (
            source_record["minimums"][metric] + increment
        )
        new_record["maximums"][metric] = (
            source_record["maximums"][metric] + increment
        )

    return new_record


def merge_path_records(target_record, new_record):
    """合并到达同一状态且上一动作因子相同的路径。"""
    target_record["path_count"] += new_record["path_count"]

    for metric in PATH_METRICS:
        target_record["minimums"][metric] = min(
            target_record["minimums"][metric],
            new_record["minimums"][metric],
        )
        target_record["maximums"][metric] = max(
            target_record["maximums"][metric],
            new_record["maximums"][metric],
        )


def shortest_path_ranges(env, dag, coupled_templates):
    """在 shortest-path DAG 上计算耦合、切换范围和路径数。"""
    config = env.config
    records_by_state = {
        dag["initial_state"]: {None: initial_path_record()}
    }
    ordered_states = sorted(
        dag["distances"],
        key=dag["distances"].get,
    )

    for state in ordered_states:
        distance = dag["distances"][state]
        if distance >= dag["optimal_length"]:
            continue

        # 切换次数取决于上一动作属于哪个因子，所以同一联合状态下
        # 需要分别保存三种上一动作因子的路径记录。
        state_records = records_by_state.get(state, {})
        for previous_factor, record in state_records.items():
            for action, next_state in dag["edges"].get(state, ()):
                action_factor = config.factor_for_action(action)
                increments = path_coupling_increments(
                    env,
                    state,
                    action,
                    coupled_templates,
                )
                switch_increment = int(
                    previous_factor is not None
                    and previous_factor != action_factor
                )
                increments["switches"] = switch_increment
                new_record = extended_path_record(record, increments)

                next_state_records = records_by_state.setdefault(
                    next_state,
                    {},
                )
                if action_factor not in next_state_records:
                    next_state_records[action_factor] = new_record
                else:
                    merge_path_records(
                        next_state_records[action_factor],
                        new_record,
                    )

    terminal_records = []
    for terminal_state in dag["terminal_states"]:
        records = records_by_state.get(terminal_state, {})
        terminal_records.extend(records.values())

    if not terminal_records:
        raise RuntimeError("shortest-path DAG 没有终止路径记录")

    path_count = sum(record["path_count"] for record in terminal_records)
    ranges = {}
    for metric in PATH_METRICS:
        ranges[metric] = [
            min(record["minimums"][metric] for record in terminal_records),
            max(record["maximums"][metric] for record in terminal_records),
        ]

    return {"path_count": path_count, "ranges": ranges}


def action_statistics(env):
    """统计全部非终止可达状态上的动作可用性。"""
    nonterminal_states = [
        state for state in env.states if not env.is_terminal(state)
    ]
    factor_totals = {factor: 0 for factor in FACTOR_ORDER}
    branching_counts = []

    for state in nonterminal_states:
        actions = env.actions(state)
        branching_counts.append(len(actions))
        for action in actions:
            factor = env.config.factor_for_action(action)
            factor_totals[factor] += 1

    state_count = len(nonterminal_states)
    factor_averages = {
        factor: factor_totals[factor] / state_count
        for factor in FACTOR_ORDER
    }
    return {
        "nonterminal_states": state_count,
        "total_available_actions": sum(branching_counts),
        "available_actions_by_factor": factor_totals,
        "average_actions_by_factor": factor_averages,
        "average_branching_factor": sum(branching_counts) / state_count,
        "minimum_branching_factor": min(branching_counts),
        "maximum_branching_factor": max(branching_counts),
    }


def selected_action(policy, state):
    """读取确定性策略选择的动作。"""
    return next(iter(policy[state]))


def solve_and_compare(env):
    """运行 PI 和 VI，并检查全部价值与不同策略动作。"""
    pi_solver = PolicyIteration(
        env,
        evaluation_tolerance=SOLVER_TOLERANCE,
    )
    vi_solver = ValueIteration(
        env,
        tolerance=SOLVER_TOLERANCE,
    )
    pi_policy, pi_values = pi_solver.solve()
    vi_policy, vi_values = vi_solver.solve()

    value_differences = {
        state: abs(pi_values[state] - vi_values[state])
        for state in env.states
    }
    max_difference_state = max(value_differences, key=value_differences.get)
    max_difference = value_differences[max_difference_state]

    policy_difference_count = 0
    unexplained_differences = []
    for state in env.states:
        if env.is_terminal(state):
            continue

        pi_action = selected_action(pi_policy, state)
        vi_action = selected_action(vi_policy, state)
        if pi_action == vi_action:
            continue

        policy_difference_count += 1
        best_actions, _ = find_best_actions(
            env,
            vi_values,
            state,
            tie_tolerance=TIE_TOLERANCE,
        )
        if pi_action not in best_actions or vi_action not in best_actions:
            unexplained_differences.append({
                "state": state,
                "pi_action": pi_action,
                "vi_action": vi_action,
                "best_actions": best_actions,
            })

    if max_difference > VALUE_TOLERANCE:
        raise RuntimeError("PI 与 VI 在全部可达状态上的价值不一致")
    if unexplained_differences:
        raise RuntimeError("部分策略差异不能由并列最优动作解释")

    return {
        "pi_iterations": pi_solver.iterations,
        "vi_iterations": vi_solver.iterations,
        "pi_vi_max_diff": max_difference,
        "max_difference_state": max_difference_state,
        "policy_difference_count": policy_difference_count,
        "unexplained_policy_differences": unexplained_differences,
    }


def analyze_task(config):
    """生成一个 anchor 的全部 Day 13–14 指标。"""
    env = FactoredMinecraftMDP(config)
    coupling = structural_coupling(env)
    query_initial_state = config.query_set[0]
    dag = shortest_path_dag(env, query_initial_state)
    path_analysis = shortest_path_ranges(env, dag, coupling["templates"])
    coupling_detail = {}
    for key in COUPLING_KEYS:
        source, target = key.split("_to_")
        coupling_detail[key] = coupling["metrics"][
            (source.upper(), target.upper())
        ]

    return {
        "anchor": config.task_name,
        "query_initial_state": query_initial_state,
        "schema_coupling": coupling["schema_counts"],
        "schema_coupling_matrix": coupling["schema_matrix"],
        "template_coupling": coupling["template_counts"],
        "template_coupling_matrix": coupling["template_matrix"],
        "coupling_detail": coupling_detail,
        "optimal_length": dag["optimal_length"],
        "path_coupling_range": {
            "k_to_l": path_analysis["ranges"]["k_to_l"],
            "l_to_b": path_analysis["ranges"]["l_to_b"],
        },
        "switch_range": path_analysis["ranges"]["switches"],
        "shortest_path_count": path_analysis["path_count"],
        "reachable_states": len(env.states),
        "action_statistics": action_statistics(env),
        "solver_comparison": solve_and_compare(env),
    }


def print_results(results):
    """打印任务书规定的四个 anchor 对比表。"""
    print(
        "| anchor | S_K->L | S_L->B | K_K->L | K_L->B | L* | "
        "N_K->L range | N_L->B range | D range | reachable states | "
        "shortest paths | PI/VI max diff |"
    )
    print(
        "| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | "
        "---: | ---: | ---: |"
    )

    for result in results:
        schema_counts = result["schema_coupling"]
        template_counts = result["template_coupling"]
        path_ranges = result["path_coupling_range"]
        solver = result["solver_comparison"]
        print(
            f"| {result['anchor']} "
            f"| {schema_counts['k_to_l']} "
            f"| {schema_counts['l_to_b']} "
            f"| {template_counts['k_to_l']} "
            f"| {template_counts['l_to_b']} "
            f"| {result['optimal_length']} "
            f"| {path_ranges['k_to_l']} "
            f"| {path_ranges['l_to_b']} "
            f"| {result['switch_range']} "
            f"| {result['reachable_states']} "
            f"| {result['shortest_path_count']} "
            f"| {solver['pi_vi_max_diff']:.12g} |"
        )

    print("\nStructural coupling detail (reachable contexts):")
    print(
        "| anchor | direction | schemas | total schemas | schema proportion | "
        "templates | total templates | M | total instances | "
        "template proportion | instance proportion |"
    )
    print(
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | "
        "---: | ---: | ---: |"
    )
    for result in results:
        for direction in COUPLING_KEYS:
            detail = result["coupling_detail"][direction]
            print(
                f"| {result['anchor']} "
                f"| {direction} "
                f"| {detail['coupled_schemas']} "
                f"| {detail['total_schemas']} "
                f"| {detail['schema_proportion']:.6f} "
                f"| {detail['coupled_templates']} "
                f"| {detail['total_templates']} "
                f"| {detail['coupled_instances']} "
                f"| {detail['total_instances']} "
                f"| {detail['template_proportion']:.6f} "
                f"| {detail['instance_proportion']:.6f} |"
            )

    print("\nAction availability and branching:")
    for result in results:
        statistics = result["action_statistics"]
        averages = statistics["average_actions_by_factor"]
        print(
            f"{result['anchor']}: total={statistics['total_available_actions']}, "
            f"mean(L/K/B)="
            f"{averages[LOCATION_FACTOR]:.3f}/"
            f"{averages[KEY_FACTOR]:.3f}/"
            f"{averages[BEEF_FACTOR]:.3f}, "
            f"branching={statistics['average_branching_factor']:.3f} "
            f"[{statistics['minimum_branching_factor']}, "
            f"{statistics['maximum_branching_factor']}], "
            f"policy differences="
            f"{result['solver_comparison']['policy_difference_count']}"
        )


def main():
    """依照固定 anchor 顺序运行并打印分析。"""
    results = [
        analyze_task(config)
        for config in TASK_CONFIGS.values()
    ]
    print_results(results)


if __name__ == "__main__":
    main()
