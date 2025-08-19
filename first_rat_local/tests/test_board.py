"""
Unit tests for Board class.

Tests board navigation, space management, and rat positioning.
"""

import pytest
from first_rat_local.core.models import Board, Space, Rat, Player, Inventory
from first_rat_local.core.enums import Color, SpaceKind


class TestBoard:
    """Test cases for Board navigation and space management."""
    
    def create_test_board(self) -> Board:
        """Create a simple test board with 10 spaces."""
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
        
        return Board(spaces=spaces, start_index=0, launch_index=9)
    
    def test_get_space_valid_index(self):
        """Test getting a space with valid index."""
        board = self.create_test_board()
        space = board.get_space(5)
        assert space.index == 5
        assert space.space_id == 5
    
    def test_get_space_invalid_index(self):
        """Test getting a space with invalid index raises error."""
        board = self.create_test_board()
        with pytest.raises(IndexError):
            board.get_space(15)
        with pytest.raises(IndexError):
            board.get_space(-1)
    
    def test_is_within_bounds(self):
        """Test boundary checking."""
        board = self.create_test_board()
        assert board.is_within_bounds(0) is True
        assert board.is_within_bounds(9) is True
        assert board.is_within_bounds(5) is True
        assert board.is_within_bounds(10) is False
        assert board.is_within_bounds(-1) is False
    
    def test_next_index_normal_movement(self):
        """Test normal movement without shortcuts."""
        board = self.create_test_board()
        assert board.next_index(0, 3) == 3
        assert board.next_index(5, 2) == 7
        assert board.next_index(3, 0) == 3
    
    def test_next_index_boundary_clamping(self):
        """Test movement is clamped to board boundaries."""
        board = self.create_test_board()
        assert board.next_index(8, 5) == 9  # Should clamp to last space
        assert board.next_index(9, 1) == 9  # Already at end
    
    def test_next_index_with_shortcuts(self):
        """Test movement with shortcuts."""
        board = self.create_test_board()
        board.shortcuts = {6: 8}  # Shortcut from index 6 to 8
        
        assert board.next_index(3, 3) == 8  # 3 + 3 = 6, shortcut to 8
        assert board.next_index(5, 1) == 6  # Normal movement, no shortcut
    
    def test_is_occupied_empty_space(self):
        """Test checking occupation of empty space."""
        board = self.create_test_board()
        rats = []
        assert board.is_occupied(5, rats) is False
    
    def test_is_occupied_with_rats(self):
        """Test checking occupation with rats present."""
        board = self.create_test_board()
        rat1 = Rat(rat_id="rat1", owner_id="player1", space_index=5)
        rat2 = Rat(rat_id="rat2", owner_id="player1", space_index=7)
        rats = [rat1, rat2]
        
        assert board.is_occupied(5, rats) is True
        assert board.is_occupied(7, rats) is True
        assert board.is_occupied(6, rats) is False
    
    def test_is_occupied_ignores_rocket_rats(self):
        """Test that rats on rocket don't count as occupying spaces."""
        board = self.create_test_board()
        rat_on_rocket = Rat(rat_id="rat1", owner_id="player1", space_index=5, on_rocket=True)
        rats = [rat_on_rocket]
        
        assert board.is_occupied(5, rats) is False
    
    def test_is_occupied_invalid_index(self):
        """Test occupation check with invalid index."""
        board = self.create_test_board()
        rat = Rat(rat_id="rat1", owner_id="player1", space_index=5)
        rats = [rat]
        
        assert board.is_occupied(15, rats) is False
        assert board.is_occupied(-1, rats) is False
    
    def test_get_rats_at_space(self):
        """Test getting all rats at a specific space."""
        board = self.create_test_board()
        rat1 = Rat(rat_id="rat1", owner_id="player1", space_index=5)
        rat2 = Rat(rat_id="rat2", owner_id="player2", space_index=5)
        rat3 = Rat(rat_id="rat3", owner_id="player1", space_index=7)
        rat4 = Rat(rat_id="rat4", owner_id="player2", space_index=5, on_rocket=True)
        rats = [rat1, rat2, rat3, rat4]
        
        rats_at_5 = board.get_rats_at_space(5, rats)
        assert len(rats_at_5) == 2  # rat4 on rocket shouldn't count
        assert rat1 in rats_at_5
        assert rat2 in rats_at_5
        assert rat4 not in rats_at_5
        
        rats_at_7 = board.get_rats_at_space(7, rats)
        assert len(rats_at_7) == 1
        assert rat3 in rats_at_7
    
    def test_get_all_rats_on_board(self):
        """Test getting all rats from all players that are on the board."""
        board = self.create_test_board()
        
        # Create players with rats
        player1 = Player(
            player_id="p1",
            name="Player 1",
            rats=[
                Rat(rat_id="r1", owner_id="p1", space_index=3),
                Rat(rat_id="r2", owner_id="p1", space_index=5, on_rocket=True)
            ],
            inv=Inventory()
        )
        
        player2 = Player(
            player_id="p2",
            name="Player 2",
            rats=[
                Rat(rat_id="r3", owner_id="p2", space_index=7),
                Rat(rat_id="r4", owner_id="p2", space_index=2)
            ],
            inv=Inventory()
        )
        
        all_players = [player1, player2]
        board_rats = board.get_all_rats_on_board(all_players)
        
        assert len(board_rats) == 3  # r2 is on rocket, shouldn't count
        rat_ids = [rat.rat_id for rat in board_rats]
        assert "r1" in rat_ids
        assert "r3" in rat_ids
        assert "r4" in rat_ids
        assert "r2" not in rat_ids