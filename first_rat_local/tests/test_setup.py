"""
Unit tests for game setup and initialization system.

Tests board creation, player initialization, and game state setup.
"""

import pytest
from first_rat_local.core.setup import (
    build_standard_board, create_player, new_game, create_test_game,
    create_demo_game, validate_game_setup, get_setup_summary
)
from first_rat_local.core.config import Config
from first_rat_local.core.enums import Color, SpaceKind, Resource


class TestBoardCreation:
    """Test cases for board creation."""
    
    def test_build_standard_board(self):
        """Test building standard board from configuration."""
        config = Config.default()
        board = build_standard_board(config)
        
        # Check board has correct number of spaces
        assert len(board.spaces) == len(config.board_layout)
        
        # Check start and launch indices
        assert board.start_index == config.start_index
        assert board.launch_index == config.launch_index
        
        # Check first space is START
        start_space = board.get_space(config.start_index)
        assert start_space.kind == SpaceKind.START
        
        # Check last space is LAUNCH_PAD
        launch_space = board.get_space(config.launch_index)
        assert launch_space.kind == SpaceKind.LAUNCH_PAD
        
        # Check space indices are sequential
        for i, space in enumerate(board.spaces):
            assert space.index == i
            assert space.space_id == i
    
    def test_board_space_types(self):
        """Test that board contains expected space types."""
        config = Config.default()
        board = build_standard_board(config)
        
        # Count different space types
        space_types = {}
        for space in board.spaces:
            space_types[space.kind] = space_types.get(space.kind, 0) + 1
        
        # Should have at least one of each major type
        assert SpaceKind.START in space_types
        assert SpaceKind.LAUNCH_PAD in space_types
        assert SpaceKind.RESOURCE in space_types
        
        # Should have exactly one start and one launch pad
        assert space_types[SpaceKind.START] == 1
        assert space_types[SpaceKind.LAUNCH_PAD] == 1


class TestPlayerCreation:
    """Test cases for player creation."""
    
    def test_create_player_basic(self):
        """Test basic player creation."""
        config = Config.default()
        player = create_player("p1", "Test Player", config)
        
        assert player.player_id == "p1"
        assert player.name == "Test Player"
        assert player.score == 0
        assert len(player.built_parts) == 0
    
    def test_create_player_rats(self):
        """Test player rat creation."""
        config = Config.default()
        player = create_player("p1", "Test Player", config)
        
        # Check correct number of rats
        assert len(player.rats) == config.starting_rats
        
        # Check each rat setup
        for i, rat in enumerate(player.rats):
            assert rat.owner_id == "p1"
            assert rat.space_index == config.start_index
            assert rat.on_rocket is False
            assert rat.rat_id == f"p1_rat_{i + 1}"
    
    def test_create_player_inventory(self):
        """Test player inventory creation."""
        config = Config.default()
        player = create_player("p1", "Test Player", config)
        
        # Check inventory setup
        assert player.inv.capacity == config.starting_inventory_capacity
        assert player.inv.total_resources() == 0
        assert player.inv.x2_active is False
        assert player.inv.bottlecaps == 0
    
    def test_create_player_tracks(self):
        """Test player track initialization."""
        config = Config.default()
        player = create_player("p1", "Test Player", config)
        
        # Check tracks are empty
        assert len(player.tracks) == 0
        assert player.tracks["lightbulb"] == 0  # Should default to 0


class TestGameCreation:
    """Test cases for complete game creation."""
    
    def test_new_game_basic(self):
        """Test basic new game creation."""
        config = Config.default()
        names = ["Alice", "Bob"]
        game_state = new_game(2, names, config, seed=42)
        
        # Check basic game state
        assert len(game_state.players) == 2
        assert game_state.current_player == 0
        assert game_state.round == 1
        assert game_state.phase == "MAIN"
        assert game_state.rng_seed == 42
        assert game_state.game_over is False
        assert game_state.winner_ids is None
        assert len(game_state.history) == 0
        
        # Check player names
        assert game_state.players[0].name == "Alice"
        assert game_state.players[1].name == "Bob"
        
        # Check player IDs
        assert game_state.players[0].player_id == "player_1"
        assert game_state.players[1].player_id == "player_2"
    
    def test_new_game_board_setup(self):
        """Test that new game has properly set up board."""
        config = Config.default()
        names = ["Alice", "Bob"]
        game_state = new_game(2, names, config)
        
        # Check board is created
        assert game_state.board is not None
        assert len(game_state.board.spaces) > 0
        assert game_state.board.start_index == config.start_index
        assert game_state.board.launch_index == config.launch_index
    
    def test_new_game_rocket_setup(self):
        """Test that new game has properly initialized rocket."""
        config = Config.default()
        names = ["Alice", "Bob"]
        game_state = new_game(2, names, config)
        
        # Check rocket is created and empty
        assert game_state.rocket is not None
        for part, builder in game_state.rocket.parts.items():
            assert builder is None
    
    def test_new_game_invalid_player_count(self):
        """Test that invalid player counts raise errors."""
        config = Config.default()
        
        # Too few players
        with pytest.raises(ValueError) as exc_info:
            new_game(1, ["Alice"], config)
        assert "Number of players must be 2-4" in str(exc_info.value)
        
        # Too many players
        with pytest.raises(ValueError) as exc_info:
            new_game(5, ["A", "B", "C", "D", "E"], config)
        assert "Number of players must be 2-4" in str(exc_info.value)
    
    def test_new_game_mismatched_names(self):
        """Test that mismatched name count raises error."""
        config = Config.default()
        
        # Too few names
        with pytest.raises(ValueError) as exc_info:
            new_game(3, ["Alice", "Bob"], config)
        assert "Expected 3 names, got 2" in str(exc_info.value)
        
        # Too many names
        with pytest.raises(ValueError) as exc_info:
            new_game(2, ["Alice", "Bob", "Charlie"], config)
        assert "Expected 2 names, got 3" in str(exc_info.value)
    
    def test_new_game_duplicate_names(self):
        """Test that duplicate names raise error."""
        config = Config.default()
        
        with pytest.raises(ValueError) as exc_info:
            new_game(2, ["Alice", "Alice"], config)
        assert "Player names must be unique" in str(exc_info.value)
    
    def test_new_game_four_players(self):
        """Test creating game with maximum players."""
        config = Config.default()
        names = ["Alice", "Bob", "Charlie", "Diana"]
        game_state = new_game(4, names, config)
        
        assert len(game_state.players) == 4
        assert game_state.players[3].name == "Diana"
        assert game_state.players[3].player_id == "player_4"


