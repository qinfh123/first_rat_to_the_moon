"""
Unit tests for GameState class.

Tests state serialization, player management, and core game state functionality.
"""

import pytest
from first_rat_local.core.models import GameState, Board, Space, Player, Rat, Inventory, Rocket
from first_rat_local.core.enums import Color, SpaceKind, Resource, RocketPart


class TestGameState:
    """Test cases for GameState serialization and player management."""
    
    def create_test_game_state(self) -> GameState:
        """Create a simple test game state."""
        # Create a simple board
        spaces = [
            Space(0, 0, Color.GREEN, SpaceKind.START),
            Space(1, 1, Color.YELLOW, SpaceKind.RESOURCE, {"resource": Resource.CHEESE, "amount": 1}),
            Space(2, 2, Color.BLUE, SpaceKind.LAUNCH_PAD)
        ]
        board = Board(spaces=spaces, start_index=0, launch_index=2)
        
        # Create players
        player1 = Player(
            player_id="p1",
            name="Player 1",
            rats=[
                Rat("r1", "p1", 0),
                Rat("r2", "p1", 1, on_rocket=True)
            ],
            inv=Inventory(capacity=4, bottlecaps=2)
        )
        player1.inv.add(Resource.CHEESE, 2)
        player1.inv.add(Resource.TIN_CAN, 1)
        player1.score = 10
        player1.built_parts.add(RocketPart.NOSE)
        
        player2 = Player(
            player_id="p2",
            name="Player 2",
            rats=[Rat("r3", "p2", 0)],
            inv=Inventory()
        )
        
        # Create rocket
        rocket = Rocket()
        rocket.build_part(RocketPart.NOSE, "p1")
        
        return GameState(
            board=board,
            players=[player1, player2],
            rocket=rocket,
            current_player=1,
            round=3,
            rng_seed=42,
            history=[{"action": "test", "events": []}]
        )
    
    def test_current_player_obj(self):
        """Test getting the current player object."""
        state = self.create_test_game_state()
        current = state.current_player_obj()
        assert current.player_id == "p2"
        assert current.name == "Player 2"
    
    def test_current_player_obj_invalid_index(self):
        """Test getting current player with invalid index."""
        state = self.create_test_game_state()
        state.current_player = 5  # Invalid index
        with pytest.raises(IndexError):
            state.current_player_obj()
    
    def test_next_player(self):
        """Test advancing to the next player."""
        state = self.create_test_game_state()
        assert state.current_player == 1
        assert state.round == 3
        
        state.next_player()  # Should go to player 0 and increment round
        assert state.current_player == 0
        assert state.round == 4
        
        state.next_player()  # Should go to player 1, same round
        assert state.current_player == 1
        assert state.round == 4
    
    def test_next_player_empty_players(self):
        """Test next_player with no players."""
        state = GameState(
            board=Board([], 0, 0),
            players=[],
            rocket=Rocket()
        )
        state.next_player()  # Should not crash
        assert state.current_player == 0
    
    def test_get_all_rats(self):
        """Test getting all rats from all players."""
        state = self.create_test_game_state()
        all_rats = state.get_all_rats()
        assert len(all_rats) == 3
        rat_ids = [rat.rat_id for rat in all_rats]
        assert "r1" in rat_ids
        assert "r2" in rat_ids
        assert "r3" in rat_ids
    
    def test_get_player_by_id(self):
        """Test getting a player by ID."""
        state = self.create_test_game_state()
        player = state.get_player_by_id("p1")
        assert player is not None
        assert player.name == "Player 1"
        
        player = state.get_player_by_id("nonexistent")
        assert player is None
    
    def test_to_dict_serialization(self):
        """Test serializing game state to dictionary."""
        state = self.create_test_game_state()
        data = state.to_dict()
        
        # Check basic structure
        assert "board" in data
        assert "players" in data
        assert "rocket" in data
        assert "current_player" in data
        assert "round" in data
        assert "history" in data
        
        # Check board serialization
        board_data = data["board"]
        assert len(board_data["spaces"]) == 3
        assert board_data["start_index"] == 0
        assert board_data["launch_index"] == 2
        
        # Check first space
        space0 = board_data["spaces"][0]
        assert space0["space_id"] == 0
        assert space0["color"] == "GREEN"
        assert space0["kind"] == "START"
        
        # Check players serialization
        players_data = data["players"]
        assert len(players_data) == 2
        
        player1_data = players_data[0]
        assert player1_data["player_id"] == "p1"
        assert player1_data["name"] == "Player 1"
        assert len(player1_data["rats"]) == 2
        assert player1_data["score"] == 10
        assert "NOSE" in player1_data["built_parts"]
        
        # Check inventory serialization
        inv_data = player1_data["inventory"]
        assert inv_data["capacity"] == 4
        assert inv_data["bottlecaps"] == 2
        assert inv_data["resources"]["CHEESE"] == 2
        assert inv_data["resources"]["TIN_CAN"] == 1
        
        # Check rocket serialization
        rocket_data = data["rocket"]
        assert rocket_data["parts"]["NOSE"] == "p1"
        assert rocket_data["parts"]["TANK"] is None
    
    def test_from_dict_deserialization(self):
        """Test deserializing game state from dictionary."""
        original_state = self.create_test_game_state()
        data = original_state.to_dict()
        restored_state = GameState.from_dict(data)
        
        # Check basic properties
        assert restored_state.current_player == original_state.current_player
        assert restored_state.round == original_state.round
        assert restored_state.rng_seed == original_state.rng_seed
        assert len(restored_state.history) == len(original_state.history)
        
        # Check board restoration
        assert len(restored_state.board.spaces) == len(original_state.board.spaces)
        assert restored_state.board.start_index == original_state.board.start_index
        assert restored_state.board.launch_index == original_state.board.launch_index
        
        # Check space restoration
        space0 = restored_state.board.spaces[0]
        assert space0.space_id == 0
        assert space0.color == Color.GREEN
        assert space0.kind == SpaceKind.START
        
        # Check players restoration
        assert len(restored_state.players) == 2
        player1 = restored_state.players[0]
        assert player1.player_id == "p1"
        assert player1.name == "Player 1"
        assert player1.score == 10
        assert RocketPart.NOSE in player1.built_parts
        
        # Check rats restoration
        assert len(player1.rats) == 2
        rat2 = next(rat for rat in player1.rats if rat.rat_id == "r2")
        assert rat2.on_rocket is True
        
        # Check inventory restoration
        assert player1.inv.capacity == 4
        assert player1.inv.bottlecaps == 2
        assert player1.inv.has(Resource.CHEESE, 2)
        assert player1.inv.has(Resource.TIN_CAN, 1)
        
        # Check rocket restoration
        assert restored_state.rocket.is_part_built(RocketPart.NOSE)
        assert restored_state.rocket.get_builder(RocketPart.NOSE) == "p1"
        assert not restored_state.rocket.is_part_built(RocketPart.TANK)
    
    def test_serialization_round_trip(self):
        """Test that serialization and deserialization are consistent."""
        original_state = self.create_test_game_state()
        
        # Serialize and deserialize
        data = original_state.to_dict()
        restored_state = GameState.from_dict(data)
        
        # Serialize again
        data2 = restored_state.to_dict()
        
        # The two serialized versions should be identical
        assert data == data2