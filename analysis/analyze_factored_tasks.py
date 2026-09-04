"""比较 Map A 与 Map B 的最小指标集。"""

from analysis.shortest_paths import (
    distances_to_terminal,
    optimal_actions,
    route_costs,
)
from env.factored_minecraft.environment import FactoredMinecraftMDP
from env.factored_minecraft.maps import beef, location, map_a, map_b
from env.factored_minecraft.tasks import combined_rules


def door_is_removed(map_config, _state, edge):
    """在反事实环境 M^{-D} 中永久阻止 Door edge。"""
    return frozenset((edge[0], edge[2])) != map_config.door_edge


def analyze_map(name, map_config):
    env = FactoredMinecraftMDP(map_config, combined_rules)
    distances = distances_to_terminal(env)

    removed_env = FactoredMinecraftMDP(
        map_config,
        combined_rules + (door_is_removed,),
    )
    removed_distances = distances_to_terminal(removed_env)

    contexts = [
        (location_state, beef_state)
        for location_state in map_config.factor_states[location]
        for beef_state in map_config.factor_states[beef]
        if not env.is_terminal((location_state, "blank", beef_state))
    ]
    location_actions = {
        action
        for action, factor in map_config.action_spec
        if factor == location
    }

    location_policy_changes = {}
    door_leverage = {}

    for location_state, beef_state in contexts:
        blank_state = (location_state, "blank", beef_state)
        blue_state = (location_state, "blue", beef_state)

        location_policy_changes[(location_state, beef_state)] = (
            optimal_actions(env, distances, blank_state) & location_actions
            != optimal_actions(env, distances, blue_state) & location_actions
        )
        door_leverage[(location_state, beef_state)] = (
            removed_distances[blue_state] - distances[blue_state]
        )

    door_cost, bypass_cost = route_costs(env)
    context_count = len(contexts)

    return {
        "name": name,
        "door_cost": door_cost,
        "bypass_cost": bypass_cost,
        "delta_cost": door_cost - bypass_cost,
        "location_policy_changes": location_policy_changes,
        "d_kl_count": sum(location_policy_changes.values()),
        "door_leverage": door_leverage,
        "door_leverage_total": sum(door_leverage.values()),
        "context_count": context_count,
        "reachable_states": len(env.states),
    }


def print_results(results):
    print(
        "| map | C_D | C_B | delta_C | D_K->L | mean_Gamma_D | reachable |"
    )
    print("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")

    for result in results:
        context_count = result["context_count"]
        d_kl = result["d_kl_count"] / context_count
        mean_leverage = result["door_leverage_total"] / context_count

        print(
            f"| {result['name']} "
            f"| {result['door_cost']} "
            f"| {result['bypass_cost']} "
            f"| {result['delta_cost']} "
            f"| {result['d_kl_count']}/{context_count} ({d_kl:.3f}) "
            f"| {result['door_leverage_total']}/{context_count} "
            f"({mean_leverage:.3f}) "
            f"| {result['reachable_states']} |"
        )


def main():
    results = [
        analyze_map("Map A", map_a),
        analyze_map("Map B", map_b),
    ]
    print_results(results)


if __name__ == "__main__":
    main()
