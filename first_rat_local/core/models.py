"""
Core data models for First Rat game.

This module defines all the data structures used in the game engine.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from collections import defaultdict
from .enums import Color, Resource, SpaceKind, RocketPart


@dataclass
class Space:
    """
    Represents a single space on the game board.
    
    棋盘上的单个格子，包含位置、颜色、类型和特殊属性。
    """
    space_id: int
    index: int                    # 在棋盘上的位置索引，越大越靠近发射台
    color: Color                  # 格子颜色
    kind: SpaceKind              # 格子类型
    payload: Dict[str, Any] = field(default_factory=dict)  # 格子特殊属性


@dataclass
class Rat:
    """
    Represents a player's rat on the board.
    
    玩家的老鼠，包含位置和状态信息。
    """
    rat_id: str                  # 老鼠唯一标识
    owner_id: str                # 所属玩家ID
    space_index: int             # 当前所在格子索引
    on_rocket: bool = False      # 是否已登船


@dataclass
class Inventory:
    """
    Represents a player's resource inventory.
    
    玩家的资源背包，管理资源存储和容量。
    """
    capacity: int = 3                                                    # 背包容量
    res: Dict[Resource, int] = field(default_factory=lambda: defaultdict(int))  # 资源数量
    x2_active: bool = False                                             # 青蛙店X2效果是否激活
    bottlecaps: int = 0                                                 # 瓶盖数量
    
    def can_add(self, amount: int) -> bool:
        """
        Check if the inventory can accommodate additional resources.
        
        检查背包是否能容纳更多资源。
        """
        current_total = sum(self.res.values())
        return current_total + amount <= self.capacity
    
    def add(self, resource: Resource, amount: int) -> None:
        """
        Add resources to the inventory.
        
        向背包添加资源。不检查容量限制，调用前应先用can_add检查。
        """
        if amount <= 0:
            return
        self.res[resource] += amount
    
    def remove(self, resource: Resource, amount: int) -> None:
        """
        Remove resources from the inventory.
        
        从背包移除资源。不检查是否有足够资源，调用前应先用has检查。
        """
        if amount <= 0:
            return
        self.res[resource] = max(0, self.res[resource] - amount)
        if self.res[resource] == 0:
            del self.res[resource]
    
    def has(self, resource: Resource, amount: int) -> bool:
        """
        Check if the inventory has enough of a specific resource.
        
        检查背包是否有足够的指定资源。
        """
        return self.res.get(resource, 0) >= amount
    
    def total_resources(self) -> int:
        """Get the total number of resources in inventory."""
        return sum(self.res.values())


@dataclass
class Player:
    """
    Represents a player in the game.
    
    游戏中的玩家，包含老鼠、背包、轨道进度和分数。
    """
    player_id: str                                                      # 玩家唯一标识
    name: str                                                          # 玩家姓名
    rats: List[Rat]                                                    # 玩家的老鼠列表
    inv: Inventory                                                     # 玩家背包
    tracks: Dict[str, int] = field(default_factory=lambda: defaultdict(int))  # 轨道进度
    score: int = 0                                                     # 当前分数
    built_parts: set[RocketPart] = field(default_factory=set)          # 已建造的火箭部件
    
    def get_rats_on_rocket(self) -> List[Rat]:
        """Get all rats that are currently on the rocket."""
        return [rat for rat in self.rats if rat.on_rocket]
    
    def get_rats_on_board(self) -> List[Rat]:
        """Get all rats that are still on the board (not on rocket)."""
        return [rat for rat in self.rats if not rat.on_rocket]
    
    def get_rats_in_inventory(self) -> List[Rat]:
        """Get all rats that are in the player's inventory (on rocket)."""
        return [rat for rat in self.rats if rat.on_rocket]


@dataclass
class Rocket:
    """
    Represents the shared rocket that players build.
    
    玩家共同建造的火箭，记录各部件的贡献者。
    """
    parts: Dict[RocketPart, Optional[str]] = field(
        default_factory=lambda: {part: None for part in RocketPart}
    )  # 火箭部件 -> 贡献者player_id的映射
    
    def is_part_built(self, part: RocketPart) -> bool:
        """Check if a rocket part has been built."""
        return self.parts[part] is not None
    
    def get_builder(self, part: RocketPart) -> Optional[str]:
        """Get the player ID who built a specific part."""
        return self.parts[part]
    
    def build_part(self, part: RocketPart, builder_id: str) -> None:
        """Mark a rocket part as built by a specific player."""
        self.parts[part] = builder_id


