"""
CLI rendering system for First Rat game.

This module provides text-based rendering for the game state.
CLI渲染系统，提供基于文本的游戏状态显示。
"""

from typing import List, Dict, Any
from ..core.models import GameState, Player, Rat
from ..core.enums import Color, SpaceKind, Resource, RocketPart, DomainEventType
from ..core.events import DomainEvent, format_event_for_display


def render_board(state: GameState) -> str:
    """
    Render the game board with rat positions.
    
    渲染游戏棋盘和老鼠位置。
    
    Args:
        state: Current game state
    
    Returns:
        Formatted board string
    """
    lines = ["=== 游戏棋盘 ==="]
    
    # Get all rats on board for position display
    all_rats = state.board.get_all_rats_on_board(state.players)
    rat_positions = {}
    for rat in all_rats:
        if rat.space_index not in rat_positions:
            rat_positions[rat.space_index] = []
        rat_positions[rat.space_index].append(rat)
    
    # Render board in rows of 10 spaces
    spaces_per_row = 10
    total_spaces = len(state.board.spaces)
    
    for row_start in range(0, total_spaces, spaces_per_row):
        row_end = min(row_start + spaces_per_row, total_spaces)
        
        # Space indices row
        indices = []
        for i in range(row_start, row_end):
            indices.append(f"{i:2d}")
        lines.append("索引: " + " ".join(indices))
        
        # Space types row
        types = []
        for i in range(row_start, row_end):
            space = state.board.spaces[i]
            type_char = _get_space_type_char(space.kind)
            types.append(f" {type_char}")
        lines.append("类型: " + " ".join(types))
        
        # Colors row
        colors = []
        for i in range(row_start, row_end):
            space = state.board.spaces[i]
            color_char = _get_color_char(space.color)
            colors.append(f" {color_char}")
        lines.append("颜色: " + " ".join(colors))
        
        # Rats row
        rats = []
        for i in range(row_start, row_end):
            if i in rat_positions:
                rat_count = len(rat_positions[i])
                if rat_count == 1:
                    # Show player number for single rat
                    rat = rat_positions[i][0]
                    player_num = _get_player_number(rat.owner_id, state.players)
                    rats.append(f"P{player_num}")
                else:
                    # Show count for multiple rats
                    rats.append(f"{rat_count}鼠")
            else:
                rats.append("  ")
        lines.append("老鼠: " + " ".join(rats))
        
        lines.append("")  # Empty line between rows
    
    # Add legend
    lines.append("=== 图例 ===")
    lines.append("类型: S=起点 L=发射台 R=资源 M=鼹鼠店 F=青蛙店 C=乌鸦店 T=轨道 ?=其他")
    lines.append("颜色: G=绿 Y=黄 R=红 B=蓝")
    lines.append("老鼠: P1=玩家1 P2=玩家2 等等")
    
    return "\n".join(lines)


def render_players(state: GameState) -> str:
    """
    Render all players' status information.
    
    渲染所有玩家的状态信息。
    
    Args:
        state: Current game state
    
    Returns:
        Formatted players status string
    """
    lines = ["=== 玩家状态 ==="]
    
    for i, player in enumerate(state.players):
        is_current = (i == state.current_player)
        current_marker = " ← 当前玩家" if is_current else ""
        
        lines.append(f"\n玩家 {i + 1}: {player.name}{current_marker}")
        lines.append(f"  分数: {player.score}")
        
        # Inventory
        inv_info = f"  背包 ({player.inv.total_resources()}/{player.inv.capacity}): "
        if player.inv.total_resources() == 0:
            inv_info += "空"
        else:
            resources = []
            for resource, amount in player.inv.res.items():
                resource_name = _get_resource_name(resource)
                resources.append(f"{resource_name}×{amount}")
            inv_info += ", ".join(resources)
        
        if player.inv.x2_active:
            inv_info += " [X2激活]"
        
        lines.append(inv_info)
        
        # Bottle caps
        if player.inv.bottlecaps > 0:
            lines.append(f"  瓶盖: {player.inv.bottlecaps}")
        
        # Tracks
        if player.tracks:
            track_info = []
            for track_name, level in player.tracks.items():
                if level > 0:
                    track_info.append(f"{track_name}轨道: {level}级")
            if track_info:
                lines.append(f"  轨道: {', '.join(track_info)}")
        
        # Built rocket parts
        if player.built_parts:
            part_names = [_get_rocket_part_name(part) for part in player.built_parts]
            lines.append(f"  已建造部件: {', '.join(part_names)}")
        
        # Rats
        board_rats = player.get_rats_on_board()
        rocket_rats = player.get_rats_on_rocket()
        
        lines.append(f"  老鼠总数: {len(player.rats)} (棋盘上: {len(board_rats)}, 火箭上: {len(rocket_rats)})")
        
        if board_rats:
            rat_positions = []
            for rat in board_rats:
                rat_positions.append(f"{rat.rat_id}@{rat.space_index}")
            lines.append(f"    棋盘位置: {', '.join(rat_positions)}")
        
        if rocket_rats:
            rat_ids = [rat.rat_id for rat in rocket_rats]
            lines.append(f"    火箭上: {', '.join(rat_ids)}")
    
    return "\n".join(lines)


