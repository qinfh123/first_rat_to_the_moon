"""
Unit tests for shop and build action validation.

Tests shop purchase, theft, and rocket building validation.
"""

import pytest
from first_rat_local.core.rules import ActionValidator
from first_rat_local.core.models import GameState, Board, Space, Player, Rat, Inventory, Rocket
from first_rat_local.core.actions import create_buy_action, create_steal_action, create_build_rocket_action, create_donate_cheese_action
from first_rat_local.core.config import Config
from first_rat_local.core.enums import Color, SpaceKind, Resource, RocketPart


class TestShopValidation:
    """Test cases for shop action validation."""
    
    def create_test_game_state(self) -> GameState:
        """Create a test game state with shops."""
        # Create board with shops
        spaces = [
            Space(0, 0, Color.GREEN, SpaceKind.START),
            Space(1, 1, Color.YELLOW, SpaceKind.SHOP_MOLE),
            Space(2, 2, Color.RED, SpaceKind.SHOP_FROG),
            Space(3, 3, Color.BLUE, SpaceKind.SHOP_CROW),
            Space(4, 4, Color.GREEN, SpaceKind.RESOURCE)
        ]
        
        board = Board(spaces=spaces, start_index=0, launch_index=4)
        
        # Create player with resources
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
        
        # Give player some resources
        player1.inv.add(Resource.TIN_CAN, 3)
        player1.inv.add(Resource.SODA, 2)
        player1.inv.add(Resource.CHEESE, 4)
        
        return GameState(
            board=board,
            players=[player1],
            rocket=Rocket(),
            current_player=0
        )
    
    def test_valid_mole_shop_purchase(self):
        """Test valid mole shop capacity purchase."""
        state = self.create_test_game_state()
        config = Config.default()
        validator = ActionValidator(config)
        
        action = create_buy_action(SpaceKind.SHOP_MOLE, "capacity", "r1")
        is_valid, error, derived = validator.validate(state, action, "p1")
        
        assert is_valid is True
        assert error is None
        assert derived["shop_kind"] == SpaceKind.SHOP_MOLE
        assert derived["item"] == "capacity"
        assert Resource.TIN_CAN in derived["price"]
    
    def test_valid_frog_shop_purchase(self):
        """Test valid frog shop x2 purchase."""
        state = self.create_test_game_state()
        config = Config.default()
        validator = ActionValidator(config)
        
        action = create_buy_action(SpaceKind.SHOP_FROG, "x2", "r2")
        is_valid, error, derived = validator.validate(state, action, "p1")
        
        assert is_valid is True
        assert error is None
        assert derived["shop_kind"] == SpaceKind.SHOP_FROG
        assert derived["item"] == "x2"
    
    def test_valid_crow_shop_purchase(self):
        """Test valid crow shop bottlecap purchase."""
        state = self.create_test_game_state()
        config = Config.default()
        validator = ActionValidator(config)
        
        action = create_buy_action(SpaceKind.SHOP_CROW, "bottlecap", "r3")
        is_valid, error, derived = validator.validate(state, action, "p1")
        
        assert is_valid is True
        assert error is None
        assert derived["shop_kind"] == SpaceKind.SHOP_CROW
        assert derived["item"] == "bottlecap"
    
    def test_invalid_insufficient_resources(self):
        """Test invalid purchase with insufficient resources."""
        state = self.create_test_game_state()
        config = Config.default()
        validator = ActionValidator(config)
        
        # Remove all tin cans
        state.players[0].inv.remove(Resource.TIN_CAN, 3)
        
        action = create_buy_action(SpaceKind.SHOP_MOLE, "capacity", "r1")
        is_valid, error, derived = validator.validate(state, action, "p1")
        
        assert is_valid is False
        assert "Not enough TIN_CAN" in error
    
    def test_invalid_rat_not_at_shop(self):
        """Test invalid purchase when rat is not at the shop."""
        state = self.create_test_game_state()
        config = Config.default()
        validator = ActionValidator(config)
        
        # Try to buy from mole shop with rat at frog shop
        action = create_buy_action(SpaceKind.SHOP_MOLE, "capacity", "r2")
        is_valid, error, derived = validator.validate(state, action, "p1")
        
        assert is_valid is False
        assert "is not at a SHOP_MOLE shop" in error
    
    def test_invalid_x2_already_active(self):
        """Test invalid frog shop purchase when x2 is already active."""
        state = self.create_test_game_state()
        config = Config.default()
        validator = ActionValidator(config)
        
        # Activate x2 effect
        state.players[0].inv.x2_active = True
        
        action = create_buy_action(SpaceKind.SHOP_FROG, "x2", "r2")
        is_valid, error, derived = validator.validate(state, action, "p1")
        
        assert is_valid is False
        assert "X2 effect is already active" in error
    
    def test_invalid_nonexistent_rat(self):
        """Test invalid purchase with nonexistent rat."""
        state = self.create_test_game_state()
        config = Config.default()
        validator = ActionValidator(config)
        
        action = create_buy_action(SpaceKind.SHOP_MOLE, "capacity", "nonexistent")
        is_valid, error, derived = validator.validate(state, action, "p1")
        
        assert is_valid is False
        assert "Rat nonexistent not found or not on board" in error


