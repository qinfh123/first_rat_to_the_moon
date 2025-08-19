"""
Scoring and end game system for First Rat game.

This module handles final scoring calculations and end game detection.
计分与终局判定系统。
"""

from typing import Dict, List, Tuple, Any
from .models import GameState, Player
from .config import Config
from .enums import RocketPart
from .events import create_game_ended_event


def check_endgame(state: GameState, config: Config) -> bool:
    """
    Check if the game should end based on configured triggers.
    
    检查游戏是否应该结束。
    
    Returns:
        True if game should end, False otherwise
    """
    triggers = config.endgame_triggers
    
    # Check fourth rat on rocket trigger
    if triggers.get("fourth_rat_on_rocket", False):
        for player in state.players:
            rats_on_rocket = len(player.get_rats_on_rocket())
            if rats_on_rocket >= 4:
                return True
    
    # Check eighth scoring marker trigger
    if triggers.get("eighth_scoring_marker", False):
        total_scoring_markers = 0
        for player in state.players:
            # Count built rocket parts as scoring markers
            total_scoring_markers += len(player.built_parts)
        
        if total_scoring_markers >= 8:
            return True
    
    return False


def calculate_final_scores(state: GameState, config: Config) -> Dict[str, Dict[str, Any]]:
    """
    Calculate final scores for all players.
    
    计算所有玩家的最终得分。
    
    Returns:
        Dictionary mapping player_id to scoring breakdown
    """
    scoring_breakdown = {}
    
    for player in state.players:
        breakdown = {
            "player_name": player.name,
            "current_score": player.score,  # Points already earned during game
            "rocket_parts_score": 0,
            "bottlecaps_score": 0,
            "lightbulb_track_score": 0,
            "remaining_resources_score": 0,
            "rats_on_rocket_count": len(player.get_rats_on_rocket()),
            "total_score": 0
        }
        
        # Calculate rocket parts score
        if config.scoring_rules.get("rocket_parts", True):
            for part in player.built_parts:
                part_score = config.rocket_part_scores.get(part, 0)
                breakdown["rocket_parts_score"] += part_score
        
        # Calculate bottlecaps score
        bottlecap_multiplier = config.scoring_rules.get("bottlecaps", 1)
        if bottlecap_multiplier > 0:
            breakdown["bottlecaps_score"] = player.inv.bottlecaps * bottlecap_multiplier
        
        # Calculate lightbulb track score
        if config.scoring_rules.get("lightbulb_track", True):
            track_level = player.tracks.get("lightbulb", 0)
            # Score based on track level (could be configured differently)
            breakdown["lightbulb_track_score"] = track_level * 2  # 2 points per level
        
        # Calculate remaining resources score
        if config.scoring_rules.get("remaining_resources", False):
            total_resources = player.inv.total_resources()
            # Convert every 2 resources to 1 point (configurable)
            breakdown["remaining_resources_score"] = total_resources // 2
        
        # Calculate total score
        breakdown["total_score"] = (
            breakdown["current_score"] +
            breakdown["rocket_parts_score"] +
            breakdown["bottlecaps_score"] +
            breakdown["lightbulb_track_score"] +
            breakdown["remaining_resources_score"]
        )
        
        scoring_breakdown[player.player_id] = breakdown
    
    return scoring_breakdown


def determine_winners(scoring_breakdown: Dict[str, Dict[str, Any]]) -> List[str]:
    """
    Determine the winner(s) based on final scores and tiebreakers.
    
    根据最终得分和平局规则确定获胜者。
    
    Returns:
        List of player IDs who won (can be multiple in case of ties)
    """
    # Find highest score
    max_score = max(breakdown["total_score"] for breakdown in scoring_breakdown.values())
    
    # Find all players with max score
    tied_players = [
        player_id for player_id, breakdown in scoring_breakdown.items()
        if breakdown["total_score"] == max_score
    ]
    
    # If only one player has max score, they win
    if len(tied_players) == 1:
        return tied_players
    
    # Tiebreaker: most rats on rocket
    max_rats_on_rocket = max(
        scoring_breakdown[player_id]["rats_on_rocket_count"] 
        for player_id in tied_players
    )
    
    winners = [
        player_id for player_id in tied_players
        if scoring_breakdown[player_id]["rats_on_rocket_count"] == max_rats_on_rocket
    ]
    
    return winners


