"""
Configuration system for First Rat game.

This module centralizes all game parameters to make the system highly configurable.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List
from .enums import Color, Resource, SpaceKind, RocketPart


@dataclass
class Config:
    """
    Central configuration for all game parameters.
    
    This class provides a single source of truth for game rules, making it easy
    to modify game behavior without changing code.
    """
    
    # Board Layout - 60 spaces from START to LAUNCH_PAD
    board_layout: List[Dict[str, Any]] = field(default_factory=list)
    start_index: int = 0
    launch_index: int = 59
    
    # Player Settings
    starting_rats: int = 2          # 每玩家初始老鼠数量
    max_rats: int = 4               # 老鼠数量上限
    starting_inventory_capacity: int = 3  # 初始背包容量
    
    # Movement Rules
    single_rat_move_range: tuple[int, int] = (1, 5)    # 单鼠移动范围 1-5步
    multi_rat_move_range: tuple[int, int] = (1, 3)     # 多鼠移动范围 各1-3步
    max_rats_per_move: int = 4      # 单次移动最多老鼠数
    
    # Special Mechanics
    soda_x2_once: bool = True       # 青蛙店饮料一次性翻倍效果
    
    # Shop Prices - {resource: amount} format
    shop_prices: Dict[SpaceKind, Dict[Resource, int]] = field(default_factory=dict)
    
    # Steal Rules - what you gain and the punishment
    steal_rules: Dict[SpaceKind, Dict[str, Any]] = field(default_factory=dict)
    
    # Rocket Part Costs and Immediate Scoring
    rocket_part_costs: Dict[RocketPart, Dict[Resource, int]] = field(default_factory=dict)
    rocket_part_scores: Dict[RocketPart, int] = field(default_factory=dict)
    
    # Cheese Donation Rewards
    donate_rewards: Dict[int, int] = field(default_factory=dict)  # {amount: points}
    
    # Lightbulb Track Rewards
    lightbulb_track_rewards: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    
    # End Game Triggers
    endgame_triggers: Dict[str, Any] = field(default_factory=dict)
    
    # Scoring Rules for final calculation
    scoring_rules: Dict[str, Any] = field(default_factory=dict)
    
    # Random seed for reproducible games
    random_seed: int = 0
    
    @classmethod
    def default(cls) -> "Config":
        """Create a standard game configuration with default rules."""
        config = cls()
        
        # Set up default board layout (60 spaces)
        config.board_layout = config._create_default_board()
        
        # Shop prices
        config.shop_prices = {
            SpaceKind.SHOP_MOLE: {Resource.TIN_CAN: 2},      # 鼹鼠店：2罐头扩容
            SpaceKind.SHOP_FROG: {Resource.SODA: 2},         # 青蛙店：2苏打粉获得X2
            SpaceKind.SHOP_CROW: {Resource.CHEESE: 2},       # 乌鸦店：2奶酪获得瓶盖
        }
        
        # Steal rules - gain item but rat goes back to START
        config.steal_rules = {
            SpaceKind.SHOP_MOLE: {"gain": "capacity", "punishment": "send_home"},
            SpaceKind.SHOP_FROG: {"gain": "x2_active", "punishment": "send_home"},
            SpaceKind.SHOP_CROW: {"gain": "bottlecap", "punishment": "send_home"},
        }
        
        # Rocket part costs and immediate scores
        config.rocket_part_costs = {
            RocketPart.NOSE: {Resource.TIN_CAN: 3, Resource.CHEESE: 1},
            RocketPart.TANK: {Resource.TIN_CAN: 2, Resource.SODA: 2},
            RocketPart.ENGINE: {Resource.TIN_CAN: 4, Resource.LIGHTBULB: 1},
            RocketPart.FIN_A: {Resource.TIN_CAN: 1, Resource.SODA: 1},
            RocketPart.FIN_B: {Resource.TIN_CAN: 1, Resource.CHEESE: 2},
        }
        
        config.rocket_part_scores = {
            RocketPart.NOSE: 4,
            RocketPart.TANK: 3,
            RocketPart.ENGINE: 5,
            RocketPart.FIN_A: 2,
            RocketPart.FIN_B: 3,
        }
        
        # Cheese donation rewards
        config.donate_rewards = {
            1: 1,   # 1奶酪 = 1分
            2: 3,   # 2奶酪 = 3分
            3: 6,   # 3奶酪 = 6分
            4: 10,  # 4奶酪 = 10分
        }
        
        # Lightbulb track rewards (level: reward)
        config.lightbulb_track_rewards = {
            1: {"type": "immediate", "points": 1},
            2: {"type": "immediate", "points": 2},
            3: {"type": "immediate", "points": 3},
            4: {"type": "passive", "effect": "extra_resource"},
            5: {"type": "immediate", "points": 5},
        }
        
        # End game triggers
        config.endgame_triggers = {
            "fourth_rat_on_rocket": True,    # 第4只老鼠登船
            "eighth_scoring_marker": True,   # 第8个得分标记
        }
        
        # Final scoring rules
        config.scoring_rules = {
            "rocket_parts": True,           # 火箭部件分数
            "bottlecaps": 1,               # 每个瓶盖1分
            "donated_cheese": True,         # 捐赠奶酪分数
            "lightbulb_track": True,        # 灯泡轨道分数
            "remaining_resources": False,   # 剩余资源不计分
        }
        
        return config
    
    def _create_default_board(self) -> List[Dict[str, Any]]:
        """Create the default 60-space board layout."""
        spaces = []
        
        # START space (index 0)
        spaces.append({
            "space_id": 0,
            "index": 0,
            "color": Color.GREEN,
            "kind": SpaceKind.START,
            "payload": {}
        })
        
        # Define a pattern for the board - mix of resources, shops, and special spaces
        pattern = [
            # Spaces 1-10
            (Color.YELLOW, SpaceKind.RESOURCE, {"resource": Resource.CHEESE, "amount": 1}),
            (Color.RED, SpaceKind.RESOURCE, {"resource": Resource.TIN_CAN, "amount": 1}),
            (Color.BLUE, SpaceKind.SHOP_MOLE, {"price": {Resource.TIN_CAN: 2}, "capacity_gain": 1}),
            (Color.GREEN, SpaceKind.RESOURCE, {"resource": Resource.SODA, "amount": 1}),
            (Color.YELLOW, SpaceKind.LIGHTBULB_TRACK, {"track_gain": 1}),
            (Color.RED, SpaceKind.RESOURCE, {"resource": Resource.LIGHTBULB, "amount": 1}),
            (Color.BLUE, SpaceKind.RESOURCE, {"resource": Resource.CHEESE, "amount": 1}),
            (Color.GREEN, SpaceKind.SHOP_FROG, {"price": {Resource.SODA: 2}, "x2_once": True}),
            (Color.YELLOW, SpaceKind.RESOURCE, {"resource": Resource.TIN_CAN, "amount": 1}),
            (Color.RED, SpaceKind.RESOURCE, {"resource": Resource.SODA, "amount": 1}),
            
            # Spaces 11-20
            (Color.BLUE, SpaceKind.RESOURCE, {"resource": Resource.LIGHTBULB, "amount": 1}),
            (Color.GREEN, SpaceKind.SHOP_CROW, {"price": {Resource.CHEESE: 2}, "bottlecap_gain": 1}),
            (Color.YELLOW, SpaceKind.RESOURCE, {"resource": Resource.CHEESE, "amount": 1}),
            (Color.RED, SpaceKind.LIGHTBULB_TRACK, {"track_gain": 1}),
            (Color.BLUE, SpaceKind.RESOURCE, {"resource": Resource.TIN_CAN, "amount": 1}),
            (Color.GREEN, SpaceKind.RESOURCE, {"resource": Resource.SODA, "amount": 1}),
            (Color.YELLOW, SpaceKind.RESOURCE, {"resource": Resource.LIGHTBULB, "amount": 1}),
            (Color.RED, SpaceKind.SHOP_MOLE, {"price": {Resource.TIN_CAN: 2}, "capacity_gain": 1}),
            (Color.BLUE, SpaceKind.RESOURCE, {"resource": Resource.CHEESE, "amount": 1}),
            (Color.GREEN, SpaceKind.RESOURCE, {"resource": Resource.TIN_CAN, "amount": 1}),
            
            # Continue pattern for remaining spaces...
            # For brevity, I'll create a simpler repeating pattern
        ]
        
        # Create spaces 1-58 using the pattern
        for i in range(1, 59):
            pattern_index = (i - 1) % len(pattern)
            color, kind, payload = pattern[pattern_index]
            
            spaces.append({
                "space_id": i,
                "index": i,
                "color": color,
                "kind": kind,
                "payload": payload
            })
        
        # LAUNCH_PAD space (index 59)
        spaces.append({
            "space_id": 59,
            "index": 59,
            "color": Color.BLUE,
            "kind": SpaceKind.LAUNCH_PAD,
            "payload": {}
        })
        
        return spaces