"""
Input parsing and validation for First Rat CLI.

This module handles parsing user commands into game actions.
输入解析和验证系统，将用户命令转换为游戏动作。
"""

import re
from typing import List, Tuple, Optional
from ..core.actions import (
    Action, create_move_action, create_buy_action, create_steal_action,
    create_build_rocket_action, create_donate_cheese_action, create_end_turn_action
)
from ..core.enums import SpaceKind, RocketPart


class InputParseError(Exception):
    """Exception raised when input cannot be parsed."""
    pass


def parse_command(command: str) -> Action:
    """
    Parse a user command string into a game action.
    
    解析用户命令字符串为游戏动作。
    
    Args:
        command: User input string
    
    Returns:
        Parsed Action object
    
    Raises:
        InputParseError: If command cannot be parsed
    """
    command = command.strip().lower()
    
    if not command:
        raise InputParseError("请输入命令")
    
    # Split command into parts
    parts = command.split()
    cmd = parts[0]
    
    try:
        if cmd in ["move", "m", "移动"]:
            return parse_move_command(parts[1:])
        elif cmd in ["buy", "b", "购买"]:
            return parse_buy_command(parts[1:])
        elif cmd in ["steal", "s", "偷窃"]:
            return parse_steal_command(parts[1:])
        elif cmd in ["build", "建造"]:
            return parse_build_command(parts[1:])
        elif cmd in ["donate", "don", "捐赠"]:
            return parse_donate_command(parts[1:])
        elif cmd in ["end", "结束"]:
            return parse_end_command()
        else:
            raise InputParseError(f"未知命令: {cmd}")
    
    except (IndexError, ValueError) as e:
        raise InputParseError(f"命令格式错误: {str(e)}")


def parse_move_command(args: List[str]) -> Action:
    """
    Parse move command arguments.
    
    格式: move <老鼠ID> <步数> [<老鼠ID2> <步数2> ...]
    例如: move r1 3
          move r1 2 r2 1
    """
    if len(args) < 2:
        raise InputParseError("移动命令格式: move <老鼠ID> <步数> [<老鼠ID2> <步数2> ...]")
    
    if len(args) % 2 != 0:
        raise InputParseError("移动命令参数必须成对出现 (老鼠ID 步数)")
    
    moves = []
    for i in range(0, len(args), 2):
        rat_id = args[i]
        try:
            steps = int(args[i + 1])
        except ValueError:
            raise InputParseError(f"步数必须是数字: {args[i + 1]}")
        
        if steps < 1:
            raise InputParseError(f"步数必须大于0: {steps}")
        
        moves.append((rat_id, steps))
    
    return create_move_action(moves)


def parse_buy_command(args: List[str]) -> Action:
    """
    Parse buy command arguments.
    
    格式: buy <商店类型> <物品> <老鼠ID>
    例如: buy mole capacity r1
          buy frog x2 r2
          buy crow bottlecap r3
    """
    if len(args) != 3:
        raise InputParseError("购买命令格式: buy <商店类型> <物品> <老鼠ID>")
    
    shop_type_str, item, rat_id = args
    
    # Parse shop type
    shop_type = parse_shop_type(shop_type_str)
    
    # Validate item for shop type
    valid_items = {
        SpaceKind.SHOP_MOLE: ["capacity", "容量"],
        SpaceKind.SHOP_FROG: ["x2", "翻倍"],
        SpaceKind.SHOP_CROW: ["bottlecap", "瓶盖"]
    }
    
    if item not in valid_items[shop_type]:
        valid_list = ", ".join(valid_items[shop_type])
        raise InputParseError(f"{shop_type_str}店无效物品: {item}，有效物品: {valid_list}")
    
    # Normalize item name
    item_mapping = {
        "容量": "capacity",
        "翻倍": "x2",
        "瓶盖": "bottlecap"
    }
    normalized_item = item_mapping.get(item, item)
    
    return create_buy_action(shop_type, normalized_item, rat_id)


def parse_steal_command(args: List[str]) -> Action:
    """
    Parse steal command arguments.
    
    格式: steal <商店类型> <物品> <老鼠ID>
    例如: steal mole capacity r1
    """
    if len(args) != 3:
        raise InputParseError("偷窃命令格式: steal <商店类型> <物品> <老鼠ID>")
    
    shop_type_str, item, rat_id = args
    
    # Parse shop type
    shop_type = parse_shop_type(shop_type_str)
    
    # Validate item (same as buy)
    valid_items = {
        SpaceKind.SHOP_MOLE: ["capacity", "容量"],
        SpaceKind.SHOP_FROG: ["x2", "翻倍"],
        SpaceKind.SHOP_CROW: ["bottlecap", "瓶盖"]
    }
    
    if item not in valid_items[shop_type]:
        valid_list = ", ".join(valid_items[shop_type])
        raise InputParseError(f"{shop_type_str}店无效物品: {item}，有效物品: {valid_list}")
    
    # Normalize item name
    item_mapping = {
        "容量": "capacity",
        "翻倍": "x2",
        "瓶盖": "bottlecap"
    }
    normalized_item = item_mapping.get(item, item)
    
    return create_steal_action(shop_type, normalized_item, rat_id)


