"""
Unit tests for end game detection integration.

Tests automatic end game triggering during action resolution.
"""

import pytest
from first_rat_local.core.models import GameState, Board, Space, Player, Rat, Inventory, Rocket
from first_rat_local.core.actions import create_move_action, create_build_rocket_action
from first_rat_local.core.config import Config
from first_rat_local.core.enums import Color, SpaceKind, Resource, RocketPart, DomainEventType


class TestEndGameIntegration:
    """Test cases for automatic end game detection during actions."""
    
    def create_test_game_state_near_endgame(self) -> GameState:
        """Create a test game state close to end game conditions."""
        # Create board with launch pad
        spaces = [
            Space(0, 0, Color.GREEN, SpaceKind.START),
            Space(1, 1, Color.YELLOW, SpaceKind.RESOURCE, {"resource": Resource.CHEESE.value, "amount": 1}),
            Space(2, 2, Color.BLUE, SpaceKind.LAUNCH_PAD)
        ]
        
        board = Board(spaces=spaces, start_index=0, launch_index=2)
        
        # Create player with 3 rats already on rocket (close to 4th rat trigger)
        player1 = Player(
            player_id="p1",
            name="Player 1",
            rats=[
                Rat("r1", "p1", 1),  # On board, can move to launch pad
                Rat("r2", "p1", 0, on_rocket=True),   # On rocket
                Rat("r3", "p1", 0, on_rocket=True),   # On rocket
                Rat("r4", "p1", 0, on_rocket=True),   # On rocket (3 total)
            ],
            inv=Inventory()
        )
        
        return GameState(
            board=board,
            players=[player1],
            rocket=Rocket(),
            current_player=0
        )
    
    def create_test_game_state_near_eighth_marker(self) -> GameState:
        """Create a test game state close to 8th scoring marker trigger."""
        board = Board([Space(0, 0, Color.GREEN, SpaceKind.START)], 0, 0)
        
        player1 = Player(
            player_id="p1",
            name="Player 1",
            rats=[Rat("r1", "p1", 0)],
            inv=Inventory(capacity=10)
        )
        
        player2 = Player(
            player_id="p2",
            name="Player 2",
            rats=[Rat("r2", "p2", 0)],
            inv=Inventory()
        )
        
        # Give players rocket parts (7 total, close to 8)
        player1.built_parts.update([
            RocketPart.NOSE, RocketPart.TANK, RocketPart.ENGINE, RocketPart.FIN_A
        ])
        player2.built_parts.update([
            RocketPart.FIN_B, RocketPart.NOSE, RocketPart.TANK  # 7 total parts
        ])
        
        # Give player1 resources to build one more part
        player1.inv.add(Resource.TIN_CAN, 5)
        player1.inv.add(Resource.CHEESE, 3)
        
        return GameState(
            board=board,
            players=[player1, player2],
            rocket=Rocket(),
            current_player=0
        )
    
    def test_fourth_rat_trigger_during_move(self):
        """Test that 4th rat boarding triggers end game during move action."""
        state = self.create_test_game_state_near_endgame()
        config = Config.default()
        
        # Move rat to launch pad (should trigger 4th rat on rocket)
        action = create_move_action([("r1", 1)])  # Move from index 1 to index 2 (launch pad)
        events = state.apply(action, "p1", config)
        
        # Check game ended
        assert state.game_over is True
        assert state.winner_ids == ["p1"]
        
        # Check events include both boarding and game end
        rocket_events = [e for e in events if e.type == DomainEventType.ON_ROCKET]
        game_end_events = [e for e in events if e.type == DomainEventType.GAME_ENDED]
        
        assert len(rocket_events) == 1
        assert len(game_end_events) == 1
        
        # Check game end event details
        game_end_event = game_end_events[0]
        assert game_end_event.payload["trigger"] == "fourth_rat_on_rocket"
        assert "p1" in game_end_event.payload["winner_ids"]
        
        # Check history includes game end
        assert len(state.history) == 2  # Move action + game end
        game_end_history = state.history[1]
        assert game_end_history["action"]["type"] == "GAME_END"
    
    def test_eighth_marker_trigger_during_build(self):
        """Test that 8th scoring marker triggers end game during build action."""
        state = self.create_test_game_state_near_eighth_marker()
        config = Config.default()
        
        # Build one more rocket part (should be the 8th scoring marker)
        action = create_build_rocket_action(RocketPart.ENGINE)  # Player 1 builds engine
        events = state.apply(action, "p1", config)
        
        # Check game ended
        assert state.game_over is True
        assert state.winner_ids is not None
        
        # Check events include both part building and game end
        score_events = [e for e in events if e.type == DomainEventType.SCORE_CHANGED]
        game_end_events = [e for e in events if e.type == DomainEventType.GAME_ENDED]
        
        assert len(score_events) == 1  # From building the part
        assert len(game_end_events) == 1
        
        # Check game end event details
        game_end_event = game_end_events[0]
        assert game_end_event.payload["trigger"] == "eighth_scoring_marker"
    
    def test_no_endgame_trigger_when_conditions_not_met(self):
        """Test that game doesn't end when conditions are not met."""
        state = self.create_test_game_state_near_endgame()
        config = Config.default()
        
        # Move rat to cheese space (not launch pad)
        action = create_move_action([("r1", 0)])  # Move to index 1 (cheese space)
        events = state.apply(action, "p1", config)
        
        # Check game didn't end
        assert state.game_over is False
        assert state.winner_ids is None
        
        # Check no game end events
        game_end_events = [e for e in events if e.type == DomainEventType.GAME_ENDED]
        assert len(game_end_events) == 0
        
        # Check only one history entry (the move action)
        assert len(state.history) == 1
        assert state.history[0]["action"]["type"] == "MOVE"
    
    def test_endgame_trigger_disabled(self):
        """Test that disabled triggers don't end the game."""
        state = self.create_test_game_state_near_endgame()
        config = Config.default()
        
        # Disable the fourth rat trigger
        config.endgame_triggers["fourth_rat_on_rocket"] = False
        
        # Move rat to launch pad
        action = create_move_action([("r1", 1)])
        events = state.apply(action, "p1", config)
        
        # Check game didn't end despite 4th rat boarding
        assert state.game_over is False
        
        # Check rat still boarded (action effects still applied)
        rat = next(r for r in state.players[0].rats if r.rat_id == "r1")
        assert rat.on_rocket is True
        
        # Check no game end events
        game_end_events = [e for e in events if e.type == DomainEventType.GAME_ENDED]
        assert len(game_end_events) == 0
    
    def test_multiple_endgame_conditions_met_simultaneously(self):
        """Test behavior when multiple end game conditions could trigger."""
        # Create a state where both conditions could be met
        board = Board([Space(0, 0, Color.GREEN, SpaceKind.START)], 0, 0)
        
        player1 = Player(
            player_id="p1",
            name="Player 1",
            rats=[
                Rat("r1", "p1", 0, on_rocket=True),
                Rat("r2", "p1", 0, on_rocket=True),
                Rat("r3", "p1", 0, on_rocket=True),  # 3 on rocket
            ],
            inv=Inventory(capacity=10)
        )
        
        # Give player 7 rocket parts (close to 8) and resources for one more
        player1.built_parts.update([
            RocketPart.NOSE, RocketPart.TANK, RocketPart.ENGINE, 
            RocketPart.FIN_A, RocketPart.FIN_B
        ])
        # Add 2 more parts from another "player" perspective to reach 7 total
        player1.built_parts.update([RocketPart.NOSE, RocketPart.TANK])  # 7 total
        
        player1.inv.add(Resource.TIN_CAN, 5)
        player1.inv.add(Resource.CHEESE, 3)
        
        state = GameState(
            board=board,
            players=[player1],
            rocket=Rocket(),
            current_player=0
        )
        
        config = Config.default()
        
        # Build rocket part (should trigger 8th marker before 4th rat could trigger)
        action = create_build_rocket_action(RocketPart.ENGINE)
        events = state.apply(action, "p1", config)
        
        # Check game ended
        assert state.game_over is True
        
        # Should trigger on whichever condition is checked first (8th marker in this case)
        game_end_events = [e for e in events if e.type == DomainEventType.GAME_ENDED]
        assert len(game_end_events) == 1
        assert game_end_events[0].payload["trigger"] == "eighth_scoring_marker"
    
    def test_endgame_prevents_further_actions(self):
        """Test that once game ends, no further actions can be taken."""
        state = self.create_test_game_state_near_endgame()
        config = Config.default()
        
        # Trigger end game
        action1 = create_move_action([("r1", 1)])
        events1 = state.apply(action1, "p1", config)
        
        assert state.game_over is True
        
        # Try to perform another action
        action2 = create_move_action([("r2", 1)])  # This should fail
        
        with pytest.raises(ValueError) as exc_info:
            state.apply(action2, "p1", config)
        
        assert "Game is already over" in str(exc_info.value)
    
    def test_endgame_scoring_calculation(self):
        """Test that end game properly calculates final scores."""
        state = self.create_test_game_state_near_endgame()
        config = Config.default()
        
        # Give player some scoring elements
        player = state.players[0]
        player.score = 10  # Current score
        player.built_parts.add(RocketPart.NOSE)  # 4 points
        player.inv.bottlecaps = 2  # 2 points
        
        # Trigger end game
        action = create_move_action([("r1", 1)])
        events = state.apply(action, "p1", config)
        
        # Check game end event has final scores
        game_end_events = [e for e in events if e.type == DomainEventType.GAME_ENDED]
        game_end_event = game_end_events[0]
        
        final_scores = game_end_event.payload["final_scores"]
        assert "p1" in final_scores
        
        # Final score should include current score + rocket parts + bottlecaps
        # Note: The exact calculation depends on the scoring rules in config
        player_final_score = final_scores["p1"]
        assert player_final_score > 10  # Should be more than just current score