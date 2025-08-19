"""
Unit tests for CLI rendering system.

Tests text-based rendering of game state components.
"""

import pytest
from first_rat_local.cli.render import (
    render_board, render_players, render_rocket_status, render_game_info,
    render_events, render_available_actions, render_full_game_state,
    _get_space_type_char, _get_color_char, _get_resource_name
)
from first_rat_local.core.models import GameState, Board, Space, Player, Rat, Inventory, Rocket
from first_rat_local.core.config import Config
from first_rat_local.core.enums import Color, SpaceKind, Resource, RocketPart, DomainEventType
from first_rat_local.core.events import create_resource_gained_event, create_score_changed_event


class TestBoardRendering:
    """Test cases for board rendering."""
    
    def create_simple_game_state(self) -> GameState:
        """Create a simple game state for testing."""
        # Create a small board for testing
        spaces = [
            Space(0, 0, Color.GREEN, SpaceKind.START),
            Space(1, 1, Color.YELLOW, SpaceKind.RESOURCE, {"resource": Resource.CHEESE.value}),
            Space(2, 2, Color.RED, SpaceKind.SHOP_MOLE),
            Space(3, 3, Color.BLUE, SpaceKind.LAUNCH_PAD)
        ]
        
        board = Board(spaces=spaces, start_index=0, launch_index=3)
        
        player1 = Player(
            player_id="p1",
            name="Alice",
            rats=[
                Rat("r1", "p1", 0),  # At start
                Rat("r2", "p1", 2)   # At mole shop
            ],
            inv=Inventory()
        )
        
        player2 = Player(
            player_id="p2",
            name="Bob",
            rats=[Rat("r3", "p2", 1)],  # At cheese space
            inv=Inventory()
        )
        
        return GameState(
            board=board,
            players=[player1, player2],
            rocket=Rocket(),
            current_player=0
        )
    
    def test_render_board_basic(self):
        """Test basic board rendering."""
        state = self.create_simple_game_state()
        board_text = render_board(state)
        
        # Check basic structure
        assert "游戏棋盘" in board_text
        assert "图例" in board_text
        
        # Check space indices are shown
        assert "索引:" in board_text
        assert " 0" in board_text
        assert " 1" in board_text
        assert " 2" in board_text
        assert " 3" in board_text
        
        # Check space types are shown
        assert "类型:" in board_text
        assert " S" in board_text  # START
        assert " R" in board_text  # RESOURCE
        assert " M" in board_text  # MOLE shop
        assert " L" in board_text  # LAUNCH_PAD
        
        # Check colors are shown
        assert "颜色:" in board_text
        assert " G" in board_text  # GREEN
        assert " Y" in board_text  # YELLOW
        assert " R" in board_text  # RED
        assert " B" in board_text  # BLUE
    
    def test_render_board_rat_positions(self):
        """Test that rat positions are correctly shown on board."""
        state = self.create_simple_game_state()
        board_text = render_board(state)
        
        # Check rat positions are shown
        assert "老鼠:" in board_text
        assert "P1" in board_text  # Player 1's rats
        assert "P2" in board_text  # Player 2's rat
    
    def test_render_board_legend(self):
        """Test that board legend is included."""
        state = self.create_simple_game_state()
        board_text = render_board(state)
        
        # Check legend is present
        assert "图例" in board_text
        assert "S=起点" in board_text
        assert "L=发射台" in board_text
        assert "R=资源" in board_text
        assert "M=鼹鼠店" in board_text
        assert "G=绿" in board_text
        assert "P1=玩家1" in board_text


class TestPlayerRendering:
    """Test cases for player rendering."""
    
    def create_detailed_game_state(self) -> GameState:
        """Create a game state with detailed player information."""
        board = Board([Space(0, 0, Color.GREEN, SpaceKind.START)], 0, 0)
        
        player1 = Player(
            player_id="p1",
            name="Alice",
            rats=[
                Rat("r1", "p1", 0),
                Rat("r2", "p1", 0, on_rocket=True)
            ],
            inv=Inventory(capacity=5),
            score=15
        )
        
        # Add resources and other elements
        player1.inv.add(Resource.CHEESE, 3)
        player1.inv.add(Resource.TIN_CAN, 2)
        player1.inv.x2_active = True
        player1.inv.bottlecaps = 2
        player1.tracks["lightbulb"] = 3
        player1.built_parts.add(RocketPart.NOSE)
        
        player2 = Player(
            player_id="p2",
            name="Bob",
            rats=[Rat("r3", "p2", 0)],
            inv=Inventory(),
            score=8
        )
        
        return GameState(
            board=board,
            players=[player1, player2],
            rocket=Rocket(),
            current_player=0
        )
    
    def test_render_players_basic_info(self):
        """Test basic player information rendering."""
        state = self.create_detailed_game_state()
        players_text = render_players(state)
        
        # Check basic structure
        assert "玩家状态" in players_text
        
        # Check player names and scores
        assert "Alice" in players_text
        assert "Bob" in players_text
        assert "分数: 15" in players_text
        assert "分数: 8" in players_text
        
        # Check current player indicator
        assert "当前玩家" in players_text
    
    def test_render_players_inventory(self):
        """Test player inventory rendering."""
        state = self.create_detailed_game_state()
        players_text = render_players(state)
        
        # Check inventory information
        assert "背包" in players_text
        assert "奶酪×3" in players_text
        assert "罐头×2" in players_text
        assert "X2激活" in players_text
        
        # Check empty inventory for player 2
        assert "空" in players_text
    
    def test_render_players_additional_elements(self):
        """Test rendering of additional player elements."""
        state = self.create_detailed_game_state()
        players_text = render_players(state)
        
        # Check bottle caps
        assert "瓶盖: 2" in players_text
        
        # Check tracks
        assert "轨道:" in players_text
        assert "lightbulb轨道: 3级" in players_text
        
        # Check built parts
        assert "已建造部件:" in players_text
        assert "火箭头" in players_text
    
    def test_render_players_rat_info(self):
        """Test rat information rendering."""
        state = self.create_detailed_game_state()
        players_text = render_players(state)
        
        # Check rat counts
        assert "老鼠总数: 2" in players_text
        assert "棋盘上: 1" in players_text
        assert "火箭上: 1" in players_text
        
        # Check rat positions
        assert "棋盘位置:" in players_text
        assert "火箭上:" in players_text


