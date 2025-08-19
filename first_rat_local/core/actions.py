"""
Action system for First Rat game.

This module defines all player actions using the Command pattern.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple
from .enums import ActionType, SpaceKind, RocketPart


@dataclass
class Action:
    """
    Base action class representing a player's action.
    
    所有玩家动作的基类，使用命令模式。
    """
    type: ActionType
    payload: Dict[str, Any]


def create_move_action(moves: List[Tuple[str, int]]) -> Action:
    """
    Create a move action.
    
    创建移动动作。
    
    Args:
        moves: List of (rat_id, steps) tuples
               - Single rat: 1 rat with 1-5 steps
               - Multiple rats: 2-4 rats with 1-3 steps each
    
    Example:
        create_move_action([("rat1", 3)])  # Move rat1 3 steps
        create_move_action([("rat1", 2), ("rat2", 1)])  # Move rat1 2 steps, rat2 1 step
    """
    return Action(
        type=ActionType.MOVE,
        payload={"moves": moves}
    )


def create_buy_action(shop_kind: SpaceKind, item: str, payer_rat_id: str) -> Action:
    """
    Create a buy action for purchasing from shops.
    
    创建商店购买动作。
    
    Args:
        shop_kind: Type of shop (SHOP_MOLE, SHOP_FROG, SHOP_CROW)
        item: Item to purchase ("capacity", "x2", "bottlecap")
        payer_rat_id: ID of the rat at the shop location
    
    Example:
        create_buy_action(SpaceKind.SHOP_MOLE, "capacity", "rat1")
    """
    return Action(
        type=ActionType.BUY,
        payload={
            "shop_kind": shop_kind,
            "item": item,
            "payer_rat_id": payer_rat_id
        }
    )


def create_steal_action(shop_kind: SpaceKind, target_item: str, payer_rat_id: str) -> Action:
    """
    Create a steal action for stealing from shops.
    
    创建商店偷窃动作。偷窃会获得物品但老鼠被送回起点。
    
    Args:
        shop_kind: Type of shop to steal from
        target_item: Item to steal
        payer_rat_id: ID of the rat performing the theft
    
    Example:
        create_steal_action(SpaceKind.SHOP_FROG, "x2", "rat2")
    """
    return Action(
        type=ActionType.STEAL,
        payload={
            "shop_kind": shop_kind,
            "target_item": target_item,
            "payer_rat_id": payer_rat_id
        }
    )


def create_build_rocket_action(part: RocketPart) -> Action:
    """
    Create a rocket building action.
    
    创建火箭建造动作。
    
    Args:
        part: Rocket part to build (NOSE, TANK, ENGINE, FIN_A, FIN_B)
    
    Example:
        create_build_rocket_action(RocketPart.ENGINE)
    """
    return Action(
        type=ActionType.BUILD_ROCKET,
        payload={"part": part}
    )


def create_donate_cheese_action(amount: int) -> Action:
    """
    Create a cheese donation action.
    
    创建奶酪捐赠动作。
    
    Args:
        amount: Amount of cheese to donate (1-4)
    
    Example:
        create_donate_cheese_action(3)  # Donate 3 cheese for points
    """
    return Action(
        type=ActionType.DONATE_CHEESE,
        payload={"amount": amount}
    )


def create_end_turn_action() -> Action:
    """
    Create an end turn action.
    
    创建结束回合动作。
    
    Example:
        create_end_turn_action()
    """
    return Action(
        type=ActionType.END_TURN,
        payload={}
    )


# Action validation helpers
def validate_move_payload(payload: Dict[str, Any]) -> bool:
    """
    Validate move action payload structure.
    
    验证移动动作载荷结构。
    """
    if "moves" not in payload:
        return False
    
    moves = payload["moves"]
    if not isinstance(moves, list) or len(moves) == 0:
        return False
    
    # Check each move tuple
    for move in moves:
        if not isinstance(move, (list, tuple)) or len(move) != 2:
            return False
        rat_id, steps = move
        if not isinstance(rat_id, str) or not isinstance(steps, int):
            return False
        if steps < 1:
            return False
    
    # Validate move rules
    if len(moves) == 1:
        # Single rat: 1-5 steps
        _, steps = moves[0]
        return 1 <= steps <= 5
    elif 2 <= len(moves) <= 4:
        # Multiple rats: each 1-3 steps
        for _, steps in moves:
            if not (1 <= steps <= 3):
                return False
        return True
    else:
        return False


def validate_buy_payload(payload: Dict[str, Any]) -> bool:
    """Validate buy action payload structure."""
    required_keys = ["shop_kind", "item", "payer_rat_id"]
    return all(key in payload for key in required_keys)


def validate_steal_payload(payload: Dict[str, Any]) -> bool:
    """Validate steal action payload structure."""
    required_keys = ["shop_kind", "target_item", "payer_rat_id"]
    return all(key in payload for key in required_keys)


def validate_build_payload(payload: Dict[str, Any]) -> bool:
    """Validate build rocket action payload structure."""
    return "part" in payload and isinstance(payload["part"], RocketPart)


def validate_donate_payload(payload: Dict[str, Any]) -> bool:
    """Validate donate cheese action payload structure."""
    if "amount" not in payload:
        return False
    amount = payload["amount"]
    return isinstance(amount, int) and 1 <= amount <= 4


def validate_action_payload(action: Action) -> bool:
    """
    Validate that an action has a properly structured payload.
    
    验证动作载荷结构是否正确。
    """
    validators = {
        ActionType.MOVE: validate_move_payload,
        ActionType.BUY: validate_buy_payload,
        ActionType.STEAL: validate_steal_payload,
        ActionType.BUILD_ROCKET: validate_build_payload,
        ActionType.DONATE_CHEESE: validate_donate_payload,
        ActionType.END_TURN: lambda p: True  # End turn has no payload requirements
    }
    
    validator = validators.get(action.type)
    if validator is None:
        return False
    
    return validator(action.payload)