def render_rocket_status(state: GameState) -> str:
    """
    Render the rocket construction status.
    
    渲染火箭建造状态。
    
    Args:
        state: Current game state
    
    Returns:
        Formatted rocket status string
    """
    lines = ["=== 火箭状态 ==="]
    
    built_parts = []
    unbuilt_parts = []
    
    for part in RocketPart:
        if state.rocket.is_part_built(part):
            builder_id = state.rocket.get_builder(part)
            builder = state.get_player_by_id(builder_id)
            builder_name = builder.name if builder else "未知"
            part_name = _get_rocket_part_name(part)
            built_parts.append(f"{part_name} (建造者: {builder_name})")
        else:
            part_name = _get_rocket_part_name(part)
            unbuilt_parts.append(part_name)
    
    if built_parts:
        lines.append("已建造部件:")
        for part_info in built_parts:
            lines.append(f"  ✓ {part_info}")
    
    if unbuilt_parts:
        lines.append("未建造部件:")
        for part_name in unbuilt_parts:
            lines.append(f"  ○ {part_name}")
    
    # Show total progress
    total_parts = len(RocketPart)
    built_count = len(built_parts)
    lines.append(f"\n建造进度: {built_count}/{total_parts} ({built_count/total_parts*100:.0f}%)")
    
    return "\n".join(lines)


def render_game_info(state: GameState) -> str:
    """
    Render general game information.
    
    渲染游戏基本信息。
    
    Args:
        state: Current game state
    
    Returns:
        Formatted game info string
    """
    lines = ["=== 游戏信息 ==="]
    
    lines.append(f"回合: {state.round}")
    lines.append(f"阶段: {state.phase}")
    
    if state.game_over:
        lines.append("状态: 游戏结束")
        if state.winner_ids:
            winner_names = []
            for winner_id in state.winner_ids:
                winner = state.get_player_by_id(winner_id)
                if winner:
                    winner_names.append(winner.name)
            lines.append(f"获胜者: {', '.join(winner_names)}")
    else:
        current_player = state.current_player_obj()
        lines.append(f"当前玩家: {current_player.name}")
    
    return "\n".join(lines)


def render_events(events: List[DomainEvent], max_events: int = 10) -> str:
    """
    Render recent domain events.
    
    渲染最近的领域事件。
    
    Args:
        events: List of domain events
        max_events: Maximum number of events to show
    
    Returns:
        Formatted events string
    """
    if not events:
        return "=== 最近事件 ===\n(无事件)"
    
    lines = ["=== 最近事件 ==="]
    
    # Show most recent events first
    recent_events = events[-max_events:] if len(events) > max_events else events
    
    for i, event in enumerate(reversed(recent_events), 1):
        event_text = format_event_for_display(event)
        lines.append(f"{i:2d}. {event_text}")
    
    if len(events) > max_events:
        lines.append(f"... (还有 {len(events) - max_events} 个更早的事件)")
    
    return "\n".join(lines)


