"""
Unit tests for scoring and end game system.

Tests final scoring calculations, end game detection, and winner determination.
"""

import pytest
from first_rat_local.core.scoring import (
    check_endgame, calculate_final_scores, determine_winners, finalize_game,
    get_scoring_summary, check_and_trigger_endgame, get_current_standings
)
from first_rat_local.core.models import GameState, Board, Space, Player, Rat, Inventory, Rocket
from first_rat_local.core.config import Config
from first_rat_local.core.enums import Color, SpaceKind, Resource, RocketPart, DomainEventType


class TestEndGameDetection:
    """Test cases for end game detection."""
    
    def create_test_game_state(self) -> GameState:
        """Create a test game state."""
        board = Board([Space(0, 0, Color.GREEN, SpaceKind.START)], 0, 0)
        
        player1 = Player(
            player_id="p1",
            name="Player 1",
            rats=[
                Rat("r1", "p1", 0),
                Rat("r2", "p1", 0),
                Rat("r3", "p1", 0, on_rocket=True),  # 1 on rocket
            ],
            inv=Inventory()
        )
        
        player2 = Player(
            player_id="p2",
            name="Player 2",
            rats=[
                Rat("r4", "p2", 0),
                Rat("r5", "p2", 0, on_rocket=True),  # 1 on rocket
                Rat("r6", "p2", 0, on_rocket=True),  # 2 on rocket
            ],
            inv=Inventory()
        )
        
        return GameState(
            board=board,
            players=[player1, player2],
            rocket=Rocket()
        )
    
    def test_fourth_rat_trigger_not_met(self):
        """Test that game doesn't end when no player has 4 rats on rocket."""
        state = self.create_test_game_state()
        config = Config.default()
        
        # Player 1 has 1 rat on rocket, Player 2 has 2 rats on rocket
        assert check_endgame(state, config) is False
    
    def test_fourth_rat_trigger_met(self):
        """Test that game ends when a player has 4 rats on rocket."""
        state = self.create_test_game_state()
        config = Config.default()
        
        # Add more rats on rocket for player 2
        player2 = state.players[1]
        player2.rats.extend([
            Rat("r7", "p2", 0, on_rocket=True),  # 3rd on rocket
            Rat("r8", "p2", 0, on_rocket=True),  # 4th on rocket
        ])
        
        assert check_endgame(state, config) is True
    
    def test_eighth_scoring_marker_trigger_not_met(self):
        """Test that game doesn't end with fewer than 8 scoring markers."""
        state = self.create_test_game_state()
        config = Config.default()
        
        # Add some rocket parts (scoring markers)
        state.players[0].built_parts.add(RocketPart.NOSE)
        state.players[0].built_parts.add(RocketPart.TANK)
        state.players[1].built_parts.add(RocketPart.ENGINE)
        # Total: 3 parts < 8
        
        assert check_endgame(state, config) is False
    
    def test_eighth_scoring_marker_trigger_met(self):
        """Test that game ends with 8 or more scoring markers."""
        state = self.create_test_game_state()
        config = Config.default()
        
        # Add 8 rocket parts across players
        state.players[0].built_parts.update([
            RocketPart.NOSE, RocketPart.TANK, RocketPart.ENGINE, RocketPart.FIN_A
        ])
        state.players[1].built_parts.update([
            RocketPart.FIN_B, RocketPart.NOSE, RocketPart.TANK, RocketPart.ENGINE
        ])
        # Total: 8 parts (some duplicates, but each player's parts count)
        
        assert check_endgame(state, config) is True
    
    def test_endgame_trigger_disabled(self):
        """Test that disabled triggers don't end the game."""
        state = self.create_test_game_state()
        config = Config.default()
        
        # Disable fourth rat trigger
        config.endgame_triggers["fourth_rat_on_rocket"] = False
        
        # Add 4 rats on rocket for player 2
        player2 = state.players[1]
        player2.rats.extend([
            Rat("r7", "p2", 0, on_rocket=True),
            Rat("r8", "p2", 0, on_rocket=True),
        ])
        
        # Should not trigger end game
        assert check_endgame(state, config) is False