@dataclass
class Board:
    """
    Represents the game board with all spaces.
    
    游戏棋盘，包含所有格子和导航方法。
    """
    spaces: List[Space]                                    # 所有格子列表
    start_index: int                                       # 起点索引
    launch_index: int                                      # 发射台索引
    shortcuts: Optional[Dict[int, int]] = None             # 捷径映射 {from_index: to_index}
    
    def get_space(self, index: int) -> Space:
        """
        Get a space by its index.
        
        根据索引获取格子。
        """
        if not self.is_within_bounds(index):
            raise IndexError(f"Space index {index} is out of bounds")
        return self.spaces[index]
    
    def is_within_bounds(self, index: int) -> bool:
        """
        Check if an index is within the board bounds.
        
        检查索引是否在棋盘范围内。
        """
        return 0 <= index < len(self.spaces)
    
    def next_index(self, current_index: int, steps: int) -> int:
        """
        Calculate the next index after moving a number of steps.
        
        计算移动指定步数后的索引位置。处理边界和捷径。
        """
        if steps <= 0:
            return current_index
        
        target_index = current_index + steps
        
        # Handle shortcuts if they exist
        if self.shortcuts and target_index in self.shortcuts:
            target_index = self.shortcuts[target_index]
        
        # Clamp to board bounds
        return min(target_index, len(self.spaces) - 1)
    
    def is_occupied(self, index: int, rats: List[Rat]) -> bool:
        """
        Check if a space is occupied by any rat.
        
        检查指定格子是否被任何老鼠占据。
        """
        if not self.is_within_bounds(index):
            return False
        
        for rat in rats:
            if not rat.on_rocket and rat.space_index == index:
                return True
        return False
    
    def get_rats_at_space(self, index: int, rats: List[Rat]) -> List[Rat]:
        """Get all rats at a specific space index."""
        return [rat for rat in rats if not rat.on_rocket and rat.space_index == index]
    
    def get_all_rats_on_board(self, all_players: List['Player']) -> List[Rat]:
        """Get all rats from all players that are currently on the board."""
        all_rats = []
        for player in all_players:
            all_rats.extend(player.get_rats_on_board())
        return all_rats