def finalize_game(state: GameState, config: Config, trigger: str) -> Dict[str, Any]:
    """
    Finalize the game by calculating scores and determining winners.
    
    通过计算分数和确定获胜者来结束游戏。
    
    Args:
        state: Current game state
        config: Game configuration
        trigger: What triggered the end game
    
    Returns:
        Dictionary with complete game results
    """
    # Calculate final scores
    scoring_breakdown = calculate_final_scores(state, config)
    
    # Determine winners
    winner_ids = determine_winners(scoring_breakdown)
    
    # Update game state
    state.game_over = True
    state.winner_ids = winner_ids
    
    # Create final scores dictionary for events
    final_scores = {
        player_id: breakdown["total_score"]
        for player_id, breakdown in scoring_breakdown.items()
    }
    
    # Create game ended event
    game_ended_event = create_game_ended_event(winner_ids, final_scores, trigger)
    
    # Add event to history
    history_entry = {
        "action": {
            "type": "GAME_END",
            "payload": {"trigger": trigger},
            "actor": "system"
        },
        "events": [{
            "type": game_ended_event.type.value,
            "payload": game_ended_event.payload,
            "actor": game_ended_event.actor,
            "timestamp": game_ended_event.timestamp
        }],
        "derived_data": {}
    }
    state.history.append(history_entry)
    
    # Prepare results
    results = {
        "game_over": True,
        "trigger": trigger,
        "winner_ids": winner_ids,
        "scoring_breakdown": scoring_breakdown,
        "final_scores": final_scores,
        "game_ended_event": game_ended_event
    }
    
    return results


def get_scoring_summary(scoring_breakdown: Dict[str, Dict[str, Any]]) -> str:
    """
    Generate a human-readable scoring summary.
    
    生成人类可读的计分总结。
    """
    lines = ["=== 最终计分 ==="]
    
    # Sort players by total score (descending)
    sorted_players = sorted(
        scoring_breakdown.items(),
        key=lambda x: x[1]["total_score"],
        reverse=True
    )
    
    for rank, (player_id, breakdown) in enumerate(sorted_players, 1):
        lines.append(f"\n第{rank}名: {breakdown['player_name']} (总分: {breakdown['total_score']})")
        lines.append(f"  游戏中得分: {breakdown['current_score']}")
        lines.append(f"  火箭部件: {breakdown['rocket_parts_score']}")
        lines.append(f"  瓶盖: {breakdown['bottlecaps_score']}")
        lines.append(f"  灯泡轨道: {breakdown['lightbulb_track_score']}")
        
        if breakdown['remaining_resources_score'] > 0:
            lines.append(f"  剩余资源: {breakdown['remaining_resources_score']}")
        
        lines.append(f"  火箭上老鼠数: {breakdown['rats_on_rocket_count']}")
    
    return "\n".join(lines)


def check_and_trigger_endgame(state: GameState, config: Config) -> Dict[str, Any] | None:
    """
    Check if endgame should trigger and finalize if so.
    
    检查是否应该触发终局，如果是则结束游戏。
    
    Returns:
        Game results if game ended, None otherwise
    """
    if state.game_over:
        return None
    
    # Check fourth rat trigger
    for player in state.players:
        if len(player.get_rats_on_rocket()) >= 4:
            return finalize_game(state, config, "fourth_rat_on_rocket")
    
    # Check eighth scoring marker trigger
    total_parts_built = sum(len(player.built_parts) for player in state.players)
    if total_parts_built >= 8:
        return finalize_game(state, config, "eighth_scoring_marker")
    
    return None


def get_current_standings(state: GameState) -> List[Tuple[str, str, int, int]]:
    """
    Get current game standings (not final scores).
    
    获取当前游戏排名（非最终得分）。
    
    Returns:
        List of (player_id, name, current_score, rats_on_rocket) tuples, sorted by score
    """
    standings = []
    
    for player in state.players:
        standings.append((
            player.player_id,
            player.name,
            player.score,
            len(player.get_rats_on_rocket())
        ))
    
    # Sort by current score (descending), then by rats on rocket (descending)
    standings.sort(key=lambda x: (x[2], x[3]), reverse=True)
    
    return standings