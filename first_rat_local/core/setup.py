"""
Game setup and initialization system for First Rat.

This module handles board creation and game initialization.
游戏初始化和棋盘创建系统。
"""

import random
from typing import List
from .models import GameState, Board, Space, Player, Rat, Inventory, Rocket
from .config import Config
from .enums import Color, SpaceKind, Resource


def build_standard_board(config: Config) -> Board:
    """
    Build the standard game board from configuration.
    
    根据配置构建标准游戏棋盘。
    
    Args:
        config: Game configuration containing board layout
    
    Returns:
        Constructed Board object
    """
    spaces = []
    
    for space_data in config.board_layout:
        space = Space(
            space_id=space_data["space_id"],
            index=space_data["index"],
            color=Color(space_data["color"]),
            kind=SpaceKind(space_data["kind"]),
            payload=space_data.get("payload", {})
        )
        spaces.append(space)
    
    # Create board with spaces
    board = Board(
        spaces=spaces,
        start_index=config.start_index,
        launch_index=config.launch_index,
        shortcuts=None  # Could be added from config if needed
    )
    
    return board


def create_player(player_id: str, name: str, config: Config) -> Player:
    """
    Create a new player with initial setup.
    
    创建具有初始设置的新玩家。
    
    Args:
        player_id: Unique player identifier
        name: Player display name
        config: Game configuration
    
    Returns:
        Initialized Player object
    """
    # Create initial rats
    rats = []
    for i in range(config.starting_rats):
        rat_id = f"{player_id}_rat_{i + 1}"
        rat = Rat(
            rat_id=rat_id,
            owner_id=player_id,
            space_index=config.start_index,
            on_rocket=False
        )
        rats.append(rat)
    
    # Create initial inventory
    inventory = Inventory(
        capacity=config.starting_inventory_capacity,
        x2_active=False,
        bottlecaps=0
    )
    
    # Create player
    player = Player(
        player_id=player_id,
        name=name,
        rats=rats,
        inv=inventory,
        score=0
    )
    
    return player


def new_game(num_players: int, names: List[str], config: Config, seed: int = 0) -> GameState:
    """
    Create a new game with the specified number of players.
    
    创建指定玩家数量的新游戏。
    
    Args:
        num_players: Number of players (2-4)
        names: List of player names
        config: Game configuration
        seed: Random seed for reproducible games
    
    Returns:
        Initialized GameState ready to play
    
    Raises:
        ValueError: If invalid number of players or mismatched names
    """
    # Validate inputs
    if not (2 <= num_players <= 4):
        raise ValueError(f"Number of players must be 2-4, got {num_players}")
    
    if len(names) != num_players:
        raise ValueError(f"Expected {num_players} names, got {len(names)}")
    
    if len(set(names)) != len(names):
        raise ValueError("Player names must be unique")
    
    # Set random seed
    if seed != 0:
        random.seed(seed)
    
    # Build board
    board = build_standard_board(config)
    
    # Create players
    players = []
    for i, name in enumerate(names):
        player_id = f"player_{i + 1}"
        player = create_player(player_id, name, config)
        players.append(player)
    
    # Create rocket
    rocket = Rocket()
    
    # Create initial game state
    game_state = GameState(
        board=board,
        players=players,
        rocket=rocket,
        current_player=0,  # First player starts
        round=1,
        phase="MAIN",
        rng_seed=seed,
        history=[],
        game_over=False,
        winner_ids=None
    )
    
    return game_state


def create_test_game(config: Config | None = None, seed: int = 42) -> GameState:
    """
    Create a test game with default settings for development and testing.
    
    创建用于开发和测试的测试游戏。
    
    Args:
        config: Optional custom configuration (uses default if None)
        seed: Random seed for reproducible test games
    
    Returns:
        Test GameState with 2 players
    """
    if config is None:
        config = Config.default()
    
    test_names = ["测试玩家1", "测试玩家2"]
    return new_game(2, test_names, config, seed)


def create_demo_game(config: Config | None = None) -> GameState:
    """
    Create a demo game with interesting starting positions for demonstration.
    
    创建用于演示的游戏，具有有趣的起始位置。
    
    Args:
        config: Optional custom configuration
    
    Returns:
        Demo GameState with modified starting positions
    """
    if config is None:
        config = Config.default()
    
    # Create basic game
    demo_names = ["爱丽丝", "鲍勃", "查理"]
    game_state = new_game(3, demo_names, config, seed=123)
    
    # Modify for demo purposes - give players some resources and advance positions
    alice = game_state.players[0]
    bob = game_state.players[1]
    charlie = game_state.players[2]
    
    # Give Alice some resources and move a rat
    alice.inv.add(Resource.CHEESE, 2)
    alice.inv.add(Resource.TIN_CAN, 1)
    alice.rats[0].space_index = 5  # Move first rat forward
    
    # Give Bob different resources and activate x2
    bob.inv.add(Resource.SODA, 3)
    bob.inv.add(Resource.LIGHTBULB, 1)
    bob.inv.x2_active = True
    bob.rats[1].space_index = 8  # Move second rat forward
    
    # Give Charlie some scoring elements
    charlie.inv.bottlecaps = 2
    charlie.score = 5
    charlie.tracks["lightbulb"] = 2
    
    return game_state