class TestRocketRendering:
    """Test cases for rocket status rendering."""
    
    def test_render_rocket_status_empty(self):
        """Test rendering empty rocket."""
        board = Board([Space(0, 0, Color.GREEN, SpaceKind.START)], 0, 0)
        player = Player("p1", "Alice", [Rat("r1", "p1", 0)], Inventory())
        state = GameState(board=board, players=[player], rocket=Rocket())
        
        rocket_text = render_rocket_status(state)
        
        # Check basic structure
        assert "火箭状态" in rocket_text
        assert "未建造部件:" in rocket_text
        assert "建造进度: 0/5" in rocket_text
        
        # Check all parts are listed as unbuilt
        assert "火箭头" in rocket_text
        assert "燃料箱" in rocket_text
        assert "引擎" in rocket_text
    
    def test_render_rocket_status_partial(self):
        """Test rendering partially built rocket."""
        board = Board([Space(0, 0, Color.GREEN, SpaceKind.START)], 0, 0)
        player = Player("p1", "Alice", [Rat("r1", "p1", 0)], Inventory())
        rocket = Rocket()
        rocket.build_part(RocketPart.NOSE, "p1")
        rocket.build_part(RocketPart.ENGINE, "p1")
        
        state = GameState(board=board, players=[player], rocket=rocket)
        
        rocket_text = render_rocket_status(state)
        
        # Check built parts section
        assert "已建造部件:" in rocket_text
        assert "✓ 火箭头 (建造者: Alice)" in rocket_text
        assert "✓ 引擎 (建造者: Alice)" in rocket_text
        
        # Check progress
        assert "建造进度: 2/5" in rocket_text


class TestGameInfoRendering:
    """Test cases for game info rendering."""
    
    def test_render_game_info_active_game(self):
        """Test rendering info for active game."""
        board = Board([Space(0, 0, Color.GREEN, SpaceKind.START)], 0, 0)
        player = Player("p1", "Alice", [Rat("r1", "p1", 0)], Inventory())
        state = GameState(board=board, players=[player], rocket=Rocket(), round=3)
        
        info_text = render_game_info(state)
        
        # Check basic info
        assert "游戏信息" in info_text
        assert "回合: 3" in info_text
        assert "阶段: MAIN" in info_text
        assert "当前玩家: Alice" in info_text
    
    def test_render_game_info_finished_game(self):
        """Test rendering info for finished game."""
        board = Board([Space(0, 0, Color.GREEN, SpaceKind.START)], 0, 0)
        player = Player("p1", "Alice", [Rat("r1", "p1", 0)], Inventory())
        state = GameState(
            board=board, 
            players=[player], 
            rocket=Rocket(),
            game_over=True,
            winner_ids=["p1"]
        )
        
        info_text = render_game_info(state)
        
        # Check game over info
        assert "状态: 游戏结束" in info_text
        assert "获胜者: Alice" in info_text


class TestEventRendering:
    """Test cases for event rendering."""
    
    def test_render_events_empty(self):
        """Test rendering with no events."""
        events_text = render_events([])
        
        assert "最近事件" in events_text
        assert "(无事件)" in events_text
    
    def test_render_events_with_events(self):
        """Test rendering with some events."""
        events = [
            create_resource_gained_event("p1", Resource.CHEESE, 2, "space"),
            create_score_changed_event("p1", 5, "build_part", 15)
        ]
        
        events_text = render_events(events)
        
        # Check events are shown
        assert "最近事件" in events_text
        assert "获得了" in events_text
        assert "奶酪" in events_text
        assert "获得" in events_text
        assert "分" in events_text
    
    def test_render_events_max_limit(self):
        """Test that event rendering respects max limit."""
        # Create more events than the limit
        events = []
        for i in range(15):
            events.append(create_resource_gained_event("p1", Resource.CHEESE, 1, "test"))
        
        events_text = render_events(events, max_events=5)
        
        # Should show only 5 most recent events
        lines = events_text.split('\n')
        event_lines = [line for line in lines if line.strip() and line[0].isdigit()]
        assert len(event_lines) == 5
        
        # Should indicate there are more events
        assert "还有" in events_text
        assert "个更早的事件" in events_text


