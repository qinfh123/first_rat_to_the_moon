"""
Rules engine for First Rat game.

This module implements action validation and effect resolution.
规则引擎，实现动作验证和效果解析。
"""

from typing import Any, Dict, List, Optional, Tuple
from .models import GameState, Player, Rat
from .actions import Action
from .config import Config
from .enums import ActionType, SpaceKind, Resource, RocketPart, Color
from .events import (
    DomainEvent, create_resource_gained_event, create_resource_spent_event,
    create_inventory_changed_event, create_on_rocket_event, create_new_rat_gained_event,
    create_score_changed_event, create_sent_home_event, create_turn_ended_event,
    create_shop_bought_event, create_shop_stolen_event, create_part_built_event,
    create_cheese_donated_event
)
from .scoring import check_and_trigger_endgame


class ActionValidator:
    """
    Validates player actions without modifying game state.
    
    验证玩家动作的合法性，不修改游戏状态。
    """
    
    def __init__(self, config: Config):
        self.config = config
    
    def validate(self, state: GameState, action: Action, actor_id: str) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Validate an action and return validation result.
        
        验证动作并返回验证结果。
        
        Returns:
            (is_valid, error_message, derived_data)
        """
        # Check if actor exists
        actor = state.get_player_by_id(actor_id)
        if actor is None:
            return False, f"Player {actor_id} not found", {}
        
        # Check if it's the actor's turn
        if state.current_player_obj().player_id != actor_id:
            return False, f"It's not {actor_id}'s turn", {}
        
        # Check if game is over
        if state.game_over:
            return False, "Game is already over", {}
        
        # Dispatch to specific validators
        validators = {
            ActionType.MOVE: self.validate_move,
            ActionType.BUY: self.validate_buy,
            ActionType.STEAL: self.validate_steal,
            ActionType.BUILD_ROCKET: self.validate_build,
            ActionType.DONATE_CHEESE: self.validate_donate,
            ActionType.END_TURN: self.validate_end_turn
        }
        
        validator = validators.get(action.type)
        if validator is None:
            return False, f"Unknown action type: {action.type}", {}
        
        return validator(state, action, actor_id)
    
    def validate_move(self, state: GameState, action: Action, actor_id: str) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Validate a move action.
        
        验证移动动作。
        """
        payload = action.payload
        moves = payload.get("moves", [])
        
        if not moves:
            return False, "No moves specified", {}
        
        actor = state.get_player_by_id(actor_id)
        board_rats = actor.get_rats_on_board()
        all_rats = state.board.get_all_rats_on_board(state.players)
        
        # Validate move count and step ranges
        if len(moves) == 1:
            # Single rat: 1-5 steps
            rat_id, steps = moves[0]
            if not (1 <= steps <= 5):
                return False, f"Single rat must move 1-5 steps, got {steps}", {}
        elif 2 <= len(moves) <= 4:
            # Multiple rats: each 1-3 steps
            for rat_id, steps in moves:
                if not (1 <= steps <= 3):
                    return False, f"Multiple rats must each move 1-3 steps, rat {rat_id} moves {steps}", {}
        else:
            return False, f"Must move 1 rat or 2-4 rats, got {len(moves)}", {}
        
        # Validate that all rats belong to the actor and are on board
        moving_rats = []
        for rat_id, steps in moves:
            rat = next((r for r in board_rats if r.rat_id == rat_id), None)
            if rat is None:
                return False, f"Rat {rat_id} not found or not on board", {}
            moving_rats.append((rat, steps))
        
        # Calculate landing positions and validate
        landing_positions = []
        landing_colors = []
        
        for rat, steps in moving_rats:
            new_index = state.board.next_index(rat.space_index, steps)
            landing_positions.append((rat.rat_id, new_index))
            
            # Get landing space color
            landing_space = state.board.get_space(new_index)
            landing_colors.append(landing_space.color)
        
        # Check color consistency - all rats must land on same color
        if len(set(landing_colors)) > 1:
            color_names = [color.value for color in landing_colors]
            return False, f"All rats must land on same color spaces, got: {color_names}", {}
        
        # Check for occupation conflicts
        for rat_id, new_index in landing_positions:
            # Check if space is occupied by any other rat (excluding the moving rats)
            occupying_rats = [r for r in all_rats if r.space_index == new_index and r.rat_id != rat_id]
            if occupying_rats:
                occupier = occupying_rats[0]
                return False, f"Space {new_index} is occupied by rat {occupier.rat_id}", {}
        
        # Check for conflicts between moving rats
        landing_indices = [pos[1] for pos in landing_positions]
        if len(set(landing_indices)) != len(landing_indices):
            return False, "Multiple rats cannot land on the same space", {}
        
        # Return derived data for effect resolution
        derived_data = {
            "landing_positions": landing_positions,
            "landing_color": landing_colors[0],
            "moving_rats": [(rat.rat_id, rat.space_index, steps) for rat, steps in moving_rats]
        }
        
        return True, None, derived_data
    
    def validate_buy(self, state: GameState, action: Action, actor_id: str) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Validate a buy action.
        
        验证购买动作。
        """
        payload = action.payload
        shop_kind = payload.get("shop_kind")
        item = payload.get("item")
        payer_rat_id = payload.get("payer_rat_id")
        
        if not all([shop_kind, item, payer_rat_id]):
            return False, "Missing required fields for buy action", {}
        
        actor = state.get_player_by_id(actor_id)
        
        # Find the paying rat
        payer_rat = next((r for r in actor.get_rats_on_board() if r.rat_id == payer_rat_id), None)
        if payer_rat is None:
            return False, f"Rat {payer_rat_id} not found or not on board", {}
        
        # Check if rat is at the correct shop
        rat_space = state.board.get_space(payer_rat.space_index)
        if rat_space.kind != shop_kind:
            return False, f"Rat {payer_rat_id} is not at a {shop_kind.value} shop", {}
        
        # Check if shop has the item and get price
        if shop_kind not in self.config.shop_prices:
            return False, f"No prices configured for {shop_kind.value}", {}
        
        price = self.config.shop_prices[shop_kind]
        
        # Validate item and check if player can afford it
        if shop_kind == SpaceKind.SHOP_MOLE and item == "capacity":
            # Check if player can afford capacity upgrade
            for resource, cost in price.items():
                if not actor.inv.has(resource, cost):
                    return False, f"Not enough {resource.value} (need {cost}, have {actor.inv.res.get(resource, 0)})", {}
        
        elif shop_kind == SpaceKind.SHOP_FROG and item == "x2":
            # Check if player can afford x2 effect and doesn't already have it
            if actor.inv.x2_active:
                return False, "X2 effect is already active", {}
            for resource, cost in price.items():
                if not actor.inv.has(resource, cost):
                    return False, f"Not enough {resource.value} (need {cost}, have {actor.inv.res.get(resource, 0)})", {}
        
        elif shop_kind == SpaceKind.SHOP_CROW and item == "bottlecap":
            # Check if player can afford bottlecap
            for resource, cost in price.items():
                if not actor.inv.has(resource, cost):
                    return False, f"Not enough {resource.value} (need {cost}, have {actor.inv.res.get(resource, 0)})", {}
        
        else:
            return False, f"Invalid item {item} for shop {shop_kind.value}", {}
        
        derived_data = {
            "shop_kind": shop_kind,
            "item": item,
            "price": price,
            "payer_rat": payer_rat
        }
        
        return True, None, derived_data
    
    def validate_steal(self, state: GameState, action: Action, actor_id: str) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Validate a steal action.
        
        验证偷窃动作。
        """
        payload = action.payload
        shop_kind = payload.get("shop_kind")
        target_item = payload.get("target_item")
        payer_rat_id = payload.get("payer_rat_id")
        
        if not all([shop_kind, target_item, payer_rat_id]):
            return False, "Missing required fields for steal action", {}
        
        actor = state.get_player_by_id(actor_id)
        
        # Find the stealing rat
        thief_rat = next((r for r in actor.get_rats_on_board() if r.rat_id == payer_rat_id), None)
        if thief_rat is None:
            return False, f"Rat {payer_rat_id} not found or not on board", {}
        
        # Check if rat is at the correct shop
        rat_space = state.board.get_space(thief_rat.space_index)
        if rat_space.kind != shop_kind:
            return False, f"Rat {payer_rat_id} is not at a {shop_kind.value} shop", {}
        
        # Check if shop supports stealing
        if shop_kind not in self.config.steal_rules:
            return False, f"Cannot steal from {shop_kind.value}", {}
        
        # Validate target item
        valid_items = {
            SpaceKind.SHOP_MOLE: ["capacity"],
            SpaceKind.SHOP_FROG: ["x2"],
            SpaceKind.SHOP_CROW: ["bottlecap"]
        }
        
        if target_item not in valid_items.get(shop_kind, []):
            return False, f"Cannot steal {target_item} from {shop_kind.value}", {}
        
        # Check specific constraints
        if shop_kind == SpaceKind.SHOP_FROG and target_item == "x2":
            if actor.inv.x2_active:
                return False, "X2 effect is already active", {}
        
        derived_data = {
            "shop_kind": shop_kind,
            "target_item": target_item,
            "thief_rat": thief_rat,
            "steal_rules": self.config.steal_rules[shop_kind]
        }
        
        return True, None, derived_data
    
    def validate_build(self, state: GameState, action: Action, actor_id: str) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Validate a build rocket action.
        
        验证建造火箭动作。
        """
        payload = action.payload
        part = payload.get("part")
        
        if part is None:
            return False, "No rocket part specified", {}
        
        if not isinstance(part, RocketPart):
            return False, f"Invalid rocket part: {part}", {}
        
        # Check if part is already built
        if state.rocket.is_part_built(part):
            builder = state.rocket.get_builder(part)
            return False, f"Rocket part {part.value} is already built by {builder}", {}
        
        # Check if player has required resources
        if part not in self.config.rocket_part_costs:
            return False, f"No cost configured for rocket part {part.value}", {}
        
        actor = state.get_player_by_id(actor_id)
        required_resources = self.config.rocket_part_costs[part]
        
        for resource, cost in required_resources.items():
            if not actor.inv.has(resource, cost):
                return False, f"Not enough {resource.value} (need {cost}, have {actor.inv.res.get(resource, 0)})", {}
        
        derived_data = {
            "part": part,
            "cost": required_resources,
            "immediate_points": self.config.rocket_part_scores.get(part, 0)
        }
        
        return True, None, derived_data
    
    def validate_donate(self, state: GameState, action: Action, actor_id: str) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Validate a donate cheese action.
        
        验证捐赠奶酪动作。
        """
        payload = action.payload
        amount = payload.get("amount")
        
        if amount is None:
            return False, "No donation amount specified", {}
        
        if not isinstance(amount, int) or amount < 1:
            return False, f"Invalid donation amount: {amount}", {}
        
        # Check if amount is in valid range
        if amount not in self.config.donate_rewards:
            valid_amounts = list(self.config.donate_rewards.keys())
            return False, f"Invalid donation amount {amount}, valid amounts: {valid_amounts}", {}
        
        # Check if player has enough cheese
        actor = state.get_player_by_id(actor_id)
        if not actor.inv.has(Resource.CHEESE, amount):
            return False, f"Not enough cheese (need {amount}, have {actor.inv.res.get(Resource.CHEESE, 0)})", {}
        
        derived_data = {
            "amount": amount,
            "points": self.config.donate_rewards[amount]
        }
        
        return True, None, derived_data
    
    def validate_end_turn(self, state: GameState, action: Action, actor_id: str) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Validate an end turn action.
        
        验证结束回合动作。
        """
        # End turn is always valid (no special conditions)
        return True, None, {}


class EffectResolver:
    """
    Resolves action effects and modifies game state.
    
    解析动作效果并修改游戏状态。
    """
    
    def __init__(self, config: Config):
        self.config = config
    
    def apply(self, state: GameState, action: Action, actor_id: str) -> List[DomainEvent]:
        """
        Apply action effects to game state and return events.
        
        将动作效果应用到游戏状态并返回事件列表。
        """
        # Dispatch to specific resolvers
        resolvers = {
            ActionType.MOVE: self.resolve_move,
            ActionType.BUY: self.resolve_buy,
            ActionType.STEAL: self.resolve_steal,
            ActionType.BUILD_ROCKET: self.resolve_build,
            ActionType.DONATE_CHEESE: self.resolve_donate,
            ActionType.END_TURN: self.resolve_end_turn
        }
        
        resolver = resolvers.get(action.type)
        if resolver is None:
            return []
        
        # Apply action effects
        events = resolver(state, action, actor_id)
        
        # Check for end game conditions after action
        endgame_results = check_and_trigger_endgame(state, self.config)
        if endgame_results is not None:
            # Game ended, add the game ended event to our events
            events.append(endgame_results["game_ended_event"])
        
        return events
    
    def resolve_move(self, state: GameState, action: Action, actor_id: str) -> List[DomainEvent]:
        """
        Resolve move action effects.
        
        解析移动动作效果。
        """
        events = []
        payload = action.payload
        moves = payload.get("moves", [])
        
        actor = state.get_player_by_id(actor_id)
        
        # Move each rat and process landing effects
        for rat_id, steps in moves:
            rat = next(r for r in actor.get_rats_on_board() if r.rat_id == rat_id)
            old_index = rat.space_index
            new_index = state.board.next_index(old_index, steps)
            
            # Update rat position
            rat.space_index = new_index
            
            # Process landing space effects
            landing_space = state.board.get_space(new_index)
            space_events = self._process_space_effects(state, actor, rat, landing_space)
            events.extend(space_events)
        
        return events
    
    def _process_space_effects(self, state: GameState, actor: Player, rat: Rat, space) -> List[DomainEvent]:
        """
        Process effects of landing on a specific space.
        
        处理落在特定格子上的效果。
        """
        events = []
        
        if space.kind == SpaceKind.RESOURCE:
            # Gain resources from resource spaces
            resource_type = Resource(space.payload.get("resource"))
            base_amount = space.payload.get("amount", 1)
            
            # Apply x2 effect if active
            actual_amount = base_amount
            if actor.inv.x2_active:
                actual_amount *= 2
                actor.inv.x2_active = False  # Consume x2 effect
                events.append(create_inventory_changed_event(actor.player_id, x2_consumed=True))
            
            # Check if inventory has space
            if actor.inv.can_add(actual_amount):
                actor.inv.add(resource_type, actual_amount)
                events.append(create_resource_gained_event(
                    actor.player_id, resource_type, actual_amount, "space"
                ))
            else:
                # Inventory full - gain what we can
                available_space = actor.inv.capacity - actor.inv.total_resources()
                if available_space > 0:
                    actor.inv.add(resource_type, available_space)
                    events.append(create_resource_gained_event(
                        actor.player_id, resource_type, available_space, "space"
                    ))
        
        elif space.kind == SpaceKind.LIGHTBULB_TRACK:
            # Advance lightbulb track
            track_gain = space.payload.get("track_gain", 1)
            actor.tracks["lightbulb"] += track_gain
            
            # Check for track rewards
            new_level = actor.tracks["lightbulb"]
            if new_level in self.config.lightbulb_track_rewards:
                reward = self.config.lightbulb_track_rewards[new_level]
                if reward["type"] == "immediate":
                    points = reward["points"]
                    actor.score += points
                    events.append(create_score_changed_event(
                        actor.player_id, points, f"lightbulb_track_level_{new_level}", actor.score
                    ))
        
        elif space.kind == SpaceKind.LAUNCH_PAD:
            # Handle rocket boarding
            if not rat.on_rocket:
                rat.on_rocket = True
                events.append(create_on_rocket_event(actor.player_id, rat.rat_id))
                
                # Spawn new rat if player hasn't reached max
                if len(actor.rats) < self.config.max_rats:
                    new_rat_id = f"{actor.player_id}_rat_{len(actor.rats) + 1}"
                    new_rat = Rat(new_rat_id, actor.player_id, state.board.start_index)
                    actor.rats.append(new_rat)
                    events.append(create_new_rat_gained_event(actor.player_id, new_rat_id))
        
        return events
    
    def resolve_buy(self, state: GameState, action: Action, actor_id: str) -> List[DomainEvent]:
        """
        Resolve buy action effects.
        
        解析购买动作效果。
        """
        events = []
        payload = action.payload
        shop_kind = payload.get("shop_kind")
        item = payload.get("item")
        
        actor = state.get_player_by_id(actor_id)
        price = self.config.shop_prices[shop_kind]
        
        # Spend resources
        for resource, cost in price.items():
            actor.inv.remove(resource, cost)
            events.append(create_resource_spent_event(actor.player_id, resource, cost, f"buy_{item}"))
        
        # Apply shop effects
        if shop_kind == SpaceKind.SHOP_MOLE and item == "capacity":
            actor.inv.capacity += 1
            events.append(create_inventory_changed_event(actor.player_id, capacity_change=1))
        
        elif shop_kind == SpaceKind.SHOP_FROG and item == "x2":
            actor.inv.x2_active = True
            events.append(create_inventory_changed_event(actor.player_id, x2_activated=True))
        
        elif shop_kind == SpaceKind.SHOP_CROW and item == "bottlecap":
            actor.inv.bottlecaps += 1
            events.append(create_inventory_changed_event(actor.player_id))
        
        return events
    
    def resolve_steal(self, state: GameState, action: Action, actor_id: str) -> List[DomainEvent]:
        """
        Resolve steal action effects.
        
        解析偷窃动作效果。
        """
        events = []
        payload = action.payload
        shop_kind = payload.get("shop_kind")
        target_item = payload.get("target_item")
        payer_rat_id = payload.get("payer_rat_id")
        
        actor = state.get_player_by_id(actor_id)
        thief_rat = next(r for r in actor.get_rats_on_board() if r.rat_id == payer_rat_id)
        
        # Apply theft effects (gain item)
        if shop_kind == SpaceKind.SHOP_MOLE and target_item == "capacity":
            actor.inv.capacity += 1
            events.append(create_inventory_changed_event(actor.player_id, capacity_change=1))
        
        elif shop_kind == SpaceKind.SHOP_FROG and target_item == "x2":
            actor.inv.x2_active = True
            events.append(create_inventory_changed_event(actor.player_id, x2_activated=True))
        
        elif shop_kind == SpaceKind.SHOP_CROW and target_item == "bottlecap":
            actor.inv.bottlecaps += 1
            events.append(create_inventory_changed_event(actor.player_id))
        
        # Apply punishment (send rat home)
        thief_rat.space_index = state.board.start_index
        events.append(create_sent_home_event(actor.player_id, thief_rat.rat_id, "theft"))
        
        return events
    
    def resolve_build(self, state: GameState, action: Action, actor_id: str) -> List[DomainEvent]:
        """
        Resolve build rocket action effects.
        
        解析建造火箭动作效果。
        """
        events = []
        payload = action.payload
        part = payload.get("part")
        
        actor = state.get_player_by_id(actor_id)
        cost = self.config.rocket_part_costs[part]
        immediate_points = self.config.rocket_part_scores.get(part, 0)
        
        # Spend resources
        for resource, amount in cost.items():
            actor.inv.remove(resource, amount)
            events.append(create_resource_spent_event(actor.player_id, resource, amount, f"build_{part.value}"))
        
        # Build the part
        state.rocket.build_part(part, actor.player_id)
        actor.built_parts.add(part)
        
        # Gain immediate points
        if immediate_points > 0:
            actor.score += immediate_points
            events.append(create_score_changed_event(
                actor.player_id, immediate_points, f"build_{part.value}", actor.score
            ))
        
        return events
    
    def resolve_donate(self, state: GameState, action: Action, actor_id: str) -> List[DomainEvent]:
        """
        Resolve donate cheese action effects.
        
        解析捐赠奶酪动作效果。
        """
        events = []
        payload = action.payload
        amount = payload.get("amount")
        
        actor = state.get_player_by_id(actor_id)
        points = self.config.donate_rewards[amount]
        
        # Spend cheese
        actor.inv.remove(Resource.CHEESE, amount)
        events.append(create_resource_spent_event(actor.player_id, Resource.CHEESE, amount, "donation"))
        
        # Gain points
        actor.score += points
        events.append(create_score_changed_event(
            actor.player_id, points, f"donate_{amount}_cheese", actor.score
        ))
        
        return events
    
    def resolve_end_turn(self, state: GameState, action: Action, actor_id: str) -> List[DomainEvent]:
        """
        Resolve end turn action effects.
        
        解析结束回合动作效果。
        """
        events = []
        
        # Create turn ended event
        events.append(create_turn_ended_event(actor_id, state.round))
        
        # Advance to next player
        state.next_player()
        
        return events