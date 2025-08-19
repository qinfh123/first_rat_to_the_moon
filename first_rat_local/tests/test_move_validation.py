"""
Unit tests for move action validation.

Tests movement rule validation including color consistency and occupation checks.
"""

import pytest
from first_rat_local.core.rules import ActionValidator
from first_rat_local.core.models import GameState, Board, Space, Player, Rat, Inventory, Rocket
from first_rat_local.core.actions import create_move_action
from first_rat_local.core.config import Config
from first_rat_local.core.enums import Color, SpaceKind


class TestMoveValidation:
    """Test cases for move action validation."""
    
    def create_test_game_state(self) -> GameState:
        """Create a test game state with a simple board."""
        # Create a simple 10-space board
        spaces = []
        colors = [Color.GREEN, Color.YELLOW, Color.RED, Color.BLUE]
        
        for i in range(10):
            space = Space(
                space_id=i,
                index=i,
                color=colors[i % 4],
                kind=SpaceKind.START if i == 0 else SpaceKind.LAUNCH_PAD if i == 9 else SpaceKind.RESOURCE,
                payload={}
            )
            spaces.append(space)
        
        board = Board(spaces=spaces, start_index=0, launch_index=9)
        
        # Create players
        player1 = Player(
            player_id="p1",
            name="Player 1",
            rats=[
                Rat("r1", "p1", 0),  # At start
                Rat("r2", "p1", 2),  # At index 2
                Rat("r3", "p1", 4)   # At index 4
            ],
            inv=Inventory()
        )
        
        player2 = Player(
            player_id="p2",
            name="Player 2",
            rats=[
                Rat("r4", "p2", 1),  # At index 1
                Rat("r5", "p2", 3)   # At index 3
            ],
            inv=Inventory()
        )
        
        return GameState(
            board=board,
            players=[player1, player2],
            rocket=Rocket(),
            current_player=0  # Player 1's turn
        )
    
    def test_valid_single_rat_move(self):
        """Test valid single rat movement."""
        state = self.create_test_game_state()
        config = Config.default()
        validator = ActionValidator(config)
        
        # Move rat r1 from index 0 to index 3 (3 steps)
        action = create_move_action([("r1", 3)])
        is_valid, error, derived = validator.validate(state, action, "p1")
        
        assert is_valid is True
        assert error is None
        assert len(derived["landing_positions"]) == 1
        assert derived["landing_positions"][0] == ("r1", 3)
        assert derived["landing_color"] == Color.BLUE  # Index 3 is blue
    
    def test_valid_multiple_rat_move(self):
        """Test valid multiple rat movement."""
        state = self.create_test_game_state()
        config = Config.default()
        validator = ActionValidator(config)
        
        # Move r1 2 steps (0->2) and r2 2 steps (2->4), both land on red spaces
        action = create_move_action([("r1", 2), ("r2", 2)])
        is_valid, error, derived = validator.validate(state, action, "p1")
        
        assert is_valid is True
        assert error is None
        assert len(derived["landing_positions"]) == 2
        assert ("r1", 2) in derived["landing_positions"]
        assert ("r2", 4) in derived["landing_positions"]
        assert derived["landing_color"] == Color.RED  # Both land on red
    
    def test_invalid_single_rat_too_many_steps(self):
        """Test invalid single rat movement with too many steps."""
        state = self.create_test_game_state()
        config = Config.default()
        validator = ActionValidator(config)
        
        # Try to move rat 6 steps (invalid for single rat)
        action = create_move_action([("r1", 6)])
        is_valid, error, derived = validator.validate(state, action, "p1")
        
        assert is_valid is False
        assert "Single rat must move 1-5 steps" in error
    
    def test_invalid_multiple_rat_too_many_steps(self):
        """Test invalid multiple rat movement with too many steps."""
        state = self.create_test_game_state()
        config = Config.default()
        validator = ActionValidator(config)
        
        # Try to move multiple rats with one having 4 steps (invalid)
        action = create_move_action([("r1", 4), ("r2", 2)])
        is_valid, error, derived = validator.validate(state, action, "p1")
        
        assert is_valid is False
        assert "Multiple rats must each move 1-3 steps" in error
    
    def test_invalid_color_mismatch(self):
        """Test invalid movement with color mismatch."""
        state = self.create_test_game_state()
        config = Config.default()
        validator = ActionValidator(config)
        
        # Move r1 1 step (0->1, yellow) and r2 1 step (2->3, blue) - different colors
        action = create_move_action([("r1", 1), ("r2", 1)])
        is_valid, error, derived = validator.validate(state, action, "p1")
        
        assert is_valid is False
        assert "All rats must land on same color spaces" in error
        assert "YELLOW" in error and "BLUE" in error
    
    def test_invalid_occupation_conflict(self):
        """Test invalid movement with occupation conflict."""
        state = self.create_test_game_state()
        config = Config.default()
        validator = ActionValidator(config)
        
        # Try to move r1 to index 1, which is occupied by r4 (player 2's rat)
        action = create_move_action([("r1", 1)])
        is_valid, error, derived = validator.validate(state, action, "p1")
        
        assert is_valid is False
        assert "Space 1 is occupied by rat r4" in error
    
    def test_invalid_self_occupation_conflict(self):
        """Test invalid movement where multiple rats land on same space."""
        state = self.create_test_game_state()
        config = Config.default()
        validator = ActionValidator(config)
        
        # Try to move both r1 and r3 to the same space (both move to index 5)
        action = create_move_action([("r1", 1), ("r3", 1)])  # r1: 0->1, r3: 4->5, but r1 lands on occupied space
        is_valid, error, derived = validator.validate(state, action, "p1")
        
        # This should fail because r1 tries to land on space 1 which is occupied by r4
        assert is_valid is False
        assert "occupied" in error
    
    def test_invalid_nonexistent_rat(self):
        """Test invalid movement with nonexistent rat."""
        state = self.create_test_game_state()
        config = Config.default()
        validator = ActionValidator(config)
        
        # Try to move a rat that doesn't exist
        action = create_move_action([("nonexistent", 2)])
        is_valid, error, derived = validator.validate(state, action, "p1")
        
        assert is_valid is False
        assert "Rat nonexistent not found or not on board" in error
    
    def test_invalid_wrong_player_rat(self):
        """Test invalid movement with another player's rat."""
        state = self.create_test_game_state()
        config = Config.default()
        validator = ActionValidator(config)
        
        # Try to move player 2's rat while it's player 1's turn
        action = create_move_action([("r4", 2)])
        is_valid, error, derived = validator.validate(state, action, "p1")
        
        assert is_valid is False
        assert "Rat r4 not found or not on board" in error
    
    def test_invalid_wrong_turn(self):
        """Test invalid movement when it's not the player's turn."""
        state = self.create_test_game_state()
        config = Config.default()
        validator = ActionValidator(config)
        
        # Try to move when it's not player 2's turn
        action = create_move_action([("r4", 2)])
        is_valid, error, derived = validator.validate(state, action, "p2")
        
        assert is_valid is False
        assert "It's not p2's turn" in error
    
    def test_invalid_game_over(self):
        """Test invalid movement when game is over."""
        state = self.create_test_game_state()
        state.game_over = True
        config = Config.default()
        validator = ActionValidator(config)
        
        action = create_move_action([("r1", 2)])
        is_valid, error, derived = validator.validate(state, action, "p1")
        
        assert is_valid is False
        assert "Game is already over" in error
    
    def test_board_boundary_clamping(self):
        """Test movement that would go beyond board boundaries."""
        state = self.create_test_game_state()
        config = Config.default()
        validator = ActionValidator(config)
        
        # Move rat from index 8 with 5 steps - should clamp to index 9 (last space)
        state.players[0].rats[0].space_index = 8  # Move r1 to index 8
        action = create_move_action([("r1", 5)])
        is_valid, error, derived = validator.validate(state, action, "p1")
        
        assert is_valid is True
        assert derived["landing_positions"][0] == ("r1", 9)  # Clamped to last space
    
    def test_too_many_rats_moving(self):
        """Test invalid movement with too many rats."""
        state = self.create_test_game_state()
        config = Config.default()
        validator = ActionValidator(config)
        
        # Try to move 5 rats (more than allowed maximum of 4)
        # Add more rats to player 1
        state.players[0].rats.extend([
            Rat("r6", "p1", 5),
            Rat("r7", "p1", 6)
        ])
        
        action = create_move_action([("r1", 1), ("r2", 1), ("r3", 1), ("r6", 1), ("r7", 1)])
        is_valid, error, derived = validator.validate(state, action, "p1")
        
        assert is_valid is False
        assert "Must move 1 rat or 2-4 rats, got 5" in error