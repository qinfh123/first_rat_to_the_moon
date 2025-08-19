"""
Unit tests for Inventory class.

Tests resource management functionality including capacity limits and resource operations.
"""

import pytest
from first_rat_local.core.models import Inventory
from first_rat_local.core.enums import Resource


class TestInventory:
    """Test cases for Inventory resource management."""
    
    def test_initial_inventory(self):
        """Test inventory starts with correct defaults."""
        inv = Inventory()
        assert inv.capacity == 3
        assert inv.total_resources() == 0
        assert inv.x2_active is False
        assert inv.bottlecaps == 0
    
    def test_can_add_within_capacity(self):
        """Test can_add returns True when within capacity."""
        inv = Inventory(capacity=3)
        assert inv.can_add(1) is True
        assert inv.can_add(3) is True
        assert inv.can_add(4) is False
    
    def test_can_add_with_existing_resources(self):
        """Test can_add considers existing resources."""
        inv = Inventory(capacity=3)
        inv.add(Resource.CHEESE, 2)
        assert inv.can_add(1) is True
        assert inv.can_add(2) is False
    
    def test_add_resources(self):
        """Test adding resources to inventory."""
        inv = Inventory()
        inv.add(Resource.CHEESE, 2)
        assert inv.res[Resource.CHEESE] == 2
        assert inv.total_resources() == 2
    
    def test_add_zero_or_negative_resources(self):
        """Test adding zero or negative resources does nothing."""
        inv = Inventory()
        inv.add(Resource.CHEESE, 0)
        inv.add(Resource.TIN_CAN, -1)
        assert inv.total_resources() == 0
    
    def test_remove_resources(self):
        """Test removing resources from inventory."""
        inv = Inventory()
        inv.add(Resource.CHEESE, 3)
        inv.remove(Resource.CHEESE, 1)
        assert inv.res[Resource.CHEESE] == 2
        assert inv.total_resources() == 2
    
    def test_remove_all_resources(self):
        """Test removing all of a resource type cleans up the dict."""
        inv = Inventory()
        inv.add(Resource.CHEESE, 2)
        inv.remove(Resource.CHEESE, 2)
        assert Resource.CHEESE not in inv.res
        assert inv.total_resources() == 0
    
    def test_remove_more_than_available(self):
        """Test removing more resources than available clamps to zero."""
        inv = Inventory()
        inv.add(Resource.CHEESE, 2)
        inv.remove(Resource.CHEESE, 5)
        assert Resource.CHEESE not in inv.res
        assert inv.total_resources() == 0
    
    def test_remove_zero_or_negative(self):
        """Test removing zero or negative resources does nothing."""
        inv = Inventory()
        inv.add(Resource.CHEESE, 2)
        inv.remove(Resource.CHEESE, 0)
        inv.remove(Resource.CHEESE, -1)
        assert inv.res[Resource.CHEESE] == 2
    
    def test_has_sufficient_resources(self):
        """Test checking if inventory has sufficient resources."""
        inv = Inventory()
        inv.add(Resource.CHEESE, 3)
        assert inv.has(Resource.CHEESE, 1) is True
        assert inv.has(Resource.CHEESE, 3) is True
        assert inv.has(Resource.CHEESE, 4) is False
        assert inv.has(Resource.TIN_CAN, 1) is False
    
    def test_multiple_resource_types(self):
        """Test inventory with multiple resource types."""
        inv = Inventory(capacity=5)
        inv.add(Resource.CHEESE, 2)
        inv.add(Resource.TIN_CAN, 1)
        inv.add(Resource.SODA, 1)
        
        assert inv.total_resources() == 4
        assert inv.can_add(1) is True
        assert inv.can_add(2) is False
        assert inv.has(Resource.CHEESE, 2) is True
        assert inv.has(Resource.TIN_CAN, 1) is True
        assert inv.has(Resource.SODA, 1) is True