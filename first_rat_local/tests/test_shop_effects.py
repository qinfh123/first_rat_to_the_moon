"""
Unit tests for shop and build action effect resolution.

Tests shop purchase, theft, and rocket building effects.
"""

import pytest
from first_rat_local.core.rules import EffectResolver
from first_rat_local.core.models import GameState, Board, Space, Player, Rat, Inventory, Rocket
from first_rat_local.core.actions import (
    create_buy_action, create_steal_action, create_build_rocket_action, 
    create_donate_cheese_action, create_end_turn_action
)
from first_rat_local.core.config import Config
from first_rat_local.core.enums import Color, SpaceKind, Resource, RocketPart, DomainEventType


class TestShopEffects:
    """Test cases for shop action effect resolution."""
    
    def create_test_game_state(self) -> GameState:
        """Create a test game state with shops."""
        spaces = [
            Space(0, 0, Color.GREEN, SpaceKind.START),
            Space(1, 1, Color.YELLOW, SpaceKind.SHOP_MOLE),
            Space(2, 2, Color.RED, SpaceKind.SHOP_FROG),
            Space(3, 3, Color.BLUE, SpaceKind.SHOP_CROW)
        ]
        
        board = Board(spaces=spaces, start_index=0, launch_index=3)
        
        player1 = Player(
            player_id="p1",
            name="Player 1",
            rats=[
                Rat("r1", "p1", 1),  # At mole shop
                Rat("r2", "p1", 2),  # At frog shop
                Rat("r3", "p1", 3)   # At crow shop
            ],
            inv=Inventory(capacity=3)
        )
        
        # Give player resources
        player1.inv.add(Resource.TIN_CAN, 5)
        player1.inv.add(Resource.SODA, 3)
        player1.inv.add(Resource.CHEESE, 4)
        
        return GameState(
            board=board,
            players=[player1],
            rocket=Rocket(),
            current_player=0
        )
    
    def test_buy_mole_shop_capacity(self):
        """Test buying capacity from mole shop."""
        state = self.create_test_game_state()
        config = Config.default()
        resolver = EffectResolver(config)
        
        original_capacity = state.players[0].inv.capacity
        original_tin_cans = state.players[0].inv.res[Resource.TIN_CAN]
        
        action = create_buy_action(SpaceKind.SHOP_MOLE, "capacity", "r1")
        events = resolver.resolve_buy(state, action, "p1")
        
        # Check capacity increased
        player = state.players[0]
        assert player.inv.capacity == original_capacity + 1
        
        # Check resources spent (mole shop costs 2 tin cans)
        assert player.inv.res[Resource.TIN_CAN] == original_tin_cans - 2
        
        # Check events
        spent_events = [e for e in events if e.type == DomainEventType.RESOURCE_SPENT]
        inventory_events = [e for e in events if e.type == DomainEventType.INVENTORY_CHANGED]
        
        assert len(spent_events) == 1
        assert spent_events[0].payload["resource"] == "TIN_CAN"
        assert spent_events[0].payload["amount"] == 2
        assert spent_events[0].payload["purpose"] == "buy_capacity"
        
        assert len(inventory_events) == 1
        assert inventory_events[0].payload["capacity_change"] == 1
    
    def test_buy_frog_shop_x2(self):
        """Test buying x2 effect from frog shop."""
        state = self.create_test_game_state()
        config = Config.default()
        resolver = EffectResolver(config)
        
        original_soda = state.players[0].inv.res[Resource.SODA]
        
        action = create_buy_action(SpaceKind.SHOP_FROG, "x2", "r2")
        events = resolver.resolve_buy(state, action, "p1")
        
        # Check x2 effect activated
        player = state.players[0]
        assert player.inv.x2_active is True
        
        # Check resources spent (frog shop costs 2 soda)
        assert player.inv.res[Resource.SODA] == original_soda - 2
        
        # Check events
        spent_events = [e for e in events if e.type == DomainEventType.RESOURCE_SPENT]
        inventory_events = [e for e in events if e.type == DomainEventType.INVENTORY_CHANGED]
        
        assert len(spent_events) == 1
        assert spent_events[0].payload["resource"] == "SODA"
        assert spent_events[0].payload["amount"] == 2
        
        assert len(inventory_events) == 1
        assert inventory_events[0].payload["x2_activated"] is True
    
    def test_buy_crow_shop_bottlecap(self):
        """Test buying bottlecap from crow shop."""
        state = self.create_test_game_state()
        config = Config.default()
        resolver = EffectResolver(config)
        
        original_cheese = state.players[0].inv.res[Resource.CHEESE]
        original_bottlecaps = state.players[0].inv.bottlecaps
        
        action = create_buy_action(SpaceKind.SHOP_CROW, "bottlecap", "r3")
        events = resolver.resolve_buy(state, action, "p1")
        
        # Check bottlecap gained
        player = state.players[0]
        assert player.inv.bottlecaps == original_bottlecaps + 1
        
        # Check resources spent (crow shop costs 2 cheese)
        assert player.inv.res[Resource.CHEESE] == original_cheese - 2
        
        # Check events
        spent_events = [e for e in events if e.type == DomainEventType.RESOURCE_SPENT]
        inventory_events = [e for e in events if e.type == DomainEventType.INVENTORY_CHANGED]
        
        assert len(spent_events) == 1
        assert spent_events[0].payload["resource"] == "CHEESE"
        assert spent_events[0].payload["amount"] == 2
        
        assert len(inventory_events) == 1
    
    def test_steal_mole_shop_capacity(self):
        """Test stealing capacity from mole shop."""
        state = self.create_test_game_state()
        config = Config.default()
        resolver = EffectResolver(config)
        
        original_capacity = state.players[0].inv.capacity
        
        action = create_steal_action(SpaceKind.SHOP_MOLE, "capacity", "r1")
        events = resolver.resolve_steal(state, action, "p1")
        
        # Check capacity increased (no cost)
        player = state.players[0]
        assert player.inv.capacity == original_capacity + 1
        
        # Check rat sent home
        rat = next(r for r in player.rats if r.rat_id == "r1")
        assert rat.space_index == 0  # Start index
        
        # Check events
        inventory_events = [e for e in events if e.type == DomainEventType.INVENTORY_CHANGED]
        sent_home_events = [e for e in events if e.type == DomainEventType.SENT_HOME]
        
        assert len(inventory_events) == 1
        assert inventory_events[0].payload["capacity_change"] == 1
        
        assert len(sent_home_events) == 1
        assert sent_home_events[0].payload["rat_id"] == "r1"
        assert sent_home_events[0].payload["reason"] == "theft"
    
    def test_steal_frog_shop_x2(self):
        """Test stealing x2 effect from frog shop."""
        state = self.create_test_game_state()
        config = Config.default()
        resolver = EffectResolver(config)
        
        action = create_steal_action(SpaceKind.SHOP_FROG, "x2", "r2")
        events = resolver.resolve_steal(state, action, "p1")
        
        # Check x2 effect activated (no cost)
        player = state.players[0]
        assert player.inv.x2_active is True
        
        # Check rat sent home
        rat = next(r for r in player.rats if r.rat_id == "r2")
        assert rat.space_index == 0
        
        # Check events
        inventory_events = [e for e in events if e.type == DomainEventType.INVENTORY_CHANGED]
        sent_home_events = [e for e in events if e.type == DomainEventType.SENT_HOME]
        
        assert len(inventory_events) == 1
        assert inventory_events[0].payload["x2_activated"] is True
        
        assert len(sent_home_events) == 1
        assert sent_home_events[0].payload["rat_id"] == "r2"