class TestSpecialGameCreation:
    """Test cases for special game creation functions."""
    
    def test_create_test_game(self):
        """Test creating test game."""
        game_state = create_test_game()
        
        # Check it's a valid 2-player game
        assert len(game_state.players) == 2
        assert game_state.players[0].name == "测试玩家1"
        assert game_state.players[1].name == "测试玩家2"
        assert game_state.rng_seed == 42
    
    def test_create_test_game_custom_config(self):
        """Test creating test game with custom config."""
        config = Config.default()
        config.starting_rats = 3  # Modify config
        
        game_state = create_test_game(config)
        
        # Check custom config was used
        for player in game_state.players:
            assert len(player.rats) == 3
    
    def test_create_demo_game(self):
        """Test creating demo game."""
        game_state = create_demo_game()
        
        # Check it's a 3-player game
        assert len(game_state.players) == 3
        assert game_state.players[0].name == "爱丽丝"
        assert game_state.players[1].name == "鲍勃"
        assert game_state.players[2].name == "查理"
        
        # Check demo modifications were applied
        alice = game_state.players[0]
        bob = game_state.players[1]
        charlie = game_state.players[2]
        
        # Alice should have resources and moved rat
        assert alice.inv.has(Resource.CHEESE, 2)
        assert alice.inv.has(Resource.TIN_CAN, 1)
        assert alice.rats[0].space_index == 5
        
        # Bob should have x2 active and moved rat
        assert bob.inv.x2_active is True
        assert bob.inv.has(Resource.SODA, 3)
        assert bob.rats[1].space_index == 8
        
        # Charlie should have scoring elements
        assert charlie.inv.bottlecaps == 2
        assert charlie.score == 5
        assert charlie.tracks["lightbulb"] == 2


class TestGameValidation:
    """Test cases for game setup validation."""
    
    def test_validate_game_setup_valid(self):
        """Test validation of properly set up game."""
        config = Config.default()
        game_state = new_game(2, ["Alice", "Bob"], config)
        
        errors = validate_game_setup(game_state, config)
        assert len(errors) == 0
    
    def test_validate_game_setup_invalid_players(self):
        """Test validation catches invalid player setup."""
        config = Config.default()
        game_state = new_game(2, ["Alice", "Bob"], config)
        
        # Modify to create invalid state
        game_state.players[0].rats[0].space_index = 10  # Wrong position
        game_state.players[1].inv.capacity = 5  # Wrong capacity
        
        errors = validate_game_setup(game_state, config)
        assert len(errors) > 0
        assert any("rat 1 at index 10" in error for error in errors)
        assert any("inventory capacity is 5" in error for error in errors)
    
    def test_validate_game_setup_invalid_game_state(self):
        """Test validation catches invalid game state."""
        config = Config.default()
        game_state = new_game(2, ["Alice", "Bob"], config)
        
        # Modify to create invalid state
        game_state.current_player = 5  # Invalid player index
        game_state.round = 0  # Invalid round
        game_state.game_over = True  # Should not be over
        
        errors = validate_game_setup(game_state, config)
        assert len(errors) >= 3
        assert any("Current player should be 0" in error for error in errors)
        assert any("Round should be 1" in error for error in errors)
        assert any("Game should not be over" in error for error in errors)


class TestSetupSummary:
    """Test cases for setup summary generation."""
    
    def test_get_setup_summary(self):
        """Test setup summary generation."""
        config = Config.default()
        game_state = new_game(3, ["Alice", "Bob", "Charlie"], config)
        
        summary = get_setup_summary(game_state)
        
        # Check summary contains expected information
        assert "游戏设置摘要" in summary
        assert "棋盘:" in summary
        assert "玩家数量: 3" in summary
        assert "Alice" in summary
        assert "Bob" in summary
        assert "Charlie" in summary
        assert "当前玩家:" in summary
        assert "回合: 1" in summary
        assert "随机种子:" in summary
    
    def test_setup_summary_format(self):
        """Test that setup summary is properly formatted."""
        config = Config.default()
        game_state = new_game(2, ["Test1", "Test2"], config)
        
        summary = get_setup_summary(game_state)
        lines = summary.split('\n')
        
        # Check structure
        assert lines[0] == "=== 游戏设置摘要 ==="
        assert len(lines) > 5  # Should have multiple lines of info
        
        # Check player info is indented
        player_lines = [line for line in lines if "Test1" in line or "Test2" in line]
        assert len(player_lines) == 2
        for line in player_lines:
            assert line.startswith("  ")  # Should be indented