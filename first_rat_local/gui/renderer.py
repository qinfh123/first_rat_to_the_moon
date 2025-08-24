"""
Game renderer for the GUI.

This module handles rendering the game state to the screen.
游戏渲染器，处理游戏状态到屏幕的渲染。
"""

from typing import List, Tuple, Optional, Dict
import pygame
import math
import os
from ..core.models import GameState, Player, Rat
from ..core.enums import Color, SpaceKind, Resource, RocketPart
from .assets import asset_manager


class RatElement:
    """
    表示一个可点击的老鼠元素
    Represents a clickable rat element
    """
    
    def __init__(self, rat: Rat, player_idx: int, x: int, y: int, width: int = 25, height: int = 25):
        self.rat = rat
        self.player_idx = player_idx
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x, y, width, height)
        self.is_selected = False
        self.is_hovered = False
    
    def update_position(self, x: int, y: int):
        """更新老鼠位置"""
        self.x = x
        self.y = y
        self.rect.x = x
        self.rect.y = y
    
    def contains_point(self, pos: Tuple[int, int]) -> bool:
        """检查点是否在老鼠元素内"""
        return self.rect.collidepoint(pos)
    
    def get_center(self) -> Tuple[int, int]:
        """获取老鼠中心点"""
        return (self.x + self.width // 2, self.y + self.height // 2)


class GameRenderer:
    """
    Handles rendering the game state to a pygame surface.
    
    处理游戏状态到pygame表面的渲染。
    """
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font_large = self._get_chinese_font(36)
        self.font_medium = self._get_chinese_font(24)
        self.font_small = self._get_chinese_font(18)
        self.font_tiny = self._get_chinese_font(14)
        
        # Colors
        self.colors = {
            'white': (255, 255, 255),
            'black': (0, 0, 0),
            'gray': (128, 128, 128),
            'light_gray': (200, 200, 200),
            'dark_gray': (64, 64, 64),
            'red': (255, 0, 0),
            'green': (0, 255, 0),
            'blue': (0, 0, 255),
            'yellow': (255, 255, 0),
            'orange': (255, 165, 0),
            'purple': (128, 0, 128),
            'cyan': (0, 255, 255),
            'panel_bg': (240, 240, 240),
            'panel_border': (100, 100, 100),
            'header_bg': (200, 200, 255),
            'success': (0, 200, 0),
            'warning': (255, 165, 0),
            'error': (255, 0, 0),
        }
        
        # Layout configuration
        self.ui_panel_width = asset_manager.config.get('ui_panel_width', 300)
        self.board_area = pygame.Rect(0, 0, 
                                     self.screen.get_width() - self.ui_panel_width, 
                                     self.screen.get_height())
        self.ui_area = pygame.Rect(self.screen.get_width() - self.ui_panel_width, 0,
                                  self.ui_panel_width, self.screen.get_height())
        
        # Animation time for effects
        self.animation_time = 0.0
        
        # Rat elements for click detection
        self.rat_elements: Dict[str, RatElement] = {}
    
    def _get_chinese_font(self, size: int) -> pygame.font.Font:
        """获取支持中文的字体"""
        # 尝试常见的中文字体
        chinese_fonts = [
            # Windows 中文字体
            "C:/Windows/Fonts/msyh.ttc",      # 微软雅黑
            "C:/Windows/Fonts/simsun.ttc",    # 宋体
            "C:/Windows/Fonts/simhei.ttf",    # 黑体
            "C:/Windows/Fonts/simkai.ttf",    # 楷体
            # macOS 中文字体
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            # Linux 中文字体
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        ]
        
        # 尝试加载中文字体
        for font_path in chinese_fonts:
            try:
                if os.path.exists(font_path):
                    return pygame.font.Font(font_path, size)
            except:
                continue
        
        # 如果没有找到中文字体，尝试系统默认字体
        try:
            # 获取系统字体列表
            system_fonts = pygame.font.get_fonts()
            
            # 寻找可能支持中文的字体
            chinese_font_names = [
                'microsoftyaheui',  # 微软雅黑
                'simsun',           # 宋体
                'simhei',           # 黑体
                'pingfangsc',       # 苹方
                'notosanscjk',      # Noto Sans CJK
                'droidsansfallback', # Droid Sans Fallback
                'wqymicrohei',      # 文泉驿微米黑
            ]
            
            for font_name in chinese_font_names:
                if font_name in system_fonts:
                    return pygame.font.SysFont(font_name, size)
            
            # 尝试一些通用的字体名称
            generic_fonts = ['arial', 'helvetica', 'sans-serif']
            for font_name in generic_fonts:
                if font_name in system_fonts:
                    return pygame.font.SysFont(font_name, size)
                    
        except Exception as e:
            print(f"⚠️ 字体加载警告: {e}")
        
        # 最后回退到默认字体
        return pygame.font.Font(None, size)
    
    def update_animation(self, dt: float):
        """Update animation time."""
        self.animation_time += dt
    
    def render_game(self, state: GameState):
        """Render the complete game state."""
        # Clear screen
        self.screen.fill(self.colors['white'])
        
        # Render board area
        self.render_board(state)
        self.render_spaces(state)
        self.render_rats(state)
        self.render_board_effects(state)
        
        # Render UI panel
        self.render_ui_panel(state)
    
    def render_board(self, state: GameState):
        """Render the game board background."""
        # Draw board background
        background = asset_manager.get_image("background")
        if background:
            # Scale background to fit board area
            scaled_bg = pygame.transform.scale(background, 
                                             (self.board_area.width, self.board_area.height))
            self.screen.blit(scaled_bg, self.board_area.topleft)
        else:
            # Create gradient background
            for y in range(self.board_area.height):
                color_ratio = y / self.board_area.height
                r = int(50 + 50 * color_ratio)
                g = int(100 + 50 * color_ratio)
                b = int(50 + 100 * color_ratio)
                pygame.draw.line(self.screen, (r, g, b), 
                               (self.board_area.x, self.board_area.y + y),
                               (self.board_area.right, self.board_area.y + y))
    
    def render_spaces(self, state: GameState):
        """Render all board spaces."""
        for space in state.board.spaces:
            self.render_space(space, state)
    
    def render_space(self, space, state: GameState):
        """Render a single board space."""
        # Get space coordinates
        x, y = asset_manager.get_space_coordinates(space.index)
        
        # Get space image
        space_image = asset_manager.get_space_image(space.kind)
        if space_image:
            self.screen.blit(space_image, (x, y))
        else:
            # Draw colored rectangle based on space type
            color = self.get_space_color(space.kind)
            pygame.draw.rect(self.screen, color, (x, y, 60, 60))
            pygame.draw.rect(self.screen, self.colors['black'], (x, y, 60, 60), 2)
        
        # Render space number
        number_text = self.font_tiny.render(str(space.index), True, self.colors['black'])
        text_rect = number_text.get_rect()
        text_rect.topleft = (x + 2, y + 2)
        self.screen.blit(number_text, text_rect)
        
        # Render space-specific content
        self.render_space_content(space, x, y, state)
    
    def get_space_color(self, space_kind: SpaceKind) -> Tuple[int, int, int]:
        """Get color for space type."""
        color_map = {
            SpaceKind.START: self.colors['green'],
            SpaceKind.LAUNCH_PAD: self.colors['red'],
            SpaceKind.RESOURCE: self.colors['yellow'],
            SpaceKind.SHOP_MOLE: (139, 69, 19),  # Brown
            SpaceKind.SHOP_FROG: (34, 139, 34),  # Forest Green
            SpaceKind.SHOP_CROW: (25, 25, 112),  # Midnight Blue
            SpaceKind.LIGHTBULB_TRACK: self.colors['orange'],
        }
        return color_map.get(space_kind, self.colors['light_gray'])
    
    def render_space_content(self, space, x: int, y: int, state: GameState):
        """Render space-specific content."""
        # Render resources on resource spaces
        if space.kind == SpaceKind.RESOURCE and 'resource' in space.payload:
            resource_type = Resource(space.payload['resource'])
            resource_image = asset_manager.get_resource_image(resource_type)
            if resource_image:
                # Scale resource image to fit in corner
                small_resource = pygame.transform.scale(resource_image, (20, 20))
                self.screen.blit(small_resource, (x + 35, y + 35))
            else:
                # Draw colored circle for resource
                resource_color = self.get_resource_color(resource_type)
                pygame.draw.circle(self.screen, resource_color, (x + 45, y + 45), 8)
        
        # Render shop icons
        elif space.kind in [SpaceKind.SHOP_MOLE, SpaceKind.SHOP_FROG, SpaceKind.SHOP_CROW]:
            # Draw shop symbol
            symbol_color = self.colors['white']
            if space.kind == SpaceKind.SHOP_MOLE:
                # Draw pickaxe symbol
                pygame.draw.line(self.screen, symbol_color, (x+40, y+40), (x+50, y+50), 3)
            elif space.kind == SpaceKind.SHOP_FROG:
                # Draw X2 symbol
                text = self.font_tiny.render("X2", True, symbol_color)
                self.screen.blit(text, (x+40, y+40))
            elif space.kind == SpaceKind.SHOP_CROW:
                # Draw bottle cap symbol
                pygame.draw.circle(self.screen, symbol_color, (x+45, y+45), 6)
                pygame.draw.circle(self.screen, self.colors['black'], (x+45, y+45), 6, 1)
        
        # Render launch pad rocket
        elif space.kind == SpaceKind.LAUNCH_PAD:
            # Draw simple rocket symbol
            rocket_points = [
                (x+30, y+10),  # Top
                (x+25, y+50),  # Bottom left
                (x+35, y+50),  # Bottom right
            ]
            pygame.draw.polygon(self.screen, self.colors['white'], rocket_points)
            pygame.draw.polygon(self.screen, self.colors['black'], rocket_points, 2)
    
    def get_resource_color(self, resource: Resource) -> Tuple[int, int, int]:
        """Get color for resource type."""
        color_map = {
            Resource.CHEESE: self.colors['yellow'],
            Resource.TIN_CAN: self.colors['gray'],
            Resource.SODA: self.colors['cyan'],
            Resource.LIGHTBULB: (255, 255, 200),
            Resource.BOTTLECAP: (200, 100, 50),
        }
        return color_map.get(resource, self.colors['white'])
    
    def render_rats(self, state: GameState):
        """Render all rats on the board and update rat elements."""
        # Clear existing rat elements
        self.rat_elements.clear()
        
        # Group rats by position to handle overlapping
        rats_by_position = {}
        
        for player_idx, player in enumerate(state.players):
            for rat in player.get_rats_on_board():
                pos = rat.space_index
                if pos not in rats_by_position:
                    rats_by_position[pos] = []
                rats_by_position[pos].append((rat, player_idx))
        
        # Render rats at each position and create rat elements
        for space_index, rats_info in rats_by_position.items():
            space_x, space_y = asset_manager.get_space_coordinates(space_index)
            
            # Arrange multiple rats in a small grid
            for i, (rat, player_idx) in enumerate(rats_info):
                # Calculate position with better spacing for multiple rats
                if len(rats_info) == 1:
                    # Single rat - center it
                    offset_x = 17
                    offset_y = 17
                elif len(rats_info) == 2:
                    # Two rats - side by side
                    offset_x = 8 + (i % 2) * 20
                    offset_y = 17
                elif len(rats_info) <= 4:
                    # Up to 4 rats - 2x2 grid
                    offset_x = 8 + (i % 2) * 20
                    offset_y = 8 + (i // 2) * 20
                else:
                    # More than 4 rats - compact grid
                    offset_x = 5 + (i % 3) * 15
                    offset_y = 5 + (i // 3) * 15
                
                rat_x = space_x + offset_x
                rat_y = space_y + offset_y
                
                # Create rat element for click detection
                rat_element = RatElement(rat, player_idx, rat_x, rat_y)
                self.rat_elements[rat.rat_id] = rat_element
                
                # Render the rat
                self.render_rat_element(rat_element)
    
    def render_rat_element(self, rat_element: RatElement):
        """渲染老鼠元素"""
        rat_image = asset_manager.get_rat_image(rat_element.player_idx)
        if rat_image:
            # Scale rat image
            scaled_rat = pygame.transform.scale(rat_image, (rat_element.width, rat_element.height))
            self.screen.blit(scaled_rat, (rat_element.x, rat_element.y))
        else:
            # Draw colored circle for rat
            player_colors = [
                self.colors['red'],
                self.colors['blue'], 
                self.colors['green'],
                self.colors['yellow']
            ]
            color = player_colors[rat_element.player_idx % len(player_colors)]
            center_x, center_y = rat_element.get_center()
            pygame.draw.circle(self.screen, color, (center_x, center_y), 12)
            pygame.draw.circle(self.screen, self.colors['black'], (center_x, center_y), 12, 2)
        
        # Add rat ID text
        rat_text = self.font_tiny.render(rat_element.rat.rat_id[-1], True, self.colors['white'])
        text_rect = rat_text.get_rect()
        text_rect.center = rat_element.get_center()
        self.screen.blit(rat_text, text_rect)
        
        # Render selection highlight
        if rat_element.is_selected:
            center_x, center_y = rat_element.get_center()
            # Animated selection ring
            radius = int(18 + 3 * math.sin(self.animation_time * 4))
            pygame.draw.circle(self.screen, self.colors['red'], (center_x, center_y), radius, 3)
        
        # Render hover highlight
        if rat_element.is_hovered:
            center_x, center_y = rat_element.get_center()
            # Pulsing hover effect
            alpha = int(128 + 127 * math.sin(self.animation_time * 6))
            hover_surface = pygame.Surface((rat_element.width + 4, rat_element.height + 4))
            hover_surface.set_alpha(alpha)
            hover_surface.fill(self.colors['white'])
            self.screen.blit(hover_surface, (rat_element.x - 2, rat_element.y - 2))
    
    def render_rat(self, rat: Rat, player_idx: int, x: int, y: int):
        """Render a single rat."""
        rat_image = asset_manager.get_rat_image(player_idx)
        if rat_image:
            # Scale rat image
            scaled_rat = pygame.transform.scale(rat_image, (25, 25))
            self.screen.blit(scaled_rat, (x, y))
        else:
            # Draw colored circle for rat
            player_colors = [
                self.colors['red'],
                self.colors['blue'], 
                self.colors['green'],
                self.colors['yellow']
            ]
            color = player_colors[player_idx % len(player_colors)]
            pygame.draw.circle(self.screen, color, (x + 12, y + 12), 12)
            pygame.draw.circle(self.screen, self.colors['black'], (x + 12, y + 12), 12, 2)
        
        # Add rat ID text
        rat_text = self.font_tiny.render(rat.rat_id[-1], True, self.colors['white'])
        text_rect = rat_text.get_rect()
        text_rect.center = (x + 12, y + 12)
        self.screen.blit(rat_text, text_rect)
    
    def render_board_effects(self, state: GameState):
        """Render special effects on the board."""
        # Render path indicators for possible moves
        # This could show valid move paths for selected rats
        pass
    
    def render_planned_moves(self, planned_moves: List[Tuple[str, int]], state: GameState):
        """渲染计划中的移动"""
        if not planned_moves:
            return
        
        for i, (rat_id, target_space) in enumerate(planned_moves):
            # 找到老鼠当前位置
            current_player = state.current_player_obj()
            rat = next((r for r in current_player.get_rats_on_board() if r.rat_id == rat_id), None)
            
            if rat:
                # 获取起始和目标坐标
                start_x, start_y = asset_manager.get_space_coordinates(rat.space_index)
                target_x, target_y = asset_manager.get_space_coordinates(target_space)
                
                # 绘制移动箭头
                start_center = (start_x + 30, start_y + 30)
                target_center = (target_x + 30, target_y + 30)
                
                # 箭头颜色根据顺序变化
                colors = [(255, 100, 100), (100, 255, 100), (100, 100, 255)]
                arrow_color = colors[i % len(colors)]
                
                # 绘制箭头线
                pygame.draw.line(self.screen, arrow_color, start_center, target_center, 3)
                
                # 绘制箭头头部
                import math
                angle = math.atan2(target_center[1] - start_center[1], target_center[0] - start_center[0])
                arrow_length = 15
                arrow_angle = math.pi / 6
                
                # 箭头的两个边
                arrow_end1 = (
                    target_center[0] - arrow_length * math.cos(angle - arrow_angle),
                    target_center[1] - arrow_length * math.sin(angle - arrow_angle)
                )
                arrow_end2 = (
                    target_center[0] - arrow_length * math.cos(angle + arrow_angle),
                    target_center[1] - arrow_length * math.sin(angle + arrow_angle)
                )
                
                pygame.draw.line(self.screen, arrow_color, target_center, arrow_end1, 3)
                pygame.draw.line(self.screen, arrow_color, target_center, arrow_end2, 3)
                
                # 显示移动步数
                steps = target_space - rat.space_index
                step_text = self.font_small.render(str(steps), True, arrow_color)
                mid_x = (start_center[0] + target_center[0]) // 2
                mid_y = (start_center[1] + target_center[1]) // 2
                self.screen.blit(step_text, (mid_x - 5, mid_y - 10))
    
    def render_ui_panel(self, state: GameState):
        """Render the UI panel with game information."""
        # Draw panel background with gradient
        for y in range(self.ui_area.height):
            color_ratio = y / self.ui_area.height
            gray_value = int(240 - 40 * color_ratio)
            color = (gray_value, gray_value, gray_value)
            pygame.draw.line(self.screen, color,
                           (self.ui_area.x, self.ui_area.y + y),
                           (self.ui_area.right, self.ui_area.y + y))
        
        # Draw panel border
        pygame.draw.line(self.screen, self.colors['panel_border'], 
                        self.ui_area.topleft, self.ui_area.bottomleft, 3)
        
        y_offset = 10
        
        # Game info section
        y_offset = self.render_game_info_panel(state, y_offset)
        
        # Players section
        y_offset = self.render_players_panel(state, y_offset)
        
        # Rocket section
        y_offset = self.render_rocket_panel(state, y_offset)
        
        # Controls section
        self.render_controls_panel(y_offset)
    
    def render_section_header(self, title: str, y_offset: int) -> int:
        """Render a section header."""
        x = self.ui_area.x + 10
        
        # Header background
        header_rect = pygame.Rect(x - 5, y_offset - 2, self.ui_panel_width - 10, 30)
        pygame.draw.rect(self.screen, self.colors['header_bg'], header_rect)
        pygame.draw.rect(self.screen, self.colors['panel_border'], header_rect, 1)
        
        # Header text
        title_surface = self.font_medium.render(title, True, self.colors['black'])
        title_rect = title_surface.get_rect()
        title_rect.centerx = header_rect.centerx
        title_rect.centery = header_rect.centery
        self.screen.blit(title_surface, title_rect)
        
        return y_offset + 35
    
    def render_game_info_panel(self, state: GameState, y_offset: int) -> int:
        """Render game information section."""
        y_offset = self.render_section_header("游戏信息", y_offset)
        x = self.ui_area.x + 10
        
        # Game status
        if state.game_over:
            status_text = "🏁 游戏结束"
            status_color = self.colors['error']
        else:
            current_player = state.current_player_obj()
            status_text = f"👤 {current_player.name} 的回合"
            status_color = self.colors['success']
        
        status = self.font_small.render(status_text, True, status_color)
        self.screen.blit(status, (x, y_offset))
        y_offset += 25
        
        # Round info with progress bar
        round_text = f"🔄 回合: {state.round}"
        round_surface = self.font_small.render(round_text, True, self.colors['black'])
        self.screen.blit(round_surface, (x, y_offset))
        y_offset += 25
        
        # Game phase
        phase_text = f"📍 阶段: {state.phase}"
        phase_surface = self.font_small.render(phase_text, True, self.colors['black'])
        self.screen.blit(phase_surface, (x, y_offset))
        y_offset += 30
        
        return y_offset
    
    def render_players_panel(self, state: GameState, y_offset: int) -> int:
        """Render players information section."""
        y_offset = self.render_section_header("玩家状态", y_offset)
        x = self.ui_area.x + 10
        
        for i, player in enumerate(state.players):
            # Player header
            is_current = (i == state.current_player)
            name_color = self.colors['blue'] if is_current else self.colors['black']
            
            # Player indicator
            indicator = "👉 " if is_current else "   "
            player_text = f"{indicator}{player.name}"
            player_surface = self.font_small.render(player_text, True, name_color)
            self.screen.blit(player_surface, (x, y_offset))
            
            # Score
            score_text = f"🏆 {player.score}分"
            score_surface = self.font_tiny.render(score_text, True, self.colors['black'])
            self.screen.blit(score_surface, (x + 150, y_offset))
            y_offset += 20
            
            # Inventory with visual bar
            total_resources = player.inv.total_resources()
            capacity = player.inv.capacity
            
            # Inventory bar
            bar_width = self.ui_panel_width - 40
            bar_height = 8
            bar_rect = pygame.Rect(x, y_offset, bar_width, bar_height)
            
            # Background
            pygame.draw.rect(self.screen, self.colors['light_gray'], bar_rect)
            
            # Fill
            if capacity > 0:
                fill_width = int((total_resources / capacity) * bar_width)
                fill_rect = pygame.Rect(x, y_offset, fill_width, bar_height)
                fill_color = self.colors['success'] if total_resources < capacity else self.colors['warning']
                pygame.draw.rect(self.screen, fill_color, fill_rect)
            
            # Border
            pygame.draw.rect(self.screen, self.colors['black'], bar_rect, 1)
            
            # Text
            inv_text = f"🎒 {total_resources}/{capacity}"
            if player.inv.x2_active:
                inv_text += " [X2]"
            
            inv_surface = self.font_tiny.render(inv_text, True, self.colors['dark_gray'])
            self.screen.blit(inv_surface, (x, y_offset + 10))
            y_offset += 25
            
            # Rats info
            board_rats = len(player.get_rats_on_board())
            rocket_rats = len(player.get_rats_on_rocket())
            rats_text = f"🐭 棋盘:{board_rats} 🚀火箭:{rocket_rats}"
            
            rats_surface = self.font_tiny.render(rats_text, True, self.colors['dark_gray'])
            self.screen.blit(rats_surface, (x, y_offset))
            y_offset += 25
            
            # Separator line
            if i < len(state.players) - 1:
                pygame.draw.line(self.screen, self.colors['light_gray'],
                               (x, y_offset), (x + bar_width, y_offset))
                y_offset += 5
        
        return y_offset + 10
    
    def render_rocket_panel(self, state: GameState, y_offset: int) -> int:
        """Render rocket status section."""
        y_offset = self.render_section_header("🚀 火箭状态", y_offset)
        x = self.ui_area.x + 10
        
        # Rocket parts with visual progress
        built_count = 0
        total_parts = len(RocketPart)
        
        for part in RocketPart:
            if state.rocket.is_part_built(part):
                built_count += 1
                builder_id = state.rocket.get_builder(part)
                builder = state.get_player_by_id(builder_id)
                builder_name = builder.name if builder else "未知"
                
                part_text = f"✅ {self.get_part_name(part)} ({builder_name})"
                color = self.colors['success']
            else:
                part_text = f"⭕ {self.get_part_name(part)}"
                color = self.colors['gray']
            
            part_surface = self.font_tiny.render(part_text, True, color)
            self.screen.blit(part_surface, (x, y_offset))
            y_offset += 18
        
        # Progress bar
        y_offset += 5
        progress_bar_width = self.ui_panel_width - 40
        progress_bar_height = 12
        progress_rect = pygame.Rect(x, y_offset, progress_bar_width, progress_bar_height)
        
        # Background
        pygame.draw.rect(self.screen, self.colors['light_gray'], progress_rect)
        
        # Fill
        if total_parts > 0:
            fill_width = int((built_count / total_parts) * progress_bar_width)
            fill_rect = pygame.Rect(x, y_offset, fill_width, progress_bar_height)
            pygame.draw.rect(self.screen, self.colors['success'], fill_rect)
        
        # Border
        pygame.draw.rect(self.screen, self.colors['black'], progress_rect, 2)
        
        # Progress text
        progress_text = f"进度: {built_count}/{total_parts} ({int(built_count/total_parts*100)}%)"
        progress_surface = self.font_tiny.render(progress_text, True, self.colors['black'])
        text_rect = progress_surface.get_rect()
        text_rect.center = (progress_rect.centerx, progress_rect.centery)
        self.screen.blit(progress_surface, text_rect)
        
        y_offset += 25
        
        return y_offset
    
    def render_controls_panel(self, y_offset: int):
        """Render controls information."""
        y_offset = self.render_section_header("🎮 控制", y_offset)
        x = self.ui_area.x + 10
        
        # Controls
        controls = [
            "🖱️ 左键: 选择/移动",
            "🖱️ 右键: 查看详情", 
            "⌨️ 空格: 结束回合",
            "⌨️ R: 重置选择",
            "⌨️ H: 帮助",
            "⌨️ ESC: 菜单"
        ]
        
        for control in controls:
            control_surface = self.font_tiny.render(control, True, self.colors['dark_gray'])
            self.screen.blit(control_surface, (x, y_offset))
            y_offset += 16
    
    def get_part_name(self, part: RocketPart) -> str:
        """Get Chinese name for rocket part."""
        part_names = {
            RocketPart.NOSE: "火箭头",
            RocketPart.TANK: "燃料箱",
            RocketPart.ENGINE: "引擎",
            RocketPart.FIN_A: "尾翼A",
            RocketPart.FIN_B: "尾翼B",
        }
        return part_names.get(part, str(part.value))
    
    def get_space_at_position(self, pos: Tuple[int, int], state: GameState) -> Optional[int]:
        """Get space index at screen position."""
        for space in state.board.spaces:
            space_x, space_y = asset_manager.get_space_coordinates(space.index)
            space_rect = pygame.Rect(space_x, space_y, 60, 60)  # Assuming 60x60 space size
            if space_rect.collidepoint(pos):
                return space.index
        return None
    
    def get_rat_at_position(self, pos: Tuple[int, int]) -> Optional[str]:
        """获取指定位置的老鼠ID"""
        for rat_id, rat_element in self.rat_elements.items():
            if rat_element.contains_point(pos):
                return rat_id
        return None
    
    def get_rat_element(self, rat_id: str) -> Optional[RatElement]:
        """获取老鼠元素"""
        return self.rat_elements.get(rat_id)
    
    def set_rat_selected(self, rat_id: str, selected: bool):
        """设置老鼠选中状态"""
        rat_element = self.rat_elements.get(rat_id)
        if rat_element:
            rat_element.is_selected = selected
    
    def set_rat_hovered(self, rat_id: str, hovered: bool):
        """设置老鼠悬停状态"""
        rat_element = self.rat_elements.get(rat_id)
        if rat_element:
            rat_element.is_hovered = hovered
    
    def clear_all_rat_states(self):
        """清除所有老鼠的状态"""
        for rat_element in self.rat_elements.values():
            rat_element.is_selected = False
            rat_element.is_hovered = False