def validate_game_setup(game_state: GameState, config: Config) -> List[str]:
    """
    Validate that a game state is properly set up according to configuration.
    
    验证游戏状态是否根据配置正确设置。
    
    Args:
        game_state: Game state to validate
        config: Expected configuration
    
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    # Check number of players
    num_players = len(game_state.players)
    if not (2 <= num_players <= 4):
        errors.append(f"Invalid number of players: {num_players}")
    
    # Check board setup
    if len(game_state.board.spaces) != len(config.board_layout):
        errors.append(f"Board has {len(game_state.board.spaces)} spaces, expected {len(config.board_layout)}")
    
    if game_state.board.start_index != config.start_index:
        errors.append(f"Start index is {game_state.board.start_index}, expected {config.start_index}")
    
    if game_state.board.launch_index != config.launch_index:
        errors.append(f"Launch index is {game_state.board.launch_index}, expected {config.launch_index}")
    
    # Check each player setup
    for i, player in enumerate(game_state.players):
        player_prefix = f"Player {i + 1}"
        
        # Check rat count
        if len(player.rats) != config.starting_rats:
            errors.append(f"{player_prefix} has {len(player.rats)} rats, expected {config.starting_rats}")
        
        # Check rat positions
        for j, rat in enumerate(player.rats):
            if rat.space_index != config.start_index:
                errors.append(f"{player_prefix} rat {j + 1} at index {rat.space_index}, expected {config.start_index}")
            
            if rat.on_rocket:
                errors.append(f"{player_prefix} rat {j + 1} should not be on rocket at start")
        
        # Check inventory setup
        if player.inv.capacity != config.starting_inventory_capacity:
            errors.append(f"{player_prefix} inventory capacity is {player.inv.capacity}, expected {config.starting_inventory_capacity}")
        
        if player.inv.total_resources() != 0:
            errors.append(f"{player_prefix} should start with no resources")
        
        if player.inv.x2_active:
            errors.append(f"{player_prefix} should not start with x2 active")
        
        if player.inv.bottlecaps != 0:
            errors.append(f"{player_prefix} should start with 0 bottle caps")
        
        # Check score
        if player.score != 0:
            errors.append(f"{player_prefix} should start with 0 score")
        
        # Check built parts
        if len(player.built_parts) != 0:
            errors.append(f"{player_prefix} should start with no built parts")
    
    # Check rocket setup
    for part, builder in game_state.rocket.parts.items():
        if builder is not None:
            errors.append(f"Rocket part {part.value} should not be built at start")
    
    # Check game state
    if game_state.current_player != 0:
        errors.append(f"Current player should be 0, got {game_state.current_player}")
    
    if game_state.round != 1:
        errors.append(f"Round should be 1, got {game_state.round}")
    
    if game_state.game_over:
        errors.append("Game should not be over at start")
    
    if game_state.winner_ids is not None:
        errors.append("Winner IDs should be None at start")
    
    if len(game_state.history) != 0:
        errors.append("History should be empty at start")
    
    return errors


def get_setup_summary(game_state: GameState) -> str:
    """
    Generate a human-readable summary of the game setup.
    
    生成游戏设置的人类可读摘要。
    
    Args:
        game_state: Game state to summarize
    
    Returns:
        Formatted setup summary string
    """
    lines = ["=== 游戏设置摘要 ==="]
    
    # Board info
    lines.append(f"棋盘: {len(game_state.board.spaces)} 个格子 (起点: {game_state.board.start_index}, 发射台: {game_state.board.launch_index})")
    
    # Players info
    lines.append(f"玩家数量: {len(game_state.players)}")
    
    for i, player in enumerate(game_state.players, 1):
        lines.append(f"  {i}. {player.name} (ID: {player.player_id})")
        lines.append(f"     老鼠数量: {len(player.rats)}")
        lines.append(f"     背包容量: {player.inv.capacity}")
    
    # Game state
    lines.append(f"当前玩家: {game_state.current_player_obj().name}")
    lines.append(f"回合: {game_state.round}")
    lines.append(f"随机种子: {game_state.rng_seed}")
    
    return "\n".join(lines)