class TestAvailableActionsRendering:
    """Test cases for available actions rendering."""
    
    def test_render_available_actions_basic(self):
        """Test basic available actions rendering."""
        board = Board([Space(0, 0, Color.GREEN, SpaceKind.START)], 0, 0)
        player = Player("p1", "Alice", [Rat("r1", "p1", 0)], Inventory())
        player.inv.add(Resource.CHEESE, 2)
        state = GameState(board=board, players=[player], rocket=Rocket())
        
        actions_text = render_available_actions(state, "p1")
        
        # Check basic structure
        assert "可用动作" in actions_text
        
        # Check movement actions
        assert "移动 (move):" in actions_text
        assert "单鼠移动:" in actions_text
        assert "多鼠移动:" in actions_text
        assert "可移动老鼠: r1" in actions_text
        
        # Check build actions
        assert "建造动作:" in actions_text
        assert "建造火箭:" in actions_text
        
        # Check donate actions (player has cheese)
        assert "捐赠动作:" in actions_text
        assert "捐赠奶酪:" in actions_text
        assert "可捐赠奶酪: 2" in actions_text
        
        # Check end turn
        assert "结束回合: end" in actions_text
    
    def test_render_available_actions_wrong_turn(self):
        """Test rendering when it's not the player's turn."""
        board = Board([Space(0, 0, Color.GREEN, SpaceKind.START)], 0, 0)
        player1 = Player("p1", "Alice", [Rat("r1", "p1", 0)], Inventory())
        player2 = Player("p2", "Bob", [Rat("r2", "p2", 0)], Inventory())
        state = GameState(board=board, players=[player1, player2], rocket=Rocket(), current_player=0)
        
        actions_text = render_available_actions(state, "p2")  # Not Bob's turn
        
        assert "不是你的回合" in actions_text
    
    def test_render_available_actions_game_over(self):
        """Test rendering when game is over."""
        board = Board([Space(0, 0, Color.GREEN, SpaceKind.START)], 0, 0)
        player = Player("p1", "Alice", [Rat("r1", "p1", 0)], Inventory())
        state = GameState(board=board, players=[player], rocket=Rocket(), game_over=True)
        
        actions_text = render_available_actions(state, "p1")
        
        assert "游戏已结束" in actions_text


class TestHelperFunctions:
    """Test cases for helper functions."""
    
    def test_get_space_type_char(self):
        """Test space type character mapping."""
        assert _get_space_type_char(SpaceKind.START) == 'S'
        assert _get_space_type_char(SpaceKind.LAUNCH_PAD) == 'L'
        assert _get_space_type_char(SpaceKind.RESOURCE) == 'R'
        assert _get_space_type_char(SpaceKind.SHOP_MOLE) == 'M'
        assert _get_space_type_char(SpaceKind.SHOP_FROG) == 'F'
        assert _get_space_type_char(SpaceKind.SHOP_CROW) == 'C'
    
    def test_get_color_char(self):
        """Test color character mapping."""
        assert _get_color_char(Color.GREEN) == 'G'
        assert _get_color_char(Color.YELLOW) == 'Y'
        assert _get_color_char(Color.RED) == 'R'
        assert _get_color_char(Color.BLUE) == 'B'
    
    def test_get_resource_name(self):
        """Test resource name mapping."""
        assert _get_resource_name(Resource.CHEESE) == "奶酪"
        assert _get_resource_name(Resource.TIN_CAN) == "罐头"
        assert _get_resource_name(Resource.SODA) == "苏打"
        assert _get_resource_name(Resource.LIGHTBULB) == "灯泡"
        assert _get_resource_name(Resource.BOTTLECAP) == "瓶盖"


class TestFullGameStateRendering:
    """Test cases for full game state rendering."""
    
    def test_render_full_game_state(self):
        """Test complete game state rendering."""
        # Create a simple game state
        board = Board([Space(0, 0, Color.GREEN, SpaceKind.START)], 0, 0)
        player = Player("p1", "Alice", [Rat("r1", "p1", 0)], Inventory())
        state = GameState(board=board, players=[player], rocket=Rocket())
        
        events = [create_resource_gained_event("p1", Resource.CHEESE, 1, "test")]
        
        full_text = render_full_game_state(state, events)
        
        # Check all sections are included
        assert "游戏信息" in full_text
        assert "游戏棋盘" in full_text
        assert "玩家状态" in full_text
        assert "火箭状态" in full_text
        assert "最近事件" in full_text
        assert "可用动作" in full_text
        
        # Check sections are separated
        sections = full_text.split("\n\n")
        assert len(sections) >= 5  # Should have multiple sections