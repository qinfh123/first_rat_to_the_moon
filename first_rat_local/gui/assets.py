"""
Asset management system for the GUI.

This module handles loading and managing game assets like images, sounds, etc.
资源管理系统，处理图像、音效等游戏资源的加载和管理。
"""

import os
import json
from typing import Dict, Tuple, Optional, Any
import pygame
from ..core.enums import Color, SpaceKind, Resource, RocketPart


class AssetManager:
    """
    Manages all game assets including images, coordinates, and configurations.
    
    管理所有游戏资源，包括图像、坐标和配置。
    """
    
    def __init__(self, assets_path: str = "assets"):
        self.assets_path = assets_path
        self.images: Dict[str, pygame.Surface] = {}
        self.coordinates: Dict[str, Tuple[int, int]] = {}
        self.config: Dict[str, Any] = {}
        
        # Initialize pygame if not already done
        if not pygame.get_init():
            pygame.init()
    
    def load_all_assets(self):
        """Load all game assets from the assets directory."""
        try:
            self.load_board_assets()
            self.load_piece_assets()
            self.load_ui_assets()
            self.load_coordinates()
            print("✓ 所有资源加载完成")
        except Exception as e:
            print(f"⚠️ 资源加载警告: {e}")
            self.create_placeholder_assets()
    
    def load_board_assets(self):
        """Load board-related assets."""
        # Background map
        bg_path = os.path.join(self.assets_path, "board", "background.png")
        if os.path.exists(bg_path):
            self.images["background"] = pygame.image.load(bg_path)
        
        # Space tiles
        spaces_dir = os.path.join(self.assets_path, "board", "spaces")
        if os.path.exists(spaces_dir):
            for filename in os.listdir(spaces_dir):
                if filename.endswith(('.png', '.jpg', '.jpeg')):
                    name = os.path.splitext(filename)[0]
                    path = os.path.join(spaces_dir, filename)
                    self.images[f"space_{name}"] = pygame.image.load(path)
    
    def load_piece_assets(self):
        """Load game piece assets (rats, resources, etc.)."""
        # Rat sprites
        rats_dir = os.path.join(self.assets_path, "pieces", "rats")
        if os.path.exists(rats_dir):
            for filename in os.listdir(rats_dir):
                if filename.endswith(('.png', '.jpg', '.jpeg')):
                    name = os.path.splitext(filename)[0]
                    path = os.path.join(rats_dir, filename)
                    self.images[f"rat_{name}"] = pygame.image.load(path)
        
        # Resource sprites
        resources_dir = os.path.join(self.assets_path, "pieces", "resources")
        if os.path.exists(resources_dir):
            for filename in os.listdir(resources_dir):
                if filename.endswith(('.png', '.jpg', '.jpeg')):
                    name = os.path.splitext(filename)[0]
                    path = os.path.join(resources_dir, filename)
                    self.images[f"resource_{name}"] = pygame.image.load(path)
        
        # Shop and item sprites
        shops_dir = os.path.join(self.assets_path, "pieces", "shops")
        if os.path.exists(shops_dir):
            for filename in os.listdir(shops_dir):
                if filename.endswith(('.png', '.jpg', '.jpeg')):
                    name = os.path.splitext(filename)[0]
                    path = os.path.join(shops_dir, filename)
                    self.images[f"shop_{name}"] = pygame.image.load(path)
    
    def load_ui_assets(self):
        """Load UI-related assets."""
        ui_dir = os.path.join(self.assets_path, "ui")
        if os.path.exists(ui_dir):
            for filename in os.listdir(ui_dir):
                if filename.endswith(('.png', '.jpg', '.jpeg')):
                    name = os.path.splitext(filename)[0]
                    path = os.path.join(ui_dir, filename)
                    self.images[f"ui_{name}"] = pygame.image.load(path)
    
    def load_coordinates(self):
        """Load space coordinates from JSON file."""
        coord_path = os.path.join(self.assets_path, "coordinates.json")
        if os.path.exists(coord_path):
            with open(coord_path, 'r', encoding='utf-8') as f:
                coord_data = json.load(f)
                self.coordinates = coord_data.get("spaces", {})
                self.config = coord_data.get("config", {})
    
    def create_placeholder_assets(self):
        """Create placeholder assets when real assets are not available."""
        print("🎨 创建占位符资源...")
        
        # Create colored rectangles as placeholders
        colors = {
            "background": (50, 100, 50),
            "space_start": (100, 255, 100),
            "space_launch": (255, 100, 100),
            "space_resource": (200, 200, 100),
            "space_shop_mole": (150, 100, 50),
            "space_shop_frog": (100, 150, 100),
            "space_shop_crow": (100, 100, 150),
            "space_track": (255, 255, 100),
        }
        
        # Create background
        self.images["background"] = pygame.Surface((1200, 800))
        self.images["background"].fill(colors["background"])
        
        # Create space tiles (60x60 pixels)
        for name, color in colors.items():
            if name.startswith("space_"):
                surface = pygame.Surface((60, 60))
                surface.fill(color)
                # Add border
                pygame.draw.rect(surface, (0, 0, 0), surface.get_rect(), 2)
                self.images[name] = surface
        
        # Create rat sprites (different colors for different players)
        rat_colors = [(255, 0, 0), (0, 0, 255), (0, 255, 0), (255, 255, 0)]
        for i, color in enumerate(rat_colors):
            surface = pygame.Surface((40, 40))
            surface.fill(color)
            pygame.draw.circle(surface, (0, 0, 0), (20, 20), 18, 2)
            self.images[f"rat_player_{i+1}"] = surface
        
        # Create resource sprites
        resource_colors = {
            "cheese": (255, 255, 0),
            "tin_can": (150, 150, 150),
            "soda": (100, 200, 255),
            "lightbulb": (255, 255, 200),
            "bottlecap": (200, 100, 50)
        }
        
        for name, color in resource_colors.items():
            surface = pygame.Surface((30, 30))
            surface.fill(color)
            pygame.draw.rect(surface, (0, 0, 0), surface.get_rect(), 1)
            self.images[f"resource_{name}"] = surface
        
        # Create default coordinates for a 10x6 grid
        self.create_default_coordinates()
    
    def create_default_coordinates(self):
        """Create default coordinate layout for spaces."""
        # Create a winding path layout
        self.coordinates = {}
        
        # Board dimensions
        board_x, board_y = 100, 100
        space_size = 70
        
        # Create a snake-like path
        positions = []
        
        # Row 1: left to right (0-9)
        for i in range(10):
            x = board_x + i * space_size
            y = board_y
            positions.append((x, y))
        
        # Row 2: right to left (10-19)
        for i in range(10):
            x = board_x + (9 - i) * space_size
            y = board_y + space_size
            positions.append((x, y))
        
        # Row 3: left to right (20-29)
        for i in range(10):
            x = board_x + i * space_size
            y = board_y + 2 * space_size
            positions.append((x, y))
        
        # Row 4: right to left (30-39)
        for i in range(10):
            x = board_x + (9 - i) * space_size
            y = board_y + 3 * space_size
            positions.append((x, y))
        
        # Row 5: left to right (40-49)
        for i in range(10):
            x = board_x + i * space_size
            y = board_y + 4 * space_size
            positions.append((x, y))
        
        # Row 6: right to left (50-59)
        for i in range(10):
            x = board_x + (9 - i) * space_size
            y = board_y + 5 * space_size
            positions.append((x, y))
        
        # Assign coordinates to spaces
        for i, (x, y) in enumerate(positions):
            self.coordinates[str(i)] = (x, y)
        
        # Configuration
        self.config = {
            "board_offset": (board_x, board_y),
            "space_size": space_size,
            "ui_panel_width": 300
        }
    
    def get_image(self, key: str) -> Optional[pygame.Surface]:
        """Get an image by key."""
        return self.images.get(key)
    
    def get_space_image(self, space_kind: SpaceKind) -> pygame.Surface:
        """Get the appropriate image for a space type."""
        kind_mapping = {
            SpaceKind.START: "space_start",
            SpaceKind.LAUNCH_PAD: "space_launch",
            SpaceKind.RESOURCE: "space_resource",
            SpaceKind.SHOP_MOLE: "space_shop_mole",
            SpaceKind.SHOP_FROG: "space_shop_frog",
            SpaceKind.SHOP_CROW: "space_shop_crow",
            SpaceKind.LIGHTBULB_TRACK: "space_track",
        }
        
        key = kind_mapping.get(space_kind, "space_resource")
        return self.images.get(key, self.images.get("space_resource"))
    
    def get_rat_image(self, player_index: int) -> pygame.Surface:
        """Get rat image for a specific player."""
        key = f"rat_player_{player_index + 1}"
        return self.images.get(key, self.images.get("rat_player_1"))
    
    def get_resource_image(self, resource: Resource) -> pygame.Surface:
        """Get image for a specific resource."""
        resource_mapping = {
            Resource.CHEESE: "resource_cheese",
            Resource.TIN_CAN: "resource_tin_can",
            Resource.SODA: "resource_soda",
            Resource.LIGHTBULB: "resource_lightbulb",
            Resource.BOTTLECAP: "resource_bottlecap",
        }
        
        key = resource_mapping.get(resource, "resource_cheese")
        return self.images.get(key, self.images.get("resource_cheese"))
    
    def get_space_coordinates(self, space_index: int) -> Tuple[int, int]:
        """Get coordinates for a space by index."""
        return self.coordinates.get(str(space_index), (0, 0))
    
    def save_coordinates_template(self):
        """Save a template coordinates file for manual editing."""
        template = {
            "config": {
                "board_offset": [100, 100],
                "space_size": 70,
                "ui_panel_width": 300,
                "window_size": [1200, 800]
            },
            "spaces": {}
        }
        
        # Add all 60 spaces with default positions
        for i in range(60):
            template["spaces"][str(i)] = [100 + (i % 10) * 70, 100 + (i // 10) * 70]
        
        # Save template
        os.makedirs(self.assets_path, exist_ok=True)
        template_path = os.path.join(self.assets_path, "coordinates_template.json")
        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)
        
        print(f"📄 坐标模板已保存到: {template_path}")
        print("你可以编辑这个文件来自定义格子位置，然后重命名为 coordinates.json")


# Global asset manager instance
asset_manager = AssetManager()