def render_available_actions(state: GameState, player_id: str) -> str:
    """
    Render available actions for a player.
    
    渲染玩家可用的动作。
    
    Args:
        state: Current game state
        player_id: Player to show actions for
    
    Returns:
        Formatted available actions string
    """
    if state.game_over:
        return "=== 可用动作 ===\n游戏已结束，无可用动作。"
    
    if state.current_player_obj().player_id != player_id:
        return "=== 可用动作 ===\n不是你的回合。"
    
    lines = ["=== 可用动作 ==="]
    
    player = state.get_player_by_id(player_id)
    board_rats = player.get_rats_on_board()
    
    # Movement actions
    if board_rats:
        lines.append("移动 (move):")
        lines.append("  单鼠移动: move <老鼠ID> <步数1-5>")
        lines.append("  多鼠移动: move <老鼠ID1> <步数1-3> <老鼠ID2> <步数1-3> ...")
        
        rat_list = ", ".join([rat.rat_id for rat in board_rats])
        lines.append(f"  可移动老鼠: {rat_list}")
    
    # Shop actions (if any rat is at a shop)
    shop_actions = []
    for rat in board_rats:
        space = state.board.get_space(rat.space_index)
        if space.kind in [SpaceKind.SHOP_MOLE, SpaceKind.SHOP_FROG, SpaceKind.SHOP_CROW]:
            shop_name = _get_shop_name(space.kind)
            shop_actions.append(f"{rat.rat_id}在{shop_name}")
    
    if shop_actions:
        lines.append("\n商店动作:")
        lines.append("  购买: buy <商店类型> <物品> <老鼠ID>")
        lines.append("  偷窃: steal <商店类型> <物品> <老鼠ID>")
        for action in shop_actions:
            lines.append(f"  {action}")
    
    # Build actions
    lines.append("\n建造动作:")
    lines.append("  建造火箭: build <部件名>")
    unbuilt_parts = []
    for part in RocketPart:
        if not state.rocket.is_part_built(part):
            unbuilt_parts.append(_get_rocket_part_name(part))
    if unbuilt_parts:
        lines.append(f"  可建造部件: {', '.join(unbuilt_parts)}")
    else:
        lines.append("  所有部件已建造完成")
    
    # Donate actions
    if player.inv.has(Resource.CHEESE, 1):
        lines.append("\n捐赠动作:")
        lines.append("  捐赠奶酪: donate <数量1-4>")
        cheese_count = player.inv.res.get(Resource.CHEESE, 0)
        lines.append(f"  可捐赠奶酪: {cheese_count}")
    
    # End turn
    lines.append("\n回合控制:")
    lines.append("  结束回合: end")
    
    return "\n".join(lines)


def render_full_game_state(state: GameState, recent_events: List[DomainEvent] = None) -> str:
    """
    Render the complete game state for display.
    
    渲染完整的游戏状态用于显示。
    
    Args:
        state: Current game state
        recent_events: Recent events to display
    
    Returns:
        Complete formatted game state string
    """
    sections = []
    
    # Game info
    sections.append(render_game_info(state))
    
    # Board
    sections.append(render_board(state))
    
    # Players
    sections.append(render_players(state))
    
    # Rocket
    sections.append(render_rocket_status(state))
    
    # Recent events
    if recent_events:
        sections.append(render_events(recent_events))
    
    # Available actions for current player
    if not state.game_over:
        current_player_id = state.current_player_obj().player_id
        sections.append(render_available_actions(state, current_player_id))
    
    return "\n\n".join(sections)


# Helper functions for rendering

def _get_space_type_char(space_kind: SpaceKind) -> str:
    """Get single character representation of space type."""
    type_chars = {
        SpaceKind.START: 'S',
        SpaceKind.LAUNCH_PAD: 'L',
        SpaceKind.RESOURCE: 'R',
        SpaceKind.SHOP_MOLE: 'M',
        SpaceKind.SHOP_FROG: 'F',
        SpaceKind.SHOP_CROW: 'C',
        SpaceKind.LIGHTBULB_TRACK: 'T',
        SpaceKind.SHORTCUT: '→',
        SpaceKind.HAZARD: '!',
    }
    return type_chars.get(space_kind, '?')


def _get_color_char(color: Color) -> str:
    """Get single character representation of color."""
    color_chars = {
        Color.GREEN: 'G',
        Color.YELLOW: 'Y',
        Color.RED: 'R',
        Color.BLUE: 'B',
    }
    return color_chars.get(color, '?')


def _get_player_number(player_id: str, players: List[Player]) -> int:
    """Get player number (1-based) from player ID."""
    for i, player in enumerate(players):
        if player.player_id == player_id:
            return i + 1
    return 0


def _get_resource_name(resource: Resource) -> str:
    """Get Chinese name for resource."""
    resource_names = {
        Resource.CHEESE: "奶酪",
        Resource.TIN_CAN: "罐头",
        Resource.SODA: "苏打",
        Resource.LIGHTBULB: "灯泡",
        Resource.BOTTLECAP: "瓶盖",
    }
    return resource_names.get(resource, str(resource.value))


def _get_rocket_part_name(part: RocketPart) -> str:
    """Get Chinese name for rocket part."""
    part_names = {
        RocketPart.NOSE: "火箭头",
        RocketPart.TANK: "燃料箱",
        RocketPart.ENGINE: "引擎",
        RocketPart.FIN_A: "尾翼A",
        RocketPart.FIN_B: "尾翼B",
    }
    return part_names.get(part, str(part.value))


def _get_shop_name(shop_kind: SpaceKind) -> str:
    """Get Chinese name for shop type."""
    shop_names = {
        SpaceKind.SHOP_MOLE: "鼹鼠店",
        SpaceKind.SHOP_FROG: "青蛙店",
        SpaceKind.SHOP_CROW: "乌鸦店",
    }
    return shop_names.get(shop_kind, str(shop_kind.value))