"""
Unit tests for Action system.

Tests action creation, payload validation, and action factory functions.
"""

import pytest
from first_rat_local.core.actions import (
    Action, create_move_action, create_buy_action, create_steal_action,
    create_build_rocket_action, create_donate_cheese_action, create_end_turn_action,
    validate_action_payload, validate_move_payload
)
from first_rat_local.core.enums import ActionType, SpaceKind, RocketPart


class TestActionCreation:
    """Test cases for action factory functions."""
    
    def test_create_move_action_single_rat(self):
        """Test creating a move action for a single rat."""
        action = create_move_action([("rat1", 3)])
        assert action.type == ActionType.MOVE
        assert action.payload["moves"] == [("rat1", 3)]
    
    def test_create_move_action_multiple_rats(self):
        """Test creating a move action for multiple rats."""
        moves = [("rat1", 2), ("rat2", 1), ("rat3", 3)]
        action = create_move_action(moves)
        assert action.type == ActionType.MOVE
        assert action.payload["moves"] == moves
    
    def test_create_buy_action(self):
        """Test creating a buy action."""
        action = create_buy_action(SpaceKind.SHOP_MOLE, "capacity", "rat1")
        assert action.type == ActionType.BUY
        assert action.payload["shop_kind"] == SpaceKind.SHOP_MOLE
        assert action.payload["item"] == "capacity"
        assert action.payload["payer_rat_id"] == "rat1"
    
    def test_create_steal_action(self):
        """Test creating a steal action."""
        action = create_steal_action(SpaceKind.SHOP_FROG, "x2", "rat2")
        assert action.type == ActionType.STEAL
        assert action.payload["shop_kind"] == SpaceKind.SHOP_FROG
        assert action.payload["target_item"] == "x2"
        assert action.payload["payer_rat_id"] == "rat2"
    
    def test_create_build_rocket_action(self):
        """Test creating a build rocket action."""
        action = create_build_rocket_action(RocketPart.ENGINE)
        assert action.type == ActionType.BUILD_ROCKET
        assert action.payload["part"] == RocketPart.ENGINE
    
    def test_create_donate_cheese_action(self):
        """Test creating a donate cheese action."""
        action = create_donate_cheese_action(3)
        assert action.type == ActionType.DONATE_CHEESE
        assert action.payload["amount"] == 3
    
    def test_create_end_turn_action(self):
        """Test creating an end turn action."""
        action = create_end_turn_action()
        assert action.type == ActionType.END_TURN
        assert action.payload == {}


class TestMovePayloadValidation:
    """Test cases for move action payload validation."""
    
    def test_valid_single_rat_moves(self):
        """Test valid single rat move payloads."""
        # Test all valid step counts for single rat
        for steps in range(1, 6):
            payload = {"moves": [("rat1", steps)]}
            assert validate_move_payload(payload) is True
    
    def test_invalid_single_rat_moves(self):
        """Test invalid single rat move payloads."""
        # Too few steps
        payload = {"moves": [("rat1", 0)]}
        assert validate_move_payload(payload) is False
        
        # Too many steps
        payload = {"moves": [("rat1", 6)]}
        assert validate_move_payload(payload) is False
    
    def test_valid_multiple_rat_moves(self):
        """Test valid multiple rat move payloads."""
        # 2 rats, valid steps
        payload = {"moves": [("rat1", 2), ("rat2", 3)]}
        assert validate_move_payload(payload) is True
        
        # 4 rats, all valid steps
        payload = {"moves": [("rat1", 1), ("rat2", 2), ("rat3", 3), ("rat4", 1)]}
        assert validate_move_payload(payload) is True
    
    def test_invalid_multiple_rat_moves(self):
        """Test invalid multiple rat move payloads."""
        # Too many steps for multi-rat
        payload = {"moves": [("rat1", 4), ("rat2", 2)]}
        assert validate_move_payload(payload) is False
        
        # Too many rats
        payload = {"moves": [("rat1", 1), ("rat2", 1), ("rat3", 1), ("rat4", 1), ("rat5", 1)]}
        assert validate_move_payload(payload) is False
    
    def test_malformed_move_payloads(self):
        """Test malformed move payloads."""
        # Missing moves key
        payload = {}
        assert validate_move_payload(payload) is False
        
        # Empty moves list
        payload = {"moves": []}
        assert validate_move_payload(payload) is False
        
        # Invalid move tuple structure
        payload = {"moves": [("rat1",)]}  # Missing steps
        assert validate_move_payload(payload) is False
        
        payload = {"moves": [("rat1", "invalid")]}  # Non-integer steps
        assert validate_move_payload(payload) is False
        
        payload = {"moves": [(123, 2)]}  # Non-string rat_id
        assert validate_move_payload(payload) is False


class TestActionPayloadValidation:
    """Test cases for general action payload validation."""
    
    def test_valid_move_action(self):
        """Test validation of valid move action."""
        action = create_move_action([("rat1", 3)])
        assert validate_action_payload(action) is True
    
    def test_valid_buy_action(self):
        """Test validation of valid buy action."""
        action = create_buy_action(SpaceKind.SHOP_MOLE, "capacity", "rat1")
        assert validate_action_payload(action) is True
    
    def test_valid_steal_action(self):
        """Test validation of valid steal action."""
        action = create_steal_action(SpaceKind.SHOP_FROG, "x2", "rat2")
        assert validate_action_payload(action) is True
    
    def test_valid_build_action(self):
        """Test validation of valid build action."""
        action = create_build_rocket_action(RocketPart.NOSE)
        assert validate_action_payload(action) is True
    
    def test_valid_donate_action(self):
        """Test validation of valid donate action."""
        action = create_donate_cheese_action(2)
        assert validate_action_payload(action) is True
    
    def test_valid_end_turn_action(self):
        """Test validation of valid end turn action."""
        action = create_end_turn_action()
        assert validate_action_payload(action) is True
    
    def test_invalid_donate_amount(self):
        """Test validation of invalid donate amounts."""
        # Too little
        action = Action(ActionType.DONATE_CHEESE, {"amount": 0})
        assert validate_action_payload(action) is False
        
        # Too much
        action = Action(ActionType.DONATE_CHEESE, {"amount": 5})
        assert validate_action_payload(action) is False
    
    def test_missing_payload_keys(self):
        """Test validation with missing payload keys."""
        # Buy action missing keys
        action = Action(ActionType.BUY, {"shop_kind": SpaceKind.SHOP_MOLE})
        assert validate_action_payload(action) is False
        
        # Build action missing part
        action = Action(ActionType.BUILD_ROCKET, {})
        assert validate_action_payload(action) is False
    
    def test_unknown_action_type(self):
        """Test validation with unknown action type."""
        # Create action with invalid type (this would normally not be possible with enum)
        action = Action(type="INVALID", payload={})
        assert validate_action_payload(action) is False