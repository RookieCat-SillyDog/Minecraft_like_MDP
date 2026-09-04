"""三因子 Minecraft 的耦合规则。
"""

from env.factored_minecraft.maps import beef, key, location


def blue_key_opens_door(map_config, state, edge):
    """门边只在 Key 为 blue 时开放。"""
    if frozenset((edge[0], edge[2])) != map_config.door_edge:
        return True
    return state[key] == "blue"


def cook_only_in_kitchen(map_config, state, edge):
    """cook 动作只在 kitchen 开放。"""
    if edge[1] != "cook":
        return True
    return state[location] == map_config.landmarks["kitchen"]


# Map A / Map B 共用的耦合规则组合：K -> L -> B。
combined_rules = (blue_key_opens_door, cook_only_in_kitchen)
