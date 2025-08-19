"""
Unit tests for domain events system.

Tests event creation, serialization, and event logging functionality.
"""

import pytest
import time
from first_rat_local.core.events import (
    DomainEvent, EventLogger, create_resource_gained_event, create_resource_spent_event,
    create_shop_bought_event, create_part_built_event, create_game_ended_event,
    format_event_for_display
)
from first_rat_local.core.enums import DomainEventType, Resource, RocketPart


class TestDomainEvent:
    """Test cases for DomainEvent creation and properties."""
    
    def test_domain_event_creation(self):
        """Test basic domain event creation."""
        event = DomainEvent(
            type=DomainEventType.RESOURCE_GAINED,
            payload={"resource": "CHEESE", "amount": 2},
            actor="player1",
            timestamp=1234567890
        )
        
        assert event.type == DomainEventType.RESOURCE_GAINED
        assert event.payload["resource"] == "CHEESE"
        assert event.payload["amount"] == 2
        assert event.actor == "player1"
        assert event.timestamp == 1234567890
    
    def test_domain_event_auto_timestamp(self):
        """Test that timestamp is automatically set when not provided."""
        before_time = int(time.time() * 1000)
        
        event = DomainEvent(
            type=DomainEventType.LOG,
            payload={"message": "test"},
            actor="system",
            timestamp=0  # Should be auto-set
        )
        
        after_time = int(time.time() * 1000)
        
        assert before_time <= event.timestamp <= after_time


class TestEventCreationHelpers:
    """Test cases for event creation helper functions."""
    
    def test_create_resource_gained_event(self):
        """Test resource gained event creation."""
        event = create_resource_gained_event("player1", Resource.CHEESE, 3, "space")
        
        assert event.type == DomainEventType.RESOURCE_GAINED
        assert event.actor == "player1"
        assert event.payload["resource"] == "CHEESE"
        assert event.payload["amount"] == 3
        assert event.payload["source"] == "space"
        assert event.timestamp > 0
    
    def test_create_resource_spent_event(self):
        """Test resource spent event creation."""
        event = create_resource_spent_event("player2", Resource.TIN_CAN, 2, "rocket_part")
        
        assert event.type == DomainEventType.RESOURCE_SPENT
        assert event.actor == "player2"
        assert event.payload["resource"] == "TIN_CAN"
        assert event.payload["amount"] == 2
        assert event.payload["purpose"] == "rocket_part"
    
    def test_create_shop_bought_event(self):
        """Test shop purchase event creation."""
        cost = {"TIN_CAN": 2}
        event = create_shop_bought_event("player1", "SHOP_MOLE", "capacity", cost, "rat1")
        
        assert event.type == DomainEventType.SHOP_BOUGHT
        assert event.actor == "player1"
        assert event.payload["shop_type"] == "SHOP_MOLE"
        assert event.payload["item"] == "capacity"
        assert event.payload["cost"] == cost
        assert event.payload["rat_id"] == "rat1"
    
    def test_create_part_built_event(self):
        """Test rocket part built event creation."""
        cost = {"TIN_CAN": 3, "CHEESE": 1}
        event = create_part_built_event("player2", RocketPart.NOSE, cost, 4)
        
        assert event.type == DomainEventType.PART_BUILT
        assert event.actor == "player2"
        assert event.payload["part"] == "NOSE"
        assert event.payload["cost"] == cost
        assert event.payload["immediate_points"] == 4
    
    def test_create_game_ended_event(self):
        """Test game ended event creation."""
        winners = ["player1", "player2"]
        scores = {"player1": 25, "player2": 25, "player3": 20}
        event = create_game_ended_event(winners, scores, "fourth_rat_on_rocket")
        
        assert event.type == DomainEventType.GAME_ENDED
        assert event.actor == "system"
        assert event.payload["winner_ids"] == winners
        assert event.payload["final_scores"] == scores
        assert event.payload["trigger"] == "fourth_rat_on_rocket"