class TestStealValidation:
    """Test cases for steal action validation."""
    
    def create_test_game_state(self) -> GameState:
        """Create a test game state for stealing tests."""
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
                Rat("r2", "p1", 2)   # At frog shop
            ],
            inv=Inventory()
        )
        
        return GameState(
            board=board,
            players=[player1],
            rocket=Rocket(),
            current_player=0
        )
    
    def test_valid_steal_from_mole_shop(self):
        """Test valid theft from mole shop."""
        state = self.create_test_game_state()
        config = Config.default()
        validator = ActionValidator(config)
        
        action = create_steal_action(SpaceKind.SHOP_MOLE, "capacity", "r1")
        is_valid, error, derived = validator.validate(state, action, "p1")
        
        assert is_valid is True
        assert error is None
        assert derived["shop_kind"] == SpaceKind.SHOP_MOLE
        assert derived["target_item"] == "capacity"
        assert derived["thief_rat"].rat_id == "r1"
    
    def test_valid_steal_from_frog_shop(self):
        """Test valid theft from frog shop."""
        state = self.create_test_game_state()
        config = Config.default()
        validator = ActionValidator(config)
        
        action = create_steal_action(SpaceKind.SHOP_FROG, "x2", "r2")
        is_valid, error, derived = validator.validate(state, action, "p1")
        
        assert is_valid is True
        assert error is None
        assert derived["target_item"] == "x2"
    
    def test_invalid_steal_x2_already_active(self):
        """Test invalid theft when x2 is already active."""
        state = self.create_test_game_state()
        config = Config.default()
        validator = ActionValidator(config)
        
        state.players[0].inv.x2_active = True
        
        action = create_steal_action(SpaceKind.SHOP_FROG, "x2", "r2")
        is_valid, error, derived = validator.validate(state, action, "p1")
        
        assert is_valid is False
        assert "X2 effect is already active" in error
    
    def test_invalid_steal_wrong_item(self):
        """Test invalid theft of wrong item from shop."""
        state = self.create_test_game_state()
        config = Config.default()
        validator = ActionValidator(config)
        
        # Try to steal x2 from mole shop (should be capacity)
        action = create_steal_action(SpaceKind.SHOP_MOLE, "x2", "r1")
        is_valid, error, derived = validator.validate(state, action, "p1")
        
        assert is_valid is False
        assert "Cannot steal x2 from SHOP_MOLE" in error