class TestBuildEffects:
    """Test cases for rocket building effect resolution."""
    
    def create_test_game_state(self) -> GameState:
        """Create a test game state for building tests."""
        board = Board([Space(0, 0, Color.GREEN, SpaceKind.START)], 0, 0)
        
        player1 = Player(
            player_id="p1",
            name="Player 1",
            rats=[Rat("r1", "p1", 0)],
            inv=Inventory(capacity=10),
            score=10
        )
        
        # Give player resources for building
        player1.inv.add(Resource.TIN_CAN, 10)
        player1.inv.add(Resource.CHEESE, 5)
        player1.inv.add(Resource.SODA, 5)
        player1.inv.add(Resource.LIGHTBULB, 3)
        
        return GameState(
            board=board,
            players=[player1],
            rocket=Rocket(),
            current_player=0
        )
    
    def test_build_rocket_nose(self):
        """Test building rocket nose."""
        state = self.create_test_game_state()
        config = Config.default()
        resolver = EffectResolver(config)
        
        original_score = state.players[0].score
        original_tin_cans = state.players[0].inv.res[Resource.TIN_CAN]
        original_cheese = state.players[0].inv.res[Resource.CHEESE]
        
        action = create_build_rocket_action(RocketPart.NOSE)
        events = resolver.resolve_build(state, action, "p1")
        
        # Check part built
        assert state.rocket.is_part_built(RocketPart.NOSE)
        assert state.rocket.get_builder(RocketPart.NOSE) == "p1"
        
        # Check player's built parts updated
        player = state.players[0]
        assert RocketPart.NOSE in player.built_parts
        
        # Check resources spent (nose costs 3 tin cans + 1 cheese)
        assert player.inv.res[Resource.TIN_CAN] == original_tin_cans - 3
        assert player.inv.res[Resource.CHEESE] == original_cheese - 1
        
        # Check immediate points gained (nose gives 4 points)
        expected_score = original_score + 4
        assert player.score == expected_score
        
        # Check events
        spent_events = [e for e in events if e.type == DomainEventType.RESOURCE_SPENT]
        score_events = [e for e in events if e.type == DomainEventType.SCORE_CHANGED]
        
        assert len(spent_events) == 2  # TIN_CAN and CHEESE
        tin_can_event = next(e for e in spent_events if e.payload["resource"] == "TIN_CAN")
        cheese_event = next(e for e in spent_events if e.payload["resource"] == "CHEESE")
        
        assert tin_can_event.payload["amount"] == 3
        assert tin_can_event.payload["purpose"] == "build_NOSE"
        assert cheese_event.payload["amount"] == 1
        assert cheese_event.payload["purpose"] == "build_NOSE"
        
        assert len(score_events) == 1
        assert score_events[0].payload["points"] == 4
        assert score_events[0].payload["reason"] == "build_NOSE"
        assert score_events[0].payload["new_total"] == expected_score
    
    def test_build_rocket_engine(self):
        """Test building rocket engine."""
        state = self.create_test_game_state()
        config = Config.default()
        resolver = EffectResolver(config)
        
        original_tin_cans = state.players[0].inv.res[Resource.TIN_CAN]
        original_lightbulbs = state.players[0].inv.res[Resource.LIGHTBULB]
        
        action = create_build_rocket_action(RocketPart.ENGINE)
        events = resolver.resolve_build(state, action, "p1")
        
        # Check part built
        assert state.rocket.is_part_built(RocketPart.ENGINE)
        assert state.rocket.get_builder(RocketPart.ENGINE) == "p1"
        
        # Check resources spent (engine costs 4 tin cans + 1 lightbulb)
        player = state.players[0]
        assert player.inv.res[Resource.TIN_CAN] == original_tin_cans - 4
        assert player.inv.res[Resource.LIGHTBULB] == original_lightbulbs - 1
        
        # Check events
        spent_events = [e for e in events if e.type == DomainEventType.RESOURCE_SPENT]
        assert len(spent_events) == 2


