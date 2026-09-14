"""事件检测
"""


def detect_events(previous, current, objects):
    """把状态变化转成事件字符"""
    if previous["position"] == current["position"]:
        return set()

    if not previous["door_open"] and current["door_open"]:
        return {"OPEN_DOOR"}

    position = current["position"]
    if position == objects["key"]:
        return {"GET_KEY"}
    if position == objects["beef"]:
        return {"GET_BEEF"}
    if position == objects["kitchen"] and current["has_beef"]:
        return {"COOK"}
    if position == objects["goal"]:
        return {"REACH_GOAL"}

    return set()
