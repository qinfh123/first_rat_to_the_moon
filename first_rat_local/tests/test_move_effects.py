"""
Unit tests for move action effect resolution.

Tests movement effects including resource collection and rat boarding.
"""

import pytest
from first_rat_local.core.rules import EffectResolver
from first_rat_local.core.models import GameState, Board, Space, Player, Rat, Inventory, Rocket
from first_rat_local.core.actions import create_move_action
from first_rat_local.core.config import Config
from first_rat_local.core.enums import Color, SpaceKind, Resource, DomainEventType


class TestMoveEffects:
    """Test cases for move action effect resolution."""
    
    def create_test_game_state(self) -> GameState:
        """Create a test game state with various space types."""
        # Create board with different space types
        spaces = [
            Space(0, 0, Color.GREEN, SpaceKind.START),
            Space(1, 1, Color.YELLOW, SpaceKind.RESOURCE, {"resource": Resource.CHEESE.value, "amount": 2}),
            Space(2, 2, Color.RED, SpaceKind.RESOURCE, {"resource": Resource.TIN_CAN.value, "amount": 1}),
            Space(3, 3, Color.BLUE, SpaceKind.LIGHTBULB_TRACK, {"track_gain": 1}),
            Space(4, 4, Color.GREEN, SpaceKind.LAUNCH_PAD)
        ]
        
        board = Board(spaces=spaces, start_index=0, launch_index=4)
        
        # Create player with rats
        player1 = Player(
            player_id="p1",
            name="Player 1",
            rats=[
                Rat("r1", "p1", 0),  # At start
                Rat("r2", "p1", 0)   # At start
            ],
            inv=Inventory(capacity=5)
        )
        
        return GameState(
            board=board,
            players=[player1],
            rocket=Rocket(),
            current_player=0
        )
    
    def test_move_to_resource_space(self):
        """Test moving to a resource space and gaining resources."""
        state = self.create_test_game_state()
        config = Config.default()
        resolver = EffectResolver(config)
        
        # Move rat to cheese space (index 1)
        action = create_move_action([("r1", 1)])
        events = resolver.resolve_move(state, action, "p1")
        
        # Check rat position updated
        rat = next(r for r in state.players[0].rats if r.rat_id == "r1")
        assert rat.space_index == 1
        
        # Check resource gained
        player = state.players[0]
        assert player.inv.has(Resource.CHEESE, 2)
        
        # Check events
        resource_events = [e for e in events if e.type == DomainEventType.RESOURCE_GAINED]
        assert len(resource_events) == 1
        assert resource_events[0].payload["resource"] == "CHEESE"
        assert resource_events[0].payload["amount"] == 2
        assert resource_events[0].payload["source"] == "space"
    
    def test_move_with_x2_effect(self):
        """Test moving to resource space with x2 effect active."""
        state = self.create_test_game_state()
        config = Config.default()
        resolver = EffectResolver(config)
        
        # Activate x2 effect
        state.players[0].inv.x2_active = True
        
        # Move rat to cheese space (index 1, gives 2 cheese normally)
        action = create_move_action([("r1", 1)])
        events = resolver.resolve_move(state, action, "p1")
        
        # Check doubled resource gained
        player = state.players[0]
        assert player.inv.has(Resource.CHEESE, 4)  # 2 * 2 = 4
        
        # Check x2 effect consumed
        assert player.inv.x2_active is False
        
        # Check events
        resource_events = [e for e in events if e.type == DomainEventType.RESOURCE_GAINED]
        x2_events = [e for e in events if e.type == DomainEventType.INVENTORY_CHANGED]
        
        assert len(resource_events) == 1
        assert resource_events[0].payload["amount"] == 4
        assert len(x2_events) == 1
        assert x2_events[0].payload["x2_consumed"] is True
    
    def test_move_to_full_inventory(self):
        """Test moving to resource space when inventory is nearly full."""
        state = self.create_test_game_state()
        config = Config.default()
        resolver = EffectResolver(config)
        
        # Fill inventory to capacity - 1
        player = state.players[0]
        player.inv.add(Resource.SODA, 4)  # Capacity is 5, so 1 space left
        
        # Move rat to cheese space (index 1, gives 2 cheese)
        action = create_move_action([("r1", 1)])
        events = resolver.resolve_move(state, action, "p1")
        
        # Check only 1 cheese gained (limited by available space)
        assert player.inv.has(Resource.CHEESE, 1)
        assert not player.inv.has(Resource.CHEESE, 2)
        
        # Check events
        resource_events = [e for e in events if e.type == DomainEventType.RESOURCE_GAINED]
        assert len(resource_events) == 1
        assert resource_events[0].payload["amount"] == 1
    
    def test_move_to_completely_full_inventory(self):
        """Test moving to resource space when inventory is completely full."""
        state = self.create_test_game_state()
        config = Config.default()
        resolver = EffectResolver(config)
        
        # Fill inventory completely
        player = state.players[0]
        player.inv.add(Resource.SODA, 5)  # Capacity is 5
        
        # Move rat to cheese space (index 1)
        action = create_move_action([("r1", 1)])
        events = resolver.resolve_move(state, action, "p1")
        
        # Check no cheese gained
        assert not player.inv.has(Resource.CHEESE, 1)
        
        # Check no resource gained events
        resource_events = [e for e in events if e.type == DomainEventType.RESOURCE_GAINED]
        assert len(resource_events) == 0
    
    def test_move_to_lightbulb_track(self):
        """Test moving to lightbulb track space."""
        state = self.create_test_game_state()
        config = Config.default()
        resolver = EffectResolver(config)
        
        # Move rat to lightbulb track space (index 3)
        action = create_move_action([("r1", 3)])
        events = resolver.resolve_move(state, action, "p1")
        
        # Check track advanced
        player = state.players[0]
        assert player.tracks["lightbulb"] == 1
        
        # Check for track reward (level 1 should give 1 point)
        assert player.score == 1
        
        # Check events
        score_events = [e for e in events if e.type == DomainEventType.SCORE_CHANGED]
        assert len(score_events) == 1
        assert score_events[0].payload["points"] == 1
        assert score_events[0].payload["reason"] == "lightbulb_track_level_1"
    
    def test_move_to_launch_pad_boarding(self):
        """Test moving to launch pad and boarding rocket."""
        state = self.create_test_game_state()
        config = Config.default()
        resolver = EffectResolver(config)
        
        # Move rat to launch pad (index 4)
        action = create_move_action([("r1", 4)])
        events = resolver.resolve_move(state, action, "p1")
        
        # Check rat boarded rocket
        rat = next(r for r in state.players[0].rats if r.rat_id == "r1")
        assert rat.on_rocket is True
        
        # Check new rat spawned (player should now have 3 rats)
        player = state.players[0]
        assert len(player.rats) == 3
        
        # Check new rat is at start
        new_rat = player.rats[2]  # Third rat (newest)
        assert new_rat.space_index == 0
        assert new_rat.on_rocket is False
        
        # Check events
        rocket_events = [e for e in events if e.type == DomainEventType.ON_ROCKET]
        new_rat_events = [e for e in events if e.type == DomainEventType.NEW_RAT_GAINED]
        
        assert len(rocket_events) == 1
        assert rocket_events[0].payload["rat_id"] == "r1"
        assert len(new_rat_events) == 1
    
    def test_move_to_launch_pad_max_rats(self):
        """Test moving to launch pad when player has max rats."""
        state = self.create_test_game_state()
        config = Config.default()
        resolver = EffectResolver(config)
        
        # Add rats to reach max (4 total)
        player = state.players[0]
        player.rats.extend([
            Rat("r3", "p1", 0),
            Rat("r4", "p1", 0)
        ])
        
        # Move rat to launch pad
        action = create_move_action([("r1", 4)])
        events = resolver.resolve_move(state, action, "p1")
        
        # Check rat boarded rocket
        rat = next(r for r in player.rats if r.rat_id == "r1")
        assert rat.on_rocket is True
        
        # Check no new rat spawned (still 4 rats)
        assert len(player.rats) == 4
        
        # Check events - should have rocket event but no new rat event
        rocket_events = [e for e in events if e.type == DomainEventType.ON_ROCKET]
        new_rat_events = [e for e in events if e.type == DomainEventType.NEW_RAT_GAINED]
        
        assert len(rocket_events) == 1
        assert len(new_rat_events) == 0
    
    def test_move_already_on_rocket_rat(self):
        """Test that rats already on rocket don't board again."""
        state = self.create_test_game_state()
        config = Config.default()
        resolver = EffectResolver(config)
        
        # Put rat on rocket and at launch pad
        rat = state.players[0].rats[0]
        rat.on_rocket = True
        rat.space_index = 4
        
        # Try to move rat (this shouldn't happen in normal gameplay, but test edge case)
        action = create_move_action([("r2", 4)])  # Move different rat
        events = resolver.resolve_move(state, action, "p1")
        
        # Check second rat boarded
        rat2 = next(r for r in state.players[0].rats if r.rat_id == "r2")
        assert rat2.on_rocket is True
        
        # Should still spawn new rat since we have < 4 total
        assert len(state.players[0].rats) == 3
    
    def test_multiple_rat_move_different_effects(self):
        """Test moving multiple rats to different space types."""
        state = self.create_test_game_state()
        config = Config.default()
        resolver = EffectResolver(config)
        
        # Move r1 to cheese space (index 1) and r2 to tin can space (index 2)
        # Both are different colors, so this would fail validation, but we're testing effects
        # Let's modify the board to make both spaces the same color
        state.board.spaces[2].color = Color.YELLOW  # Make tin can space same color as cheese
        
        action = create_move_action([("r1", 1), ("r2", 2)])
        events = resolver.resolve_move(state, action, "p1")
        
        # Check both rats moved
        rat1 = next(r for r in state.players[0].rats if r.rat_id == "r1")
        rat2 = next(r for r in state.players[0].rats if r.rat_id == "r2")
        assert rat1.space_index == 1
        assert rat2.space_index == 2
        
        # Check resources gained from both spaces
        player = state.players[0]
        assert player.inv.has(Resource.CHEESE, 2)
        assert player.inv.has(Resource.TIN_CAN, 1)
        
        # Check events
        resource_events = [e for e in events if e.type == DomainEventType.RESOURCE_GAINED]
        assert len(resource_events) == 2