class TestDonateEffects:
    """Test cases for cheese donation effect resolution."""
    
    def create_test_game_state(self) -> GameState:
        """Create a test game state for donation tests."""
        board = Board([Space(0, 0, Color.GREEN, SpaceKind.START)], 0, 0)
        
        player1 = Player(
            player_id="p1",
            name="Player 1",
            rats=[Rat("r1", "p1", 0)],
            inv=Inventory(),
            score=5
        )
        
        player1.inv.add(Resource.CHEESE, 10)
        
        return GameState(
            board=board,
            players=[player1],
            rocket=Rocket(),
            current_player=0
        )
    
    def test_donate_cheese_small_amount(self):
        """Test donating small amount of cheese."""
        state = self.create_test_game_state()
        config = Config.default()
        resolver = EffectResolver(config)
        
        original_score = state.players[0].score
        original_cheese = state.players[0].inv.res[Resource.CHEESE]
        
        action = create_donate_cheese_action(1)
        events = resolver.resolve_donate(state, action, "p1")
        
        # Check cheese spent
        player = state.players[0]
        assert player.inv.res[Resource.CHEESE] == original_cheese - 1
        
        # Check points gained (1 cheese = 1 point)
        expected_score = original_score + 1
        assert player.score == expected_score
        
        # Check events
        spent_events = [e for e in events if e.type == DomainEventType.RESOURCE_SPENT]
        score_events = [e for e in events if e.type == DomainEventType.SCORE_CHANGED]
        
        assert len(spent_events) == 1
        assert spent_events[0].payload["resource"] == "CHEESE"
        assert spent_events[0].payload["amount"] == 1
        assert spent_events[0].payload["purpose"] == "donation"
        
        assert len(score_events) == 1
        assert score_events[0].payload["points"] == 1
        assert score_events[0].payload["reason"] == "donate_1_cheese"
    
    def test_donate_cheese_large_amount(self):
        """Test donating large amount of cheese for better efficiency."""
        state = self.create_test_game_state()
        config = Config.default()
        resolver = EffectResolver(config)
        
        original_score = state.players[0].score
        
        action = create_donate_cheese_action(4)
        events = resolver.resolve_donate(state, action, "p1")
        
        # Check points gained (4 cheese = 10 points, better than 4x1=4 points)
        expected_score = original_score + 10
        player = state.players[0]
        assert player.score == expected_score
        
        # Check events
        score_events = [e for e in events if e.type == DomainEventType.SCORE_CHANGED]
        assert len(score_events) == 1
        assert score_events[0].payload["points"] == 10
        assert score_events[0].payload["reason"] == "donate_4_cheese"


