"""
Domain events system for First Rat game.

This module defines domain events used for logging, replay, and UI updates.
领域事件系统，用于日志记录、回放和界面更新。
"""

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from .enums import DomainEventType, Resource, RocketPart


@dataclass
class DomainEvent:
    """
    Represents a domain event that occurred during gameplay.
    
    表示游戏过程中发生的领域事件。
    """
    type: DomainEventType                    # 事件类型
    payload: Dict[str, Any]                  # 事件数据
    actor: str                               # 触发事件的玩家ID
    timestamp: int                           # 事件时间戳（毫秒）
    
    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp == 0:
            self.timestamp = int(time.time() * 1000)


# Event creation helper functions
def create_resource_gained_event(actor: str, resource: Resource, amount: int, 
                                source: str = "unknown") -> DomainEvent:
    """
    Create a resource gained event.
    
    创建资源获得事件。
    
    Args:
        actor: 玩家ID
        resource: 获得的资源类型
        amount: 获得的数量
        source: 资源来源（如"space", "shop", "track"等）
    """
    return DomainEvent(
        type=DomainEventType.RESOURCE_GAINED,
        payload={
            "resource": resource.value,
            "amount": amount,
            "source": source
        },
        actor=actor,
        timestamp=0  # Will be set in __post_init__
    )


def create_resource_spent_event(actor: str, resource: Resource, amount: int,
                               purpose: str = "unknown") -> DomainEvent:
    """
    Create a resource spent event.
    
    创建资源消耗事件。
    """
    return DomainEvent(
        type=DomainEventType.RESOURCE_SPENT,
        payload={
            "resource": resource.value,
            "amount": amount,
            "purpose": purpose
        },
        actor=actor,
        timestamp=0
    )


def create_inventory_changed_event(actor: str, capacity_change: int = 0,
                                 x2_activated: bool = False, x2_consumed: bool = False) -> DomainEvent:
    """
    Create an inventory changed event.
    
    创建背包变化事件。
    """
    return DomainEvent(
        type=DomainEventType.INVENTORY_CHANGED,
        payload={
            "capacity_change": capacity_change,
            "x2_activated": x2_activated,
            "x2_consumed": x2_consumed
        },
        actor=actor,
        timestamp=0
    )


def create_track_advanced_event(actor: str, track_name: str, new_level: int,
                               reward: Optional[Dict[str, Any]] = None) -> DomainEvent:
    """
    Create a track advanced event.
    
    创建轨道推进事件。
    """
    return DomainEvent(
        type=DomainEventType.TRACK_ADVANCED,
        payload={
            "track_name": track_name,
            "new_level": new_level,
            "reward": reward
        },
        actor=actor,
        timestamp=0
    )


def create_shop_bought_event(actor: str, shop_type: str, item: str,
                           cost: Dict[str, int], rat_id: str) -> DomainEvent:
    """
    Create a shop purchase event.
    
    创建商店购买事件。
    """
    return DomainEvent(
        type=DomainEventType.SHOP_BOUGHT,
        payload={
            "shop_type": shop_type,
            "item": item,
            "cost": cost,
            "rat_id": rat_id
        },
        actor=actor,
        timestamp=0
    )


def create_shop_stolen_event(actor: str, shop_type: str, item: str, rat_id: str) -> DomainEvent:
    """
    Create a shop theft event.
    
    创建商店偷窃事件。
    """
    return DomainEvent(
        type=DomainEventType.SHOP_STOLEN,
        payload={
            "shop_type": shop_type,
            "item": item,
            "rat_id": rat_id
        },
        actor=actor,
        timestamp=0
    )


def create_sent_home_event(actor: str, rat_id: str, reason: str = "theft") -> DomainEvent:
    """
    Create a sent home event (rat punishment).
    
    创建老鼠被送回起点事件。
    """
    return DomainEvent(
        type=DomainEventType.SENT_HOME,
        payload={
            "rat_id": rat_id,
            "reason": reason
        },
        actor=actor,
        timestamp=0
    )


def create_on_rocket_event(actor: str, rat_id: str) -> DomainEvent:
    """
    Create a rat boarding rocket event.
    
    创建老鼠登船事件。
    """
    return DomainEvent(
        type=DomainEventType.ON_ROCKET,
        payload={
            "rat_id": rat_id
        },
        actor=actor,
        timestamp=0
    )


def create_new_rat_gained_event(actor: str, rat_id: str) -> DomainEvent:
    """
    Create a new rat gained event.
    
    创建获得新老鼠事件。
    """
    return DomainEvent(
        type=DomainEventType.NEW_RAT_GAINED,
        payload={
            "rat_id": rat_id
        },
        actor=actor,
        timestamp=0
    )


def create_score_changed_event(actor: str, points: int, reason: str,
                             new_total: int) -> DomainEvent:
    """
    Create a score changed event.
    
    创建分数变化事件。
    """
    return DomainEvent(
        type=DomainEventType.SCORE_CHANGED,
        payload={
            "points": points,
            "reason": reason,
            "new_total": new_total
        },
        actor=actor,
        timestamp=0
    )


def create_part_built_event(actor: str, part: RocketPart, cost: Dict[str, int],
                          immediate_points: int) -> DomainEvent:
    """
    Create a rocket part built event.
    
    创建火箭部件建造事件。
    """
    return DomainEvent(
        type=DomainEventType.PART_BUILT,
        payload={
            "part": part.value,
            "cost": cost,
            "immediate_points": immediate_points
        },
        actor=actor,
        timestamp=0
    )


