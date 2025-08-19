"""
Unit tests for rules engine integration with GameState.

Tests complete action processing including validation, effect resolution, and history logging.
"""

import pytest
from first_rat_local.core.models import GameState, Board, Space, Player, Rat, Inventory, Rocket
from first_rat_local.core.actions import (
    create_move_action, create_buy_action, create_build_rocket_action, 
    create_donate_cheese_action, create_end_turn_action
)
from first_rat_local.core.config import Config
from first_rat_local.core.enums import Color, SpaceKind, Resource, RocketPart, DomainEventType


class TestRulesIntegration:
    """Test cases for complete action processing through the rules engine."""
    
    def create_test_game_state(self) -> GameState:
        """Create a comprehensive test game state."""
        # Create board with various space types
        spaces = [
            Space(0, 0, Color.GREEN, SpaceKind.START),
            Space(1, 1, Color.YELLOW, SpaceKind.RESOURCE, {"resource": Resource.CHEESE.value, "amount": 2}),
            Space(2, 2, Color.RED, SpaceKind.SHOP_MOLE),
            Space(3, 3, Color.BLUE, SpaceKind.LAUNCH_PAD)
        ]
        
        board = Board(spaces=spaces, start_index=0, launch_index=3)
        
        # Create player with resources
        player1 = Player(
            player_id="p1",
            name="Player 1",
            rats=[
                Rat("r1", "p1", 0),  # At start
                Rat("r2", "p1", 2)   # At mole shop
            ],
            inv=Inventory(capacity=5)
        )
        
        # Give player resources
        player1.inv.add(Resource.TIN_CAN, 5)
        player1.inv.add(Resource.CHEESE, 3)
        
        return GameState(
            board=board,
            players=[player1],
            rocket=Rocket(),
            current_player=0
        )
    
    def test_successful_move_action_processing(self):
        """Test complete processing of a valid move action."""
        state = self.create_test_game_state()
        config = Config.default()
        
        # Move rat to cheese space
        action = create_move_action([("r1", 1)])
        events = state.apply(action, "p1", config)
        
        # Check rat moved
        rat = next(r for r in state.players[0].rats if r.rat_id == "r1")
        assert rat.space_index == 1
        
        # Check resource gained
        player = state.players[0]
        assert player.inv.has(Resource.CHEESE, 5)  # 3 original + 2 from space
        
        # Check events generated
        assert len(events) > 0
        resource_events = [e for e in events if e.type == DomainEventType.RESOURCE_GAINED]
        assert len(resource_events) == 1
        assert resource_events[0].payload["amount"] == 2
        
        # Check history logged
        assert len(state.history) == 1
        history_entry = state.history[0]
        assert history_entry["action"]["type"] == "MOVE"
        assert history_entry["action"]["actor"] == "p1"
        assert len(history_entry["events"]) == len(events)
    
    def test_successful_buy_action_processing(self):
        """Test complete processing of a valid buy action."""
        state = self.create_test_game_state()
        config = Config.default()
        
        original_capacity = state.players[0].inv.capacity
        original_tin_cans = state.players[0].inv.res[Resource.TIN_CAN]
        
        # Buy capacity from mole shop
        action = create_buy_action(SpaceKind.SHOP_MOLE, "capacity", "r2")
        events = state.apply(action, "p1", config)
        
        # Check capacity increased
        player = state.players[0]
        assert player.inv.capacity == original_capacity + 1
        
        # Check resources spent
        assert player.inv.res[Resource.TIN_CAN] == original_tin_cans - 2
        
        # Check events generated
        spent_events = [e for e in events if e.type == DomainEventType.RESOURCE_SPENT]
        inventory_events = [e for e in events if e.type == DomainEventType.INVENTORY_CHANGED]
        
        assert len(spent_events) == 1
        assert len(inventory_events) == 1
        
        # Check history logged
        assert len(state.history) == 1
        history_entry = state.history[0]
        assert history_entry["action"]["type"] == "BUY"
    
    def test_successful_build_action_processing(self):
        """Test complete processing of a valid build action."""
        state = self.create_test_game_state()
        config = Config.default()
        
        original_score = state.players[0].score
        
        # Build rocket nose (costs 3 tin cans + 1 cheese)
        action = create_build_rocket_action(RocketPart.NOSE)
        events = state.apply(action, "p1", config)
        
        # Check part built
        assert state.rocket.is_part_built(RocketPart.NOSE)
        assert state.rocket.get_builder(RocketPart.NOSE) == "p1"
        
        # Check player's built parts updated
        player = state.players[0]
        assert RocketPart.NOSE in player.built_parts
        
        # Check resources spent
        assert player.inv.res[Resource.TIN_CAN] == 2  # 5 - 3 = 2
        assert player.inv.res[Resource.CHEESE] == 2   # 3 - 1 = 2
        
        # Check score increased
        assert player.score > original_score
        
        # Check events generated
        spent_events = [e for e in events if e.type == DomainEventType.RESOURCE_SPENT]
        score_events = [e for e in events if e.type == DomainEventType.SCORE_CHANGED]
        
        assert len(spent_events) == 2  # TIN_CAN and CHEESE
        assert len(score_events) == 1
    
    def test_invalid_action_raises_error(self):
        """Test that invalid actions raise ValueError."""
        state = self.create_test_game_state()
        config = Config.default()
        
        # Try to move a nonexistent rat
        action = create_move_action([("nonexistent", 2)])
        
        with pytest.raises(ValueError) as exc_info:
            state.apply(action, "p1", config)
        
        assert "Invalid action" in str(exc_info.value)
        assert "not found" in str(exc_info.value)
        
        # Check no history entry created for invalid action
        assert len(state.history) == 0
    
    def test_wrong_player_turn_raises_error(self):
        """Test that actions by wrong player raise ValueError."""
        state = self.create_test_game_state()
        config = Config.default()
        
        # Add second player
        player2 = Player(
            player_id="p2",
            name="Player 2",
            rats=[Rat("r3", "p2", 0)],
            inv=Inventory()
        )
        state.players.append(player2)
        
        # Try to act as player 2 when it's player 1's turn
        action = create_move_action([("r3", 1)])
        
        with pytest.raises(ValueError) as exc_info:
            state.apply(action, "p2", config)
        
        assert "It's not p2's turn" in str(exc_info.value)
    
    def test_game_over_prevents_actions(self):
        """Test that actions are prevented when game is over."""
        state = self.create_test_game_state()
        state.game_over = True
        config = Config.default()
        
        action = create_move_action([("r1", 1)])
        
        with pytest.raises(ValueError) as exc_info:
            state.apply(action, "p1", config)
        
        assert "Game is already over" in str(exc_info.value)
    
    def test_invariant_checking_after_action(self):
        """Test that invariants are checked after each action."""
        state = self.create_test_game_state()
        config = Config.default()
        
        # Manually break an invariant (this shouldn't happen in normal gameplay)
        # We'll test by creating a scenario where inventory exceeds capacity
        player = state.players[0]
        player.inv.capacity = 2  # Reduce capacity below current resources
        
        action = create_move_action([("r1", 1)])
        
        # This should raise an invariant violation
        with pytest.raises(ValueError) as exc_info:
            state.apply(action, "p1", config)
        
        assert "inventory exceeds capacity" in str(exc_info.value)
    
    def test_end_turn_advances_player(self):
        """Test that end turn action advances to next player."""
        state = self.create_test_game_state()
        config = Config.default()
        
        # Add second player
        player2 = Player(
            player_id="p2",
            name="Player 2",
            rats=[Rat("r3", "p2", 0)],
            inv=Inventory()
        )
        state.players.append(player2)
        
        assert state.current_player == 0  # Player 1's turn
        
        # End turn
        action = create_end_turn_action()
        events = state.apply(action, "p1", config)
        
        # Check player advanced
        assert state.current_player == 1  # Now player 2's turn
        
        # Check events
        turn_events = [e for e in events if e.type == DomainEventType.TURN_ENDED]
        assert len(turn_events) == 1
        assert turn_events[0].actor == "p1"
    
    def test_multiple_actions_history_accumulation(self):
        """Test that multiple actions accumulate in history."""
        state = self.create_test_game_state()
        config = Config.default()
        
        # Perform multiple actions
        action1 = create_move_action([("r1", 1)])
        events1 = state.apply(action1, "p1", config)
        
        action2 = create_buy_action(SpaceKind.SHOP_MOLE, "capacity", "r2")
        events2 = state.apply(action2, "p1", config)
        
        action3 = create_end_turn_action()
        events3 = state.apply(action3, "p1", config)
        
        # Check history has all actions
        assert len(state.history) == 3
        
        assert state.history[0]["action"]["type"] == "MOVE"
        assert state.history[1]["action"]["type"] == "BUY"
        assert state.history[2]["action"]["type"] == "END_TURN"
        
        # Check each history entry has events
        assert len(state.history[0]["events"]) == len(events1)
        assert len(state.history[1]["events"]) == len(events2)
        assert len(state.history[2]["events"]) == len(events3)
    
    def test_derived_data_in_history(self):
        """Test that derived data from validation is stored in history."""
        state = self.create_test_game_state()
        config = Config.default()
        
        # Move action should have derived data about landing positions
        action = create_move_action([("r1", 1)])
        events = state.apply(action, "p1", config)
        
        # Check derived data in history
        history_entry = state.history[0]
        assert "derived_data" in history_entry
        
        derived = history_entry["derived_data"]
        assert "landing_positions" in derived
        assert "landing_color" in derived
        assert derived["landing_positions"] == [("r1", 1)]
    
    def test_rocket_boarding_spawns_new_rat(self):
        """Test that boarding rocket spawns new rat when possible."""
        state = self.create_test_game_state()
        config = Config.default()
        
        original_rat_count = len(state.players[0].rats)
        
        # Move rat to launch pad
        action = create_move_action([("r1", 3)])
        events = state.apply(action, "p1", config)
        
        # Check rat boarded
        rat = next(r for r in state.players[0].rats if r.rat_id == "r1")
        assert rat.on_rocket is True
        
        # Check new rat spawned
        player = state.players[0]
        assert len(player.rats) == original_rat_count + 1
        
        # Check new rat is at start
        new_rats = [r for r in player.rats if r.rat_id != "r1" and r.rat_id != "r2"]
        assert len(new_rats) == 1
        assert new_rats[0].space_index == 0
        assert new_rats[0].on_rocket is False
        
        # Check events
        rocket_events = [e for e in events if e.type == DomainEventType.ON_ROCKET]
        new_rat_events = [e for e in events if e.type == DomainEventType.NEW_RAT_GAINED]
        
        assert len(rocket_events) == 1
        assert len(new_rat_events) == 1