class TestBuildValidation:
    """Test cases for rocket building validation."""
    
    def create_test_game_state(self) -> GameState:
        """Create a test game state for building tests."""
        board = Board([Space(0, 0, Color.GREEN, SpaceKind.START)], 0, 0)
        
        player1 = Player(
            player_id="p1",
            name="Player 1",
            rats=[Rat("r1", "p1", 0)],
            inv=Inventory(capacity=10)
        )
        
        # Give player resources for building
        player1.inv.add(Resource.TIN_CAN, 5)
        player1.inv.add(Resource.CHEESE, 3)
        player1.inv.add(Resource.SODA, 3)
        player1.inv.add(Resource.LIGHTBULB, 2)
        
        return GameState(
            board=board,
            players=[player1],
            rocket=Rocket(),
            current_player=0
        )
    
    def test_valid_build_nose(self):
        """Test valid nose building."""
        state = self.create_test_game_state()
        config = Config.default()
        validator = ActionValidator(config)
        
        action = create_build_rocket_action(RocketPart.NOSE)
        is_valid, error, derived = validator.validate(state, action, "p1")
        
        assert is_valid is True
        assert error is None
        assert derived["part"] == RocketPart.NOSE
        assert Resource.TIN_CAN in derived["cost"]
        assert Resource.CHEESE in derived["cost"]
        assert derived["immediate_points"] > 0
    
    def test_valid_build_engine(self):
        """Test valid engine building."""
        state = self.create_test_game_state()
        config = Config.default()
        validator = ActionValidator(config)
        
        action = create_build_rocket_action(RocketPart.ENGINE)
        is_valid, error, derived = validator.validate(state, action, "p1")
        
        assert is_valid is True
        assert error is None
        assert derived["part"] == RocketPart.ENGINE
        assert Resource.TIN_CAN in derived["cost"]
        assert Resource.LIGHTBULB in derived["cost"]
    
    def test_invalid_build_insufficient_resources(self):
        """Test invalid building with insufficient resources."""
        state = self.create_test_game_state()
        config = Config.default()
        validator = ActionValidator(config)
        
        # Remove all tin cans
        state.players[0].inv.remove(Resource.TIN_CAN, 5)
        
        action = create_build_rocket_action(RocketPart.NOSE)
        is_valid, error, derived = validator.validate(state, action, "p1")
        
        assert is_valid is False
        assert "Not enough TIN_CAN" in error
    
    def test_invalid_build_already_built(self):
        """Test invalid building when part is already built."""
        state = self.create_test_game_state()
        config = Config.default()
        validator = ActionValidator(config)
        
        # Mark nose as already built
        state.rocket.build_part(RocketPart.NOSE, "other_player")
        
        action = create_build_rocket_action(RocketPart.NOSE)
        is_valid, error, derived = validator.validate(state, action, "p1")
        
        assert is_valid is False
        assert "Rocket part NOSE is already built" in error


class TestDonateValidation:
    """Test cases for cheese donation validation."""
    
    def create_test_game_state(self) -> GameState:
        """Create a test game state for donation tests."""
        board = Board([Space(0, 0, Color.GREEN, SpaceKind.START)], 0, 0)
        
        player1 = Player(
            player_id="p1",
            name="Player 1",
            rats=[Rat("r1", "p1", 0)],
            inv=Inventory()
        )
        
        player1.inv.add(Resource.CHEESE, 5)
        
        return GameState(
            board=board,
            players=[player1],
            rocket=Rocket(),
            current_player=0
        )
    
    def test_valid_donate_cheese(self):
        """Test valid cheese donation."""
        state = self.create_test_game_state()
        config = Config.default()
        validator = ActionValidator(config)
        
        action = create_donate_cheese_action(3)
        is_valid, error, derived = validator.validate(state, action, "p1")
        
        assert is_valid is True
        assert error is None
        assert derived["amount"] == 3
        assert derived["points"] > 0
    
    def test_invalid_donate_insufficient_cheese(self):
        """Test invalid donation with insufficient cheese."""
        state = self.create_test_game_state()
        config = Config.default()
        validator = ActionValidator(config)
        
        # Remove most cheese
        state.players[0].inv.remove(Resource.CHEESE, 4)
        
        action = create_donate_cheese_action(3)
        is_valid, error, derived = validator.validate(state, action, "p1")
        
        assert is_valid is False
        assert "Not enough cheese" in error
    
    def test_invalid_donate_invalid_amount(self):
        """Test invalid donation with invalid amount."""
        state = self.create_test_game_state()
        config = Config.default()
        validator = ActionValidator(config)
        
        # Try to donate 5 cheese (not in valid amounts)
        action = create_donate_cheese_action(5)
        is_valid, error, derived = validator.validate(state, action, "p1")
        
        assert is_valid is False
        assert "Invalid donation amount 5" in error