@dataclass
class GameState:
    """
    Central game state containing all game information.
    
    游戏的中央状态，包含所有游戏信息，支持序列化和回放。
    """
    board: Board                                                       # 游戏棋盘
    players: List[Player]                                              # 所有玩家
    rocket: Rocket                                                     # 共享火箭
    current_player: int = 0                                            # 当前玩家索引
    round: int = 1                                                     # 当前回合数
    phase: str = "MAIN"                                                # 游戏阶段
    rng_seed: int = 0                                                  # 随机种子
    history: List[Dict[str, Any]] = field(default_factory=list)       # 动作和事件历史
    game_over: bool = False                                            # 游戏是否结束
    winner_ids: Optional[List[str]] = None                             # 获胜者ID列表
    
    def current_player_obj(self) -> Player:
        """
        Get the current player object.
        
        获取当前玩家对象。
        """
        if not self.players or self.current_player >= len(self.players):
            raise IndexError("Invalid current player index")
        return self.players[self.current_player]
    
    def next_player(self) -> None:
        """
        Advance to the next player.
        
        切换到下一个玩家。
        """
        if not self.players:
            return
        self.current_player = (self.current_player + 1) % len(self.players)
        if self.current_player == 0:  # Completed a full round
            self.round += 1
    
    def get_all_rats(self) -> List[Rat]:
        """Get all rats from all players."""
        all_rats = []
        for player in self.players:
            all_rats.extend(player.rats)
        return all_rats
    
    def get_player_by_id(self, player_id: str) -> Optional[Player]:
        """Get a player by their ID."""
        for player in self.players:
            if player.player_id == player_id:
                return player
        return None
    
    def apply(self, action: 'Action', actor_id: str, config: 'Config') -> List['DomainEvent']:
        """
        Apply an action to the game state using the rules engine.
        
        应用动作到游戏状态，使用规则引擎进行验证和效果解析。
        
        Returns:
            List of domain events generated by the action
            
        Raises:
            ValueError: If the action is invalid
        """
        from .rules import ActionValidator, EffectResolver
        from .actions import Action
        
        # Validate action
        validator = ActionValidator(config)
        is_valid, error_msg, derived_data = validator.validate(self, action, actor_id)
        
        if not is_valid:
            raise ValueError(f"Invalid action: {error_msg}")
        
        # Apply effects
        resolver = EffectResolver(config)
        events = resolver.apply(self, action, actor_id)
        
        # Log action and events to history
        history_entry = {
            "action": {
                "type": action.type.value,
                "payload": action.payload,
                "actor": actor_id
            },
            "events": [
                {
                    "type": event.type.value,
                    "payload": event.payload,
                    "actor": event.actor,
                    "timestamp": event.timestamp
                }
                for event in events
            ],
            "derived_data": derived_data
        }
        self.history.append(history_entry)
        
        # Check invariants after action
        self._check_invariants()
        
        return events
    
    def _check_invariants(self) -> None:
        """
        Check game state invariants to ensure consistency.
        
        检查游戏状态不变式以确保一致性。
        """
        for player in self.players:
            # Check inventory constraints
            if player.inv.total_resources() > player.inv.capacity:
                raise ValueError(f"Player {player.player_id} inventory exceeds capacity")
            
            # Check resource counts are non-negative
            for resource, amount in player.inv.res.items():
                if amount < 0:
                    raise ValueError(f"Player {player.player_id} has negative {resource.value}: {amount}")
            
            # Check score is non-negative
            if player.score < 0:
                raise ValueError(f"Player {player.player_id} has negative score: {player.score}")
            
            # Check rat positions are valid
            for rat in player.rats:
                if not rat.on_rocket and not self.board.is_within_bounds(rat.space_index):
                    raise ValueError(f"Rat {rat.rat_id} at invalid position: {rat.space_index}")
        
        # Check current player index is valid
        if self.current_player >= len(self.players):
            raise ValueError(f"Invalid current player index: {self.current_player}")
        
        # Check rocket parts consistency
        for part, builder_id in self.rocket.parts.items():
            if builder_id is not None:
                builder = self.get_player_by_id(builder_id)
                if builder is None:
                    raise ValueError(f"Rocket part {part.value} built by unknown player: {builder_id}")
                if part not in builder.built_parts:
                    raise ValueError(f"Player {builder_id} doesn't have {part.value} in built_parts")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize the game state to a dictionary.
        
        将游戏状态序列化为字典，用于保存和传输。
        """
        return {
            "board": {
                "spaces": [
                    {
                        "space_id": space.space_id,
                        "index": space.index,
                        "color": space.color.value,
                        "kind": space.kind.value,
                        "payload": space.payload
                    }
                    for space in self.board.spaces
                ],
                "start_index": self.board.start_index,
                "launch_index": self.board.launch_index,
                "shortcuts": self.board.shortcuts
            },
            "players": [
                {
                    "player_id": player.player_id,
                    "name": player.name,
                    "rats": [
                        {
                            "rat_id": rat.rat_id,
                            "owner_id": rat.owner_id,
                            "space_index": rat.space_index,
                            "on_rocket": rat.on_rocket
                        }
                        for rat in player.rats
                    ],
                    "inventory": {
                        "capacity": player.inv.capacity,
                        "resources": {res.value: amount for res, amount in player.inv.res.items()},
                        "x2_active": player.inv.x2_active,
                        "bottlecaps": player.inv.bottlecaps
                    },
                    "tracks": dict(player.tracks),
                    "score": player.score,
                    "built_parts": [part.value for part in player.built_parts]
                }
                for player in self.players
            ],
            "rocket": {
                "parts": {part.value: builder_id for part, builder_id in self.rocket.parts.items()}
            },
            "current_player": self.current_player,
            "round": self.round,
            "phase": self.phase,
            "rng_seed": self.rng_seed,
            "history": self.history,
            "game_over": self.game_over,
            "winner_ids": self.winner_ids
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GameState":
        """
        Deserialize a game state from a dictionary.
        
        从字典反序列化游戏状态。
        """
        # Reconstruct board
        spaces = []
        for space_data in data["board"]["spaces"]:
            space = Space(
                space_id=space_data["space_id"],
                index=space_data["index"],
                color=Color(space_data["color"]),
                kind=SpaceKind(space_data["kind"]),
                payload=space_data["payload"]
            )
            spaces.append(space)
        
        board = Board(
            spaces=spaces,
            start_index=data["board"]["start_index"],
            launch_index=data["board"]["launch_index"],
            shortcuts=data["board"]["shortcuts"]
        )
        
        # Reconstruct players
        players = []
        for player_data in data["players"]:
            # Reconstruct rats
            rats = []
            for rat_data in player_data["rats"]:
                rat = Rat(
                    rat_id=rat_data["rat_id"],
                    owner_id=rat_data["owner_id"],
                    space_index=rat_data["space_index"],
                    on_rocket=rat_data["on_rocket"]
                )
                rats.append(rat)
            
            # Reconstruct inventory
            inv_data = player_data["inventory"]
            inventory = Inventory(
                capacity=inv_data["capacity"],
                x2_active=inv_data["x2_active"],
                bottlecaps=inv_data["bottlecaps"]
            )
            # Restore resources
            for res_str, amount in inv_data["resources"].items():
                inventory.res[Resource(res_str)] = amount
            
            # Reconstruct player
            player = Player(
                player_id=player_data["player_id"],
                name=player_data["name"],
                rats=rats,
                inv=inventory,
                tracks=defaultdict(int, player_data["tracks"]),
                score=player_data["score"],
                built_parts={RocketPart(part_str) for part_str in player_data["built_parts"]}
            )
            players.append(player)
        
        # Reconstruct rocket
        rocket = Rocket()
        for part_str, builder_id in data["rocket"]["parts"].items():
            rocket.parts[RocketPart(part_str)] = builder_id
        
        # Create game state
        return cls(
            board=board,
            players=players,
            rocket=rocket,
            current_player=data["current_player"],
            round=data["round"],
            phase=data["phase"],
            rng_seed=data["rng_seed"],
            history=data["history"],
            game_over=data["game_over"],
            winner_ids=data["winner_ids"]
        )