class TestScoring:
    """Test cases for final scoring calculations."""
    
    def create_test_game_state_for_scoring(self) -> GameState:
        """Create a test game state with various scoring elements."""
        board = Board([Space(0, 0, Color.GREEN, SpaceKind.START)], 0, 0)
        
        player1 = Player(
            player_id="p1",
            name="Player 1",
            rats=[
                Rat("r1", "p1", 0, on_rocket=True),
                Rat("r2", "p1", 0, on_rocket=True),
                Rat("r3", "p1", 0),
            ],
            inv=Inventory(),
            score=15  # Points earned during game
        )
        
        # Add scoring elements
        player1.built_parts.update([RocketPart.NOSE, RocketPart.ENGINE])
        player1.inv.bottlecaps = 3
        player1.tracks["lightbulb"] = 4
        player1.inv.add(Resource.CHEESE, 2)
        player1.inv.add(Resource.TIN_CAN, 3)  # Total 5 resources
        
        player2 = Player(
            player_id="p2",
            name="Player 2",
            rats=[
                Rat("r4", "p2", 0, on_rocket=True),
                Rat("r5", "p2", 0),
            ],
            inv=Inventory(),
            score=12
        )
        
        player2.built_parts.add(RocketPart.TANK)
        player2.inv.bottlecaps = 1
        player2.tracks["lightbulb"] = 2
        player2.inv.add(Resource.SODA, 1)  # 1 resource
        
        return GameState(
            board=board,
            players=[player1, player2],
            rocket=Rocket()
        )
    
    def test_calculate_final_scores(self):
        """Test final score calculation with all scoring elements."""
        state = self.create_test_game_state_for_scoring()
        config = Config.default()
        
        # Enable remaining resources scoring for this test
        config.scoring_rules["remaining_resources"] = True
        
        breakdown = calculate_final_scores(state, config)
        
        # Check player 1 scoring
        p1_score = breakdown["p1"]
        assert p1_score["player_name"] == "Player 1"
        assert p1_score["current_score"] == 15
        assert p1_score["rocket_parts_score"] == 9  # NOSE(4) + ENGINE(5)
        assert p1_score["bottlecaps_score"] == 3   # 3 bottlecaps * 1
        assert p1_score["lightbulb_track_score"] == 8  # 4 levels * 2
        assert p1_score["remaining_resources_score"] == 2  # 5 resources // 2
        assert p1_score["rats_on_rocket_count"] == 2
        
        expected_p1_total = 15 + 9 + 3 + 8 + 2  # 37
        assert p1_score["total_score"] == expected_p1_total
        
        # Check player 2 scoring
        p2_score = breakdown["p2"]
        assert p2_score["current_score"] == 12
        assert p2_score["rocket_parts_score"] == 3  # TANK(3)
        assert p2_score["bottlecaps_score"] == 1
        assert p2_score["lightbulb_track_score"] == 4  # 2 levels * 2
        assert p2_score["remaining_resources_score"] == 0  # 1 resource // 2 = 0
        assert p2_score["rats_on_rocket_count"] == 1
        
        expected_p2_total = 12 + 3 + 1 + 4 + 0  # 20
        assert p2_score["total_score"] == expected_p2_total
    
    def test_calculate_final_scores_disabled_elements(self):
        """Test final score calculation with some elements disabled."""
        state = self.create_test_game_state_for_scoring()
        config = Config.default()
        
        # Disable some scoring elements
        config.scoring_rules["rocket_parts"] = False
        config.scoring_rules["bottlecaps"] = 0  # No points per bottlecap
        config.scoring_rules["lightbulb_track"] = False
        config.scoring_rules["remaining_resources"] = False
        
        breakdown = calculate_final_scores(state, config)
        
        # Player 1 should only have current score
        p1_score = breakdown["p1"]
        assert p1_score["rocket_parts_score"] == 0
        assert p1_score["bottlecaps_score"] == 0
        assert p1_score["lightbulb_track_score"] == 0
        assert p1_score["remaining_resources_score"] == 0
        assert p1_score["total_score"] == 15  # Only current score
    
    def test_determine_winners_clear_winner(self):
        """Test winner determination with clear winner."""
        scoring_breakdown = {
            "p1": {"total_score": 30, "rats_on_rocket_count": 2},
            "p2": {"total_score": 25, "rats_on_rocket_count": 1},
            "p3": {"total_score": 20, "rats_on_rocket_count": 3}
        }
        
        winners = determine_winners(scoring_breakdown)
        assert winners == ["p1"]
    
    def test_determine_winners_tie_broken_by_rats(self):
        """Test winner determination with tie broken by rats on rocket."""
        scoring_breakdown = {
            "p1": {"total_score": 25, "rats_on_rocket_count": 2},
            "p2": {"total_score": 25, "rats_on_rocket_count": 3},
            "p3": {"total_score": 20, "rats_on_rocket_count": 1}
        }
        
        winners = determine_winners(scoring_breakdown)
        assert winners == ["p2"]  # Same score but more rats on rocket
    
    def test_determine_winners_complete_tie(self):
        """Test winner determination with complete tie."""
        scoring_breakdown = {
            "p1": {"total_score": 25, "rats_on_rocket_count": 2},
            "p2": {"total_score": 25, "rats_on_rocket_count": 2},
            "p3": {"total_score": 20, "rats_on_rocket_count": 3}
        }
        
        winners = determine_winners(scoring_breakdown)
        assert set(winners) == {"p1", "p2"}  # Both tied for first