def parse_build_command(args: List[str]) -> Action:
    """
    Parse build command arguments.
    
    格式: build <部件名>
    例如: build nose
          build 火箭头
    """
    if len(args) != 1:
        raise InputParseError("建造命令格式: build <部件名>")
    
    part_str = args[0]
    
    # Parse rocket part
    part_mapping = {
        "nose": RocketPart.NOSE,
        "tank": RocketPart.TANK,
        "engine": RocketPart.ENGINE,
        "fin_a": RocketPart.FIN_A,
        "fin_b": RocketPart.FIN_B,
        "火箭头": RocketPart.NOSE,
        "燃料箱": RocketPart.TANK,
        "引擎": RocketPart.ENGINE,
        "尾翼a": RocketPart.FIN_A,
        "尾翼b": RocketPart.FIN_B,
    }
    
    part = part_mapping.get(part_str.lower())
    if part is None:
        valid_parts = list(part_mapping.keys())
        raise InputParseError(f"无效部件: {part_str}，有效部件: {', '.join(valid_parts)}")
    
    return create_build_rocket_action(part)


def parse_donate_command(args: List[str]) -> Action:
    """
    Parse donate command arguments.
    
    格式: donate <数量>
    例如: donate 3
    """
    if len(args) != 1:
        raise InputParseError("捐赠命令格式: donate <数量>")
    
    try:
        amount = int(args[0])
    except ValueError:
        raise InputParseError(f"捐赠数量必须是数字: {args[0]}")
    
    if not (1 <= amount <= 4):
        raise InputParseError(f"捐赠数量必须在1-4之间: {amount}")
    
    return create_donate_cheese_action(amount)


def parse_end_command() -> Action:
    """Parse end turn command."""
    return create_end_turn_action()


def parse_shop_type(shop_str: str) -> SpaceKind:
    """Parse shop type string into SpaceKind enum."""
    shop_mapping = {
        "mole": SpaceKind.SHOP_MOLE,
        "frog": SpaceKind.SHOP_FROG,
        "crow": SpaceKind.SHOP_CROW,
        "鼹鼠": SpaceKind.SHOP_MOLE,
        "青蛙": SpaceKind.SHOP_FROG,
        "乌鸦": SpaceKind.SHOP_CROW,
    }
    
    shop_type = shop_mapping.get(shop_str.lower())
    if shop_type is None:
        valid_shops = list(shop_mapping.keys())
        raise InputParseError(f"无效商店类型: {shop_str}，有效类型: {', '.join(valid_shops)}")
    
    return shop_type


def get_command_help() -> str:
    """Get help text for all available commands."""
    help_text = """
=== 命令帮助 ===

移动命令:
  move <老鼠ID> <步数>              - 移动单只老鼠 (1-5步)
  move <老鼠ID1> <步数1> <老鼠ID2> <步数2> ... - 移动多只老鼠 (各1-3步)
  例: move r1 3
      move r1 2 r2 1

商店命令:
  buy <商店> <物品> <老鼠ID>        - 购买商店物品
  steal <商店> <物品> <老鼠ID>      - 偷窃商店物品 (老鼠会被送回起点)
  
  商店类型: mole/鼹鼠, frog/青蛙, crow/乌鸦
  物品: capacity/容量, x2/翻倍, bottlecap/瓶盖
  例: buy mole capacity r1
      steal frog x2 r2

建造命令:
  build <部件>                     - 建造火箭部件
  部件: nose/火箭头, tank/燃料箱, engine/引擎, fin_a/尾翼a, fin_b/尾翼b
  例: build nose

捐赠命令:
  donate <数量>                    - 捐赠奶酪获得分数 (1-4个)
  例: donate 3

回合控制:
  end                             - 结束当前回合

其他:
  help                           - 显示此帮助信息
  quit/exit                      - 退出游戏
"""
    return help_text.strip()


def suggest_corrections(invalid_command: str) -> List[str]:
    """Suggest possible corrections for invalid commands."""
    suggestions = []
    
    # Common command variations
    command_suggestions = {
        "mov": "move",
        "移": "move", 
        "买": "buy",
        "偷": "steal",
        "造": "build",
        "捐": "donate",
        "结": "end"
    }
    
    first_word = invalid_command.split()[0].lower() if invalid_command.split() else ""
    
    if first_word in command_suggestions:
        suggestions.append(f"你是否想输入: {command_suggestions[first_word]}")
    
    # Check for partial matches
    all_commands = ["move", "buy", "steal", "build", "donate", "end", "help"]
    for cmd in all_commands:
        if cmd.startswith(first_word) and len(first_word) >= 2:
            suggestions.append(f"你是否想输入: {cmd}")
    
    return suggestions