class TestEndTurnEffects:
    """Test cases for end turn effect resolution."""
    
    def create_test_game_state(self) -> GameState:
        """Create a test game state for end turn tests."""
        board = Board([Space(0, 0, Color.GREEN, SpaceKind.START)], 0, 0)
        
        player1 = Player(player_id="p1", name="Player 1", rats=[Rat("r1", "p1", 0)], inv=Inventory())
        player2 = Player(player_id="p2", name="Player 2", rats=[Rat("r2", "p2", 0)], inv=Inventory())
        
        return GameState(
            board=board,
            players=[player1, player2],
            rocket=Rocket(),
            current_player=0,  # Player 1's turn
            round=2
        )
    
    def test_end_turn_advance_player(self):
        """Test ending turn advances to next player."""
        state = self.create_test_game_state()
        config = Config.default()
        resolver = EffectResolver(config)
        
        original_player = state.current_player
        original_round = state.round
        
        action = create_end_turn_action()
        events = resolver.resolve_end_turn(state, action, "p1")
        
        # Check player advanced
        assert state.current_player == 1  # Player 2's turn
        assert state.round == original_round  # Same round
        
        # Check events
        turn_events = [e for e in events if e.type == DomainEventType.TURN_ENDED]
        assert len(turn_events) == 1
        assert turn_events[0].payload["round_number"] == original_round
        assert turn_events[0].actor == "p1"
    
    def test_end_turn_advance_round(self):
        """Test ending turn advances round when last player ends turn."""
        state = self.create_test_game_state()
        state.current_player = 1  # Player 2's turn (last player)
        config = Config.default()
        resolver = EffectResolver(config)
        
        original_round = state.round
        
        action = create_end_turn_action()
        events = resolver.resolve_end_turn(state, action, "p2")
        
        # Check round advanced and back to player 1
        assert state.current_player == 0  # Back to player 1
        assert state.round == original_round + 1  # New round
        
        # Check events
        turn_events = [e for e in events if e.type == DomainEventType.TURN_ENDED]
        assert len(turn_events) == 1
        assert turn_events[0].actor == "p2"