class TestGameFinalization:
    """Test cases for game finalization."""
    
    def create_test_game_state(self) -> GameState:
        """Create a test game state for finalization."""
        board = Board([Space(0, 0, Color.GREEN, SpaceKind.START)], 0, 0)
        
        player1 = Player(
            player_id="p1",
            name="Player 1",
            rats=[Rat("r1", "p1", 0, on_rocket=True)],
            inv=Inventory(),
            score=20
        )
        
        player2 = Player(
            player_id="p2",
            name="Player 2",
            rats=[Rat("r2", "p2", 0)],
            inv=Inventory(),
            score=15
        )
        
        return GameState(
            board=board,
            players=[player1, player2],
            rocket=Rocket()
        )
    
    def test_finalize_game(self):
        """Test complete game finalization."""
        state = self.create_test_game_state()
        config = Config.default()
        
        results = finalize_game(state, config, "fourth_rat_on_rocket")
        
        # Check game state updated
        assert state.game_over is True
        assert state.winner_ids is not None
        
        # Check results structure
        assert results["game_over"] is True
        assert results["trigger"] == "fourth_rat_on_rocket"
        assert "winner_ids" in results
        assert "scoring_breakdown" in results
        assert "final_scores" in results
        assert "game_ended_event" in results
        
        # Check history updated
        assert len(state.history) == 1
        history_entry = state.history[0]
        assert history_entry["action"]["type"] == "GAME_END"
        assert len(history_entry["events"]) == 1
        assert history_entry["events"][0]["type"] == "GAME_ENDED"
    
    def test_check_and_trigger_endgame_fourth_rat(self):
        """Test automatic endgame triggering with fourth rat."""
        state = self.create_test_game_state()
        config = Config.default()
        
        # Add 3 more rats on rocket for player 1 (total 4)
        player1 = state.players[0]
        player1.rats.extend([
            Rat("r3", "p1", 0, on_rocket=True),
            Rat("r4", "p1", 0, on_rocket=True),
            Rat("r5", "p1", 0, on_rocket=True),
        ])
        
        results = check_and_trigger_endgame(state, config)
        
        assert results is not None
        assert results["trigger"] == "fourth_rat_on_rocket"
        assert state.game_over is True
    
    def test_check_and_trigger_endgame_no_trigger(self):
        """Test that endgame doesn't trigger when conditions not met."""
        state = self.create_test_game_state()
        config = Config.default()
        
        results = check_and_trigger_endgame(state, config)
        
        assert results is None
        assert state.game_over is False
    
    def test_get_scoring_summary(self):
        """Test scoring summary generation."""
        scoring_breakdown = {
            "p1": {
                "player_name": "Player 1",
                "total_score": 30,
                "current_score": 15,
                "rocket_parts_score": 8,
                "bottlecaps_score": 3,
                "lightbulb_track_score": 4,
                "remaining_resources_score": 0,
                "rats_on_rocket_count": 2
            },
            "p2": {
                "player_name": "Player 2",
                "total_score": 25,
                "current_score": 12,
                "rocket_parts_score": 5,
                "bottlecaps_score": 2,
                "lightbulb_track_score": 6,
                "remaining_resources_score": 0,
                "rats_on_rocket_count": 1
            }
        }
        
        summary = get_scoring_summary(scoring_breakdown)
        
        assert "最终计分" in summary
        assert "Player 1" in summary
        assert "Player 2" in summary
        assert "第1名" in summary
        assert "第2名" in summary
        assert "总分: 30" in summary
        assert "总分: 25" in summary
    
    def test_get_current_standings(self):
        """Test current standings generation."""
        state = self.create_test_game_state()
        
        # Add more scoring elements
        state.players[0].score = 25
        state.players[1].score = 30  # Player 2 has higher current score
        
        standings = get_current_standings(state)
        
        assert len(standings) == 2
        
        # Should be sorted by score (descending)
        assert standings[0][0] == "p2"  # Player 2 first (higher score)
        assert standings[0][2] == 30    # Score
        assert standings[1][0] == "p1"  # Player 1 second
        assert standings[1][2] == 25    # Score