class TestEventLogger:
    """Test cases for EventLogger functionality."""
    
    def create_test_events(self) -> list[DomainEvent]:
        """Create a set of test events."""
        return [
            create_resource_gained_event("player1", Resource.CHEESE, 2, "space"),
            create_resource_spent_event("player1", Resource.TIN_CAN, 1, "shop"),
            create_resource_gained_event("player2", Resource.SODA, 1, "space"),
            create_shop_bought_event("player1", "SHOP_MOLE", "capacity", {"TIN_CAN": 2}, "rat1"),
            create_part_built_event("player2", RocketPart.ENGINE, {"TIN_CAN": 4}, 5)
        ]
    
    def test_event_logger_creation(self):
        """Test EventLogger creation and basic functionality."""
        logger = EventLogger()
        assert len(logger.events) == 0
        
        event = create_resource_gained_event("player1", Resource.CHEESE, 1)
        logger.add_event(event)
        
        assert len(logger.events) == 1
        assert logger.events[0] == event
    
    def test_add_multiple_events(self):
        """Test adding multiple events at once."""
        logger = EventLogger()
        events = self.create_test_events()
        
        logger.add_events(events)
        assert len(logger.events) == 5
    
    def test_get_events_by_type(self):
        """Test filtering events by type."""
        logger = EventLogger()
        events = self.create_test_events()
        logger.add_events(events)
        
        resource_events = logger.get_events_by_type(DomainEventType.RESOURCE_GAINED)
        assert len(resource_events) == 2
        
        shop_events = logger.get_events_by_type(DomainEventType.SHOP_BOUGHT)
        assert len(shop_events) == 1
        
        nonexistent_events = logger.get_events_by_type(DomainEventType.GAME_ENDED)
        assert len(nonexistent_events) == 0
    
    def test_get_events_by_actor(self):
        """Test filtering events by actor."""
        logger = EventLogger()
        events = self.create_test_events()
        logger.add_events(events)
        
        player1_events = logger.get_events_by_actor("player1")
        assert len(player1_events) == 3
        
        player2_events = logger.get_events_by_actor("player2")
        assert len(player2_events) == 2
        
        nonexistent_events = logger.get_events_by_actor("player3")
        assert len(nonexistent_events) == 0
    
    def test_get_events_since_timestamp(self):
        """Test filtering events by timestamp."""
        logger = EventLogger()
        
        # Create events with specific timestamps
        old_event = DomainEvent(
            type=DomainEventType.LOG,
            payload={"message": "old"},
            actor="system",
            timestamp=1000
        )
        
        new_event = DomainEvent(
            type=DomainEventType.LOG,
            payload={"message": "new"},
            actor="system",
            timestamp=2000
        )
        
        logger.add_events([old_event, new_event])
        
        recent_events = logger.get_events_since(1500)
        assert len(recent_events) == 1
        assert recent_events[0] == new_event
    
    def test_get_recent_events(self):
        """Test getting recent events."""
        logger = EventLogger()
        events = self.create_test_events()
        logger.add_events(events)
        
        # Get last 3 events
        recent = logger.get_recent_events(3)
        assert len(recent) == 3
        assert recent == events[-3:]
        
        # Get more events than available
        all_recent = logger.get_recent_events(10)
        assert len(all_recent) == 5
        assert all_recent == events
    
    def test_clear_events(self):
        """Test clearing all events."""
        logger = EventLogger()
        events = self.create_test_events()
        logger.add_events(events)
        
        assert len(logger.events) == 5
        logger.clear()
        assert len(logger.events) == 0
    
    def test_serialization_to_dict_list(self):
        """Test serializing events to dictionary list."""
        logger = EventLogger()
        event = create_resource_gained_event("player1", Resource.CHEESE, 2)
        logger.add_event(event)
        
        dict_list = logger.to_dict_list()
        assert len(dict_list) == 1
        
        event_dict = dict_list[0]
        assert event_dict["type"] == "RESOURCE_GAINED"
        assert event_dict["actor"] == "player1"
        assert event_dict["payload"]["resource"] == "CHEESE"
        assert event_dict["payload"]["amount"] == 2
        assert "timestamp" in event_dict
    
    def test_deserialization_from_dict_list(self):
        """Test deserializing events from dictionary list."""
        dict_list = [
            {
                "type": "RESOURCE_GAINED",
                "payload": {"resource": "CHEESE", "amount": 2, "source": "space"},
                "actor": "player1",
                "timestamp": 1234567890
            },
            {
                "type": "SHOP_BOUGHT",
                "payload": {"shop_type": "SHOP_MOLE", "item": "capacity", "cost": {"TIN_CAN": 2}, "rat_id": "rat1"},
                "actor": "player2",
                "timestamp": 1234567891
            }
        ]
        
        logger = EventLogger.from_dict_list(dict_list)
        assert len(logger.events) == 2
        
        event1 = logger.events[0]
        assert event1.type == DomainEventType.RESOURCE_GAINED
        assert event1.actor == "player1"
        assert event1.payload["resource"] == "CHEESE"
        
        event2 = logger.events[1]
        assert event2.type == DomainEventType.SHOP_BOUGHT
        assert event2.actor == "player2"


class TestEventFormatting:
    """Test cases for event display formatting."""
    
    def test_format_resource_gained_event(self):
        """Test formatting resource gained event."""
        event = create_resource_gained_event("玩家1", Resource.CHEESE, 3, "格子")
        formatted = format_event_for_display(event)
        assert "玩家1 获得了 3 个 CHEESE (来源: 格子)" == formatted
    
    def test_format_shop_bought_event(self):
        """Test formatting shop purchase event."""
        event = create_shop_bought_event("玩家2", "鼹鼠店", "背包扩容", {"TIN_CAN": 2}, "rat1")
        formatted = format_event_for_display(event)
        assert "玩家2 在 鼹鼠店 购买了 背包扩容" == formatted
    
    def test_format_part_built_event(self):
        """Test formatting rocket part built event."""
        event = create_part_built_event("玩家1", RocketPart.ENGINE, {"TIN_CAN": 4}, 5)
        formatted = format_event_for_display(event)
        assert "玩家1 建造了火箭部件 ENGINE，获得 5 分" == formatted
    
    def test_format_game_ended_event(self):
        """Test formatting game ended event."""
        event = create_game_ended_event(["玩家1"], {"玩家1": 30, "玩家2": 25}, "第四只老鼠登船")
        formatted = format_event_for_display(event)
        assert "游戏结束！获胜者: 玩家1 (触发条件: 第四只老鼠登船)" == formatted