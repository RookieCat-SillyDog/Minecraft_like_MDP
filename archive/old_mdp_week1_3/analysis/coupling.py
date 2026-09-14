"""三因子任务的结构耦合分析。"""

from env.factored_minecraft.maps import beef, key, location


coupling_directions = {
    "l_to_k": (location, key),
    "l_to_b": (location, beef),
    "k_to_l": (key, location),
    "k_to_b": (key, beef),
    "b_to_l": (beef, location),
    "b_to_k": (beef, key),
}


def edge_outcome(
    env,
    edge,
    conditioning_factor,
    target_factor,
    conditioning_state,
    other_state,
):
    """从环境转移律取得边在指定 context 下的结果。"""
    source, action, _ = edge
    other_factor = 3 - target_factor - conditioning_factor
    state = [None, None, None]
    state[target_factor] = source
    state[conditioning_factor] = conditioning_state
    state[other_factor] = other_state
    state = tuple(state)

    if action not in env.actions(state):
        return None
    return env.transitions(state, action)[0][1][target_factor]


def reachable_contexts(env, conditioning_factor, target_factor, edge):
    """按第三因子分组，收集模板源状态的可达条件 context。"""
    source = edge[0]
    other_factor = 3 - conditioning_factor - target_factor
    groups = {}

    for state in env.states:
        if env.is_terminal(state) or state[target_factor] != source:
            continue
        groups.setdefault(state[other_factor], set()).add(
            state[conditioning_factor]
        )

    return groups


def actual_templates(env):
    """从全部可达转移收集三个因子的实际有向模板。"""
    templates = {factor: [] for factor in range(3)}
    seen = {factor: set() for factor in range(3)}

    for state in env.states:
        if env.is_terminal(state):
            continue
        for action in env.actions(state):
            factor = env.action_factor[action]
            next_state = env.transitions(state, action)[0][1]
            edge = (state[factor], action, next_state[factor])
            if edge not in seen[factor]:
                seen[factor].add(edge)
                templates[factor].append(edge)

    return {factor: tuple(edges) for factor, edges in templates.items()}


def structural_coupling(env):
    """计算六个方向的规则模式和具体模板耦合。"""
    templates_by_factor = actual_templates(env)
    template_matrix = {
        source: {target: 0 for target in range(3)}
        for source in range(3)
    }
    schema_matrix = {
        source: {target: 0 for target in range(3)}
        for source in range(3)
    }
    metrics = {}
    coupled_templates = {}

    for conditioning, target in coupling_directions.values():
        coupled_edges = set()
        coupled_instances = 0
        total_instances = 0

        for edge in templates_by_factor[target]:
            legal_contexts = set()
            is_coupled = False
            contexts = reachable_contexts(env, conditioning, target, edge)

            for other_state, conditioning_states in contexts.items():
                outcomes = set()
                for conditioning_state in conditioning_states:
                    outcome = edge_outcome(
                        env,
                        edge,
                        conditioning,
                        target,
                        conditioning_state,
                        other_state,
                    )
                    outcomes.add(outcome)
                    if outcome == edge[2]:
                        legal_contexts.add(conditioning_state)
                if len(outcomes) > 1:
                    is_coupled = True

            total_instances += len(legal_contexts)
            if is_coupled:
                coupled_edges.add(edge)
                coupled_instances += len(legal_contexts)

        direction = (conditioning, target)
        target_templates = templates_by_factor[target]
        coupled_schemas = {edge[1] for edge in coupled_edges}
        total_schemas = len({edge[1] for edge in target_templates})

        coupled_templates[direction] = coupled_edges
        template_matrix[conditioning][target] = len(coupled_edges)
        schema_matrix[conditioning][target] = len(coupled_schemas)
        metrics[direction] = {
            "coupled_schemas": len(coupled_schemas),
            "total_schemas": total_schemas,
            "schema_proportion": len(coupled_schemas) / total_schemas,
            "coupled_templates": len(coupled_edges),
            "total_templates": len(target_templates),
            "coupled_instances": coupled_instances,
            "total_instances": total_instances,
            "template_proportion": len(coupled_edges) / len(target_templates),
            "instance_proportion": (
                coupled_instances / total_instances if total_instances else 0.0
            ),
            "analysis_scope": "reachable_contexts",
        }

    return {
        "template_matrix": template_matrix,
        "schema_matrix": schema_matrix,
        "metrics": metrics,
        "templates": coupled_templates,
        "template_counts": {
            name: template_matrix[source][target]
            for name, (source, target) in coupling_directions.items()
        },
        "schema_counts": {
            name: schema_matrix[source][target]
            for name, (source, target) in coupling_directions.items()
        },
    }