def create_cheese_donated_event(actor: str, amount: int, points: int) -> DomainEvent:
    """
    Create a cheese donation event.
    
    创建奶酪捐赠事件。
    """
    return DomainEvent(
        type=DomainEventType.CHEESE_DONATED,
        payload={
            "amount": amount,
            "points": points
        },
        actor=actor,
        timestamp=0
    )


def create_turn_ended_event(actor: str, round_number: int) -> DomainEvent:
    """
    Create a turn ended event.
    
    创建回合结束事件。
    """
    return DomainEvent(
        type=DomainEventType.TURN_ENDED,
        payload={
            "round_number": round_number
        },
        actor=actor,
        timestamp=0
    )


def create_game_ended_event(winner_ids: List[str], final_scores: Dict[str, int],
                          trigger: str) -> DomainEvent:
    """
    Create a game ended event.
    
    创建游戏结束事件。
    """
    return DomainEvent(
        type=DomainEventType.GAME_ENDED,
        payload={
            "winner_ids": winner_ids,
            "final_scores": final_scores,
            "trigger": trigger
        },
        actor="system",
        timestamp=0
    )


def create_log_event(actor: str, message: str, level: str = "info") -> DomainEvent:
    """
    Create a general log event.
    
    创建一般日志事件。
    """
    return DomainEvent(
        type=DomainEventType.LOG,
        payload={
            "message": message,
            "level": level
        },
        actor=actor,
        timestamp=0
    )


class EventLogger:
    """
    Utility class for managing and filtering domain events.
    
    用于管理和过滤领域事件的工具类。
    """
    
    def __init__(self):
        self.events: List[DomainEvent] = []
    
    def add_event(self, event: DomainEvent) -> None:
        """Add an event to the log."""
        self.events.append(event)
    
    def add_events(self, events: List[DomainEvent]) -> None:
        """Add multiple events to the log."""
        self.events.extend(events)
    
    def get_events_by_type(self, event_type: DomainEventType) -> List[DomainEvent]:
        """Get all events of a specific type."""
        return [event for event in self.events if event.type == event_type]
    
    def get_events_by_actor(self, actor: str) -> List[DomainEvent]:
        """Get all events by a specific actor."""
        return [event for event in self.events if event.actor == actor]
    
    def get_events_since(self, timestamp: int) -> List[DomainEvent]:
        """Get all events since a specific timestamp."""
        return [event for event in self.events if event.timestamp >= timestamp]
    
    def get_recent_events(self, count: int = 10) -> List[DomainEvent]:
        """Get the most recent events."""
        return self.events[-count:] if len(self.events) >= count else self.events
    
    def clear(self) -> None:
        """Clear all events."""
        self.events.clear()
    
    def to_dict_list(self) -> List[Dict[str, Any]]:
        """Convert all events to a list of dictionaries for serialization."""
        return [
            {
                "type": event.type.value,
                "payload": event.payload,
                "actor": event.actor,
                "timestamp": event.timestamp
            }
            for event in self.events
        ]
    
    @classmethod
    def from_dict_list(cls, data: List[Dict[str, Any]]) -> "EventLogger":
        """Create an EventLogger from a list of dictionaries."""
        logger = cls()
        for event_data in data:
            event = DomainEvent(
                type=DomainEventType(event_data["type"]),
                payload=event_data["payload"],
                actor=event_data["actor"],
                timestamp=event_data["timestamp"]
            )
            logger.add_event(event)
        return logger


def format_event_for_display(event: DomainEvent) -> str:
    """
    Format an event for human-readable display.
    
    将事件格式化为人类可读的显示文本。
    """
    actor = event.actor
    payload = event.payload
    
    if event.type == DomainEventType.RESOURCE_GAINED:
        return f"{actor} 获得了 {payload['amount']} 个 {payload['resource']} (来源: {payload['source']})"
    
    elif event.type == DomainEventType.RESOURCE_SPENT:
        return f"{actor} 消耗了 {payload['amount']} 个 {payload['resource']} (用途: {payload['purpose']})"
    
    elif event.type == DomainEventType.SHOP_BOUGHT:
        return f"{actor} 在 {payload['shop_type']} 购买了 {payload['item']}"
    
    elif event.type == DomainEventType.SHOP_STOLEN:
        return f"{actor} 从 {payload['shop_type']} 偷取了 {payload['item']}，老鼠 {payload['rat_id']} 被送回起点"
    
    elif event.type == DomainEventType.ON_ROCKET:
        return f"{actor} 的老鼠 {payload['rat_id']} 登上了火箭"
    
    elif event.type == DomainEventType.NEW_RAT_GAINED:
        return f"{actor} 获得了新老鼠 {payload['rat_id']}"
    
    elif event.type == DomainEventType.PART_BUILT:
        return f"{actor} 建造了火箭部件 {payload['part']}，获得 {payload['immediate_points']} 分"
    
    elif event.type == DomainEventType.CHEESE_DONATED:
        return f"{actor} 捐赠了 {payload['amount']} 个奶酪，获得 {payload['points']} 分"
    
    elif event.type == DomainEventType.SCORE_CHANGED:
        return f"{actor} 因 {payload['reason']} 获得 {payload['points']} 分，总分: {payload['new_total']}"
    
    elif event.type == DomainEventType.TURN_ENDED:
        return f"{actor} 结束了第 {payload['round_number']} 回合"
    
    elif event.type == DomainEventType.GAME_ENDED:
        winners = ", ".join(payload['winner_ids'])
        return f"游戏结束！获胜者: {winners} (触发条件: {payload['trigger']})"
    
    elif event.type == DomainEventType.LOG:
        return f"[{payload['level'].upper()}] {payload['message']}"
    
    else:
        return f"{actor}: {event.type.value} - {payload}"