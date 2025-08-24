"""
Main GUI application for First Rat game.

This module provides the graphical user interface using pygame.
主GUI应用程序，使用pygame提供图形用户界面。
"""

import sys
import os
import math
from typing import Optional, Tuple, List
import pygame
import time
from ..core.setup import new_game, create_demo_game
from ..core.config import Config
from ..core.models import GameState
from ..core.actions import create_move_action, create_end_turn_action
from ..core.events import DomainEvent
from .assets import asset_manager
from .renderer import GameRenderer


class FirstRatGUI:
    """
    Main GUI application class.
    
    主GUI应用程序类。
    """
    
    def __init__(self):
        # Initialize pygame
        pygame.init()
        pygame.mixer.init()  # Initialize sound mixer
        
        # Screen setup
        self.screen_width = 1200
        self.screen_height = 800
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("萌鼠登月 - First Rat to the Moon")
        
        # Set window icon if available
        try:
            icon = pygame.image.load("assets/ui/icons/rocket.png")
            pygame.display.set_icon(icon)
        except:
            pass
        
        # Game components
        self.clock = pygame.time.Clock()
        self.config = Config.default()
        self.game_state: Optional[GameState] = None
        self.renderer = GameRenderer(self.screen)
        
        # UI state
        self.selected_space: Optional[int] = None
        self.selected_rats: List[str] = []
        self.game_mode = "menu"  # "menu", "game", "game_over"
        self.recent_events: List[DomainEvent] = []
        
        # 新的移动状态管理
        self.move_state = "idle"  # "idle", "selecting", "confirming"
        self.planned_moves: List[Tuple[str, int]] = []  # [(rat_id, target_space), ...]
        self.current_selecting_rat: Optional[str] = None
        self.move_sequence_step = 0
        
        # 状态备份和回滚功能
        self.saved_positions: Optional[dict] = None  # 保存移动前的老鼠位置
        self.has_backup = False  # 是否有备份状态
        
        # 回合内移动限制
        self.moved_rats_this_turn: List[str] = []  # 本回合已移动的老鼠ID列表
        
        # Animation and visual effects
        self.animation_time = 0.0
        self.hover_space: Optional[int] = None
        self.show_help = False
        self.notification_text = ""
        self.notification_timer = 0.0
        self.last_action_time = 0.0
        
        # Sound effects
        self.sounds = {}
        self.load_sounds()
        
        # Load assets
        asset_manager.load_all_assets()
        
        # Fonts - 使用支持中文的字体
        self.font_large = self._get_chinese_font(48)
        self.font_medium = self._get_chinese_font(32)
        self.font_small = self._get_chinese_font(24)
        self.font_tiny = self._get_chinese_font(18)
        
        print("🎮 GUI初始化完成")    

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
    
    def load_sounds(self):
        """Load sound effects."""
        sound_files = {
            'click': 'assets/sounds/click.wav',
            'move': 'assets/sounds/move.wav',
            'error': 'assets/sounds/error.wav',
            'success': 'assets/sounds/success.wav',
            'end_turn': 'assets/sounds/end_turn.wav',
            'game_over': 'assets/sounds/game_over.wav'
        }
        
        for name, path in sound_files.items():
            try:
                self.sounds[name] = pygame.mixer.Sound(path)
            except:
                # Create placeholder sounds if files don't exist
                self.sounds[name] = None
    
    def play_sound(self, sound_name: str):
        """Play a sound effect."""
        if sound_name in self.sounds and self.sounds[sound_name]:
            try:
                self.sounds[sound_name].play()
            except:
                pass
    
    def show_notification(self, text: str, duration: float = 2.0):
        """Show a notification message."""
        self.notification_text = text
        self.notification_timer = duration 
   
    def run(self):
        """Main game loop."""
        running = True
        
        while running:
            dt = self.clock.tick(60) / 1000.0  # Delta time in seconds
            self.animation_time += dt
            
            if self.notification_timer > 0:
                self.notification_timer -= dt
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self.handle_event(event)
            
            # Update mouse hover
            self.update_mouse_hover()
            
            # Update game state
            self.update()
            
            # Render
            self.render()
            
        pygame.quit()
        sys.exit()
    
    def update_mouse_hover(self):
        """Update mouse hover effects."""
        if self.game_state and self.game_mode == "game":
            mouse_pos = pygame.mouse.get_pos()
            
            # Clear previous hover states
            self.renderer.clear_all_rat_states()
            for rat_id in self.selected_rats:
                self.renderer.set_rat_selected(rat_id, True)
            
            # Check for rat hover first (rats have priority over spaces)
            hovered_rat = self.renderer.get_rat_at_position(mouse_pos)
            if hovered_rat:
                self.renderer.set_rat_hovered(hovered_rat, True)
                self.hover_space = None
            else:
                # Check for space hover if no rat is hovered
                self.hover_space = self.renderer.get_space_at_position(mouse_pos, self.game_state)
    
    def handle_event(self, event: pygame.event.Event):
        """Handle pygame events."""
        if self.game_mode == "menu":
            self.handle_menu_event(event)
        elif self.game_mode == "game":
            self.handle_game_event(event)
        elif self.game_mode == "game_over":
            self.handle_game_over_event(event)
    
    def handle_menu_event(self, event: pygame.event.Event):
        """Handle events in menu mode."""
        if event.type == pygame.KEYDOWN:
            self.play_sound('click')
            if event.key == pygame.K_1:
                # New 2-player game
                self.start_new_game(2, ["玩家1", "玩家2"])
            elif event.key == pygame.K_2:
                # New 3-player game
                self.start_new_game(3, ["玩家1", "玩家2", "玩家3"])
            elif event.key == pygame.K_3:
                # New 4-player game
                self.start_new_game(4, ["玩家1", "玩家2", "玩家3", "玩家4"])
            elif event.key == pygame.K_d:
                # Demo game
                self.game_state = create_demo_game()
                self.game_mode = "game"
                
                # 为第一个玩家保存回合开始前的状态
                self.save_positions_backup()
                first_player = self.game_state.current_player_obj()
                print(f"💾 已为第一个玩家 {first_player.name} 保存回合开始前状态")
                
                self.show_notification("🎮 演示游戏开始")
                print("🎮 演示游戏开始")
            elif event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                pygame.quit()
                sys.exit()
    
    def handle_game_event(self, event: pygame.event.Event):
        """Handle events in game mode."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game_mode = "menu"
                self.game_state = None
                self.play_sound('click')
            elif event.key == pygame.K_SPACE:
                # End turn
                self.execute_end_turn()
            elif event.key == pygame.K_h:
                # Toggle help
                self.show_help = not self.show_help
                self.play_sound('click')
            elif event.key == pygame.K_r:
                # Reset selection and move state
                self.reset_move_state()
                self.show_notification("🔄 已重置移动状态")
                self.play_sound('click')
            elif event.key == pygame.K_RETURN:
                # Confirm current moves (Enter key)
                if self.move_state == "selecting" and self.planned_moves:
                    self.confirm_all_moves()
            elif event.key == pygame.K_c:
                # Cancel current move sequence
                if self.move_state != "idle":
                    self.cancel_move_sequence()
            elif event.key == pygame.K_u:
                # Undo/Rollback to saved positions (U key)
                if self.has_backup:
                    self.rollback_positions()
                else:
                    self.show_notification("❌ 没有可回滚的状态")
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                self.handle_left_click(event.pos)
            elif event.button == 3:  # Right click
                self.handle_right_click(event.pos)
    
    def handle_game_over_event(self, event: pygame.event.Event):
        """Handle events in game over mode."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_SPACE:
                self.game_mode = "menu"
                self.game_state = None
                self.play_sound('click')
    
    def handle_left_click(self, pos: Tuple[int, int]):
        """Handle left mouse click."""
        if not self.game_state or self.game_state.game_over:
            return
        
        self.play_sound('click')
        
        # Check if clicking on a rat first (rats have priority)
        clicked_rat_id = self.renderer.get_rat_at_position(pos)
        if clicked_rat_id:
            self.handle_rat_click(clicked_rat_id)
            return
        
        # If no rat clicked, check if clicking on a space
        space_index = self.renderer.get_space_at_position(pos, self.game_state)
        if space_index is not None:
            self.handle_space_click(space_index)
    
    def handle_rat_click(self, rat_id: str):
        """处理老鼠点击事件 - 新的按顺序选择逻辑"""
        current_player = self.game_state.current_player_obj()
        
        # 检查这只老鼠是否属于当前玩家
        rat = None
        for r in current_player.get_rats_on_board():
            if r.rat_id == rat_id:
                rat = r
                break
        
        if not rat:
            self.show_notification("❌ 这不是你的老鼠")
            return
        
        # 检查这只老鼠是否在本回合已经移动过
        if rat_id in self.moved_rats_this_turn:
            self.show_notification("❌ 这只老鼠本回合已经移动过")
            return
        
        # 检查是否已经在计划移动中
        for planned_rat_id, _ in self.planned_moves:
            if planned_rat_id == rat_id:
                self.show_notification("❌ 这只老鼠已经计划移动")
                return
        
        # 根据移动状态处理点击
        if self.move_state == "idle":
            # 开始新的移动序列
            self.start_rat_selection(rat_id)
        elif self.move_state == "selecting":
            # 检查是否可以选择更多老鼠
            if self.can_select_more_rats():
                self.start_rat_selection(rat_id)
            else:
                self.show_notification("❌ 当前无法选择更多老鼠")
        
        print(f"移动状态: {self.move_state}, 计划移动: {self.planned_moves}")
    
    def handle_right_click(self, pos: Tuple[int, int]):
        """Handle right mouse click (show info)."""
        if not self.game_state:
            return
        
        space_index = self.renderer.get_space_at_position(pos, self.game_state)
        if space_index is not None:
            self.show_space_info(space_index)
    
    def handle_space_click(self, space_index: int):
        """Handle clicking on a space - 新的移动逻辑."""
        if self.move_state == "selecting" and self.current_selecting_rat:
            # 当前正在为某只老鼠选择目标位置
            self.set_rat_target(self.current_selecting_rat, space_index)
        elif self.selected_rats:
            # 兼容旧的移动逻辑
            self.attempt_move_to_space(space_index)
        else:
            # 没有选中老鼠，显示空间信息
            self.show_space_info(space_index)
        
        self.selected_space = space_index  
  
    # ===== 状态备份和回滚功能 =====
    
    def save_positions_backup(self):
        """保存当前所有老鼠的位置状态"""
        if not self.game_state:
            return
        
        self.saved_positions = {}
        print('开始备份')
        # 保存所有玩家的老鼠位置
        for player in self.game_state.players:
            player_positions = {}
            
            # 保存棋盘上的老鼠位置
            for rat in player.get_rats_on_board():
                player_positions[rat.rat_id] = {
                    'space_index': rat.space_index,
                    'location': 'board'
                }
            
            # 保存火箭上的老鼠
            for rat in player.get_rats_on_rocket():
                player_positions[rat.rat_id] = {
                    'space_index': None,
                    'location': 'rocket'
                }
            
            # 保存玩家库存中的老鼠 (如果有这个方法的话)
            if hasattr(player, 'get_rats_in_inventory'):
                for rat in player.get_rats_in_inventory():
                    player_positions[rat.rat_id] = {
                        'space_index': None,
                        'location': 'inventory'
                    }
            
            self.saved_positions[player.player_id] = player_positions
        print(f"💾 已保存位置备份: {self.saved_positions}")
        self.has_backup = True
        print(f"💾 已保存位置备份: {len(self.saved_positions)} 个玩家的状态")
        
    def rollback_positions(self):
        """回滚到保存的位置状态"""
        if not self.has_backup or not self.saved_positions or not self.game_state:
            self.show_notification("❌ 没有可回滚的状态")
            return
        
        try:
            # 恢复所有玩家的老鼠位置
            for player in self.game_state.players:
                if player.player_id not in self.saved_positions:
                    continue
                
                saved_player_positions = self.saved_positions[player.player_id]
                
                # 根据保存的状态恢复老鼠位置
                for rat_id, position_info in saved_player_positions.items():
                    # 找到对应的老鼠对象
                    rat = None
                    for r in player.rats:
                        if r.rat_id == rat_id:
                            rat = r
                            break
                    
                    if rat:
                        location = position_info['location']
                        space_index = position_info['space_index']
                        
                        if location == 'board':
                            rat.space_index = space_index
                            rat.on_rocket = False
                        elif location == 'rocket' or location == 'inventory':
                            rat.on_rocket = True
                            # 火箭上的老鼠不需要设置 space_index
            
            # 清除移动状态和已移动老鼠记录
            self.reset_move_state()
            self.moved_rats_this_turn.clear()  # 清空已移动老鼠列表，允许重新移动
            
            # 保留备份状态，允许多次回滚
            # self.clear_backup()  # 注释掉，保持备份状态
            
            self.play_sound('success')
            self.show_notification("✅ 已回滚到移动前状态 (可重复回滚)")
            print("🔄 位置状态已回滚，备份状态保留")
            
        except Exception as e:
            self.play_sound('error')
            self.show_notification(f"❌ 回滚失败: {str(e)}")
            print(f"❌ 回滚失败: {e}")
    
    def clear_backup(self):
        """清除备份状态"""
        self.saved_positions = None
        self.has_backup = False
        print("🗑️ 已清除位置备份")
    
    def auto_save_before_move(self):
        """在回合开始时自动保存状态（已弃用，现在在玩家切换时保存）"""
        # 这个方法已经不再需要，因为现在在玩家切换时就保存状态
        # 保留此方法以防其他地方还有调用
        if not self.has_backup:
            print("⚠️ 警告：应该在玩家切换时已保存状态，但当前没有备份")
            self.save_positions_backup()
            self.show_notification("💾 紧急保存：回合开始前状态")    
   
 # ===== 新的移动逻辑方法 =====
    
    def reset_move_state(self):
        """重置移动状态到初始状态"""
        self.move_state = "idle"
        self.planned_moves.clear()
        self.current_selecting_rat = None
        self.move_sequence_step = 0
        self.selected_rats.clear()
        self.selected_space = None
        
        # 清除所有老鼠的视觉状态
        self.renderer.clear_all_rat_states()
        
        print("🔄 移动状态已重置")
        if self.moved_rats_this_turn:
            print(f"📋 本回合已移动的老鼠: {self.moved_rats_this_turn}")
    
    def start_rat_selection(self, rat_id: str):
        """开始选择一只老鼠进行移动"""
        # 移除在移动时的自动保存，现在在玩家切换时保存
        
        self.current_selecting_rat = rat_id
        self.move_state = "selecting"
        
        # 更新视觉状态
        self.renderer.set_rat_selected(rat_id, True)
        
        current_player = self.game_state.current_player_obj()
        rat = next((r for r in current_player.get_rats_on_board() if r.rat_id == rat_id), None)
        
        if rat:
            self.show_notification(f"🐭 选中老鼠 {rat_id[-1]}，请点击目标位置 (最大移动5步)")
            print(f"开始选择老鼠 {rat_id} 的移动目标，当前位置: {rat.space_index}")
    
    def set_rat_target(self, rat_id: str, target_space: int):
        """为选中的老鼠设置目标位置"""
        current_player = self.game_state.current_player_obj()
        rat = next((r for r in current_player.get_rats_on_board() if r.rat_id == rat_id), None)
        
        if not rat:
            self.show_notification("❌ 找不到老鼠")
            return
        
        # 计算移动步数
        steps = target_space - rat.space_index
        
        # 验证移动
        if steps <= 0:
            self.show_notification("❌ 只能向前移动")
            return
        
        if steps > 5:
            self.show_notification("❌ 最大移动步数为5")
            return
        
        # 添加到计划移动列表
        self.planned_moves.append((rat_id, target_space))
        self.current_selecting_rat = None
        
        # 更新视觉状态
        self.renderer.set_rat_selected(rat_id, False)  # 取消选中状态
        
        print(f"老鼠 {rat_id} 计划移动 {steps} 步到位置 {target_space}")
        
        # 根据移动步数决定下一步
        if steps > 3:
            # 移动超过3步，只能移动这一只老鼠，立即执行
            self.show_notification(f"🚀 移动超过3步，立即执行移动")
            self.execute_single_move()
        else:
            # 移动3步或以下，可以选择更多老鼠
            self.show_notification(f"✅ 已计划移动 {steps} 步。按回车确认，或选择更多老鼠")
            self.prompt_for_more_moves()
    
    def can_select_more_rats(self) -> bool:
        """检查是否可以选择更多老鼠"""
        # 如果已有移动超过3步的老鼠，不能选择更多
        for rat_id, target_space in self.planned_moves:
            current_player = self.game_state.current_player_obj()
            rat = next((r for r in current_player.get_rats_on_board() if r.rat_id == rat_id), None)
            if rat:
                steps = target_space - rat.space_index
                if steps > 3:
                    return False
        
        # 最多选择3只老鼠（游戏规则限制）
        return len(self.planned_moves) < 3
    
    def prompt_for_more_moves(self):
        """提示用户是否要选择更多老鼠"""
        moves_count = len(self.planned_moves)
        if moves_count == 1:
            self.show_notification("💡 可以选择更多老鼠，或按回车确认当前移动")
        else:
            self.show_notification(f"💡 已选择 {moves_count} 只老鼠，按回车确认或继续选择") 
   
    def execute_single_move(self):
        """执行单只老鼠的移动（移动超过3步的情况）"""
        if not self.planned_moves:
            return
        
        # 只执行第一个移动
        rat_id, target_space = self.planned_moves[0]
        current_player = self.game_state.current_player_obj()
        rat = next((r for r in current_player.get_rats_on_board() if r.rat_id == rat_id), None)
        
        if rat:
            steps = target_space - rat.space_index
            moves = [(rat_id, steps)]
            
            try:
                # 执行移动
                action = create_move_action(moves)
                events = self.game_state.apply(action, current_player.player_id, self.config)
                self.recent_events.extend(events)
                
                # 记录已移动的老鼠
                self.moved_rats_this_turn.append(rat_id)
                
                self.play_sound('move')
                self.show_notification(f"✅ 老鼠移动成功: {steps} 步")
                print(f"✓ 单只老鼠移动成功: {rat_id} 移动 {steps} 步")
                
                # 移动成功，但保留备份状态直到回合结束
                # self.clear_backup()  # 不在这里清除，等回合结束时清除
                
                # 重置状态
                self.reset_move_state()
                
                # 检查游戏是否结束
                if self.game_state.game_over:
                    self.game_mode = "game_over"
                    self.play_sound('game_over')
                
            except ValueError as e:
                self.play_sound('error')
                self.show_notification(f"❌ 移动失败: {str(e)} | 按U键回滚")
                print(f"❌ 移动失败: {e}")
                # 不重置状态，保留备份以便用户选择回滚
                self.reset_move_state()
    
    def confirm_all_moves(self):
        """确认并执行所有计划的移动"""
        if not self.planned_moves:
            self.show_notification("❌ 没有计划的移动")
            return
        
        current_player = self.game_state.current_player_obj()
        moves = []
        
        # 构建移动列表
        for rat_id, target_space in self.planned_moves:
            rat = next((r for r in current_player.get_rats_on_board() if r.rat_id == rat_id), None)
            if rat:
                steps = target_space - rat.space_index
                moves.append((rat_id, steps))
        
        if moves:
            try:
                # 执行所有移动
                action = create_move_action(moves)
                events = self.game_state.apply(action, current_player.player_id, self.config)
                self.recent_events.extend(events)
                
                # 记录所有已移动的老鼠
                for rat_id, _ in moves:
                    self.moved_rats_this_turn.append(rat_id)
                
                self.play_sound('move')
                self.show_notification(f"✅ 批量移动成功: {len(moves)} 只老鼠")
                print(f"✓ 批量移动成功: {moves}")
                
                # 移动成功，但保留备份状态直到回合结束
                # self.clear_backup()  # 不在这里清除，等回合结束时清除
                
                # 重置状态
                self.reset_move_state()
                
                # 检查游戏是否结束
                if self.game_state.game_over:
                    self.game_mode = "game_over"
                    self.play_sound('game_over')
                
            except ValueError as e:
                self.play_sound('error')
                self.show_notification(f"❌ 移动失败: {str(e)} | 按U键回滚")
                print(f"❌ 移动失败: {e}")
                # 不重置状态，保留备份以便用户选择回滚
    
    def cancel_move_sequence(self):
        """取消当前的移动序列"""
        self.show_notification("🚫 已取消移动序列")
        self.reset_move_state()
        self.play_sound('click')    

    def attempt_move_to_space(self, target_space: int):
        """Attempt to move selected rats to target space."""
        if not self.selected_rats:
            return
        
        current_player = self.game_state.current_player_obj()
        
        # Calculate moves for each selected rat
        moves = []
        for rat_id in self.selected_rats:
            rat = next((r for r in current_player.get_rats_on_board() if r.rat_id == rat_id), None)
            if rat:
                steps = target_space - rat.space_index
                if steps > 0:  # Only forward moves
                    moves.append((rat_id, steps))
        
        if moves:
            try:
                # Create and execute move action
                action = create_move_action(moves)
                events = self.game_state.apply(action, current_player.player_id, self.config)
                self.recent_events.extend(events)
                
                # 记录所有已移动的老鼠
                for rat_id, _ in moves:
                    self.moved_rats_this_turn.append(rat_id)
                
                # Clear selection
                self.selected_rats.clear()
                
                self.play_sound('move')
                self.show_notification(f"✅ 移动成功: {len(moves)}只老鼠")
                print(f"✓ 移动成功: {moves}")
                
                # Check if game ended
                if self.game_state.game_over:
                    self.game_mode = "game_over"
                    self.play_sound('game_over')
                
            except ValueError as e:
                self.play_sound('error')
                self.show_notification(f"❌ 移动失败: {str(e)}")
                print(f"❌ 移动失败: {e}")
    
    def execute_end_turn(self):
        """Execute end turn action."""
        if not self.game_state or self.game_state.game_over:
            return
        
        try:
            current_player = self.game_state.current_player_obj()
            action = create_end_turn_action()
            events = self.game_state.apply(action, current_player.player_id, self.config)
            self.recent_events.extend(events)
            
            # Clear selections and backup
            self.selected_rats.clear()
            self.selected_space = None
            self.moved_rats_this_turn.clear()  # 清空本回合已移动老鼠列表
            self.clear_backup()  # 结束回合时清除备份
            
            # 为新的当前玩家保存回合开始前的状态
            if not self.game_state.game_over:
                self.save_positions_backup()
                new_player = self.game_state.current_player_obj()
                print(f"💾 已为新玩家 {new_player.name} 保存回合开始前状态")
            
            self.play_sound('end_turn')
            self.show_notification(f"✅ {current_player.name} 结束回合")
            print(f"✓ {current_player.name} 结束回合")
            
        except ValueError as e:
            self.play_sound('error')
            self.show_notification(f"❌ 结束回合失败: {str(e)}")
            print(f"❌ 结束回合失败: {e}")
    
    def show_space_info(self, space_index: int):
        """Show information about a space."""
        space = self.game_state.board.get_space(space_index)
        info_text = f"格子 {space_index}: {space.kind.value}"
        
        if space.color:
            info_text += f" ({space.color.value})"
        
        self.show_notification(info_text)
        print(f"格子 {space_index}: {space.kind.value} ({space.color.value})")
        
        if space.payload:
            print(f"  属性: {space.payload}")
        
        # Show rats at this space
        rats_here = []
        for player in self.game_state.players:
            for rat in player.get_rats_on_board():
                if rat.space_index == space_index:
                    rats_here.append(f"{rat.rat_id}({player.name})")
        
        if rats_here:
            print(f"  老鼠: {', '.join(rats_here)}")
    
    def start_new_game(self, num_players: int, names: List[str]):
        """Start a new game."""
        try:
            self.game_state = new_game(num_players, names, self.config)
            self.game_mode = "game"
            self.recent_events.clear()
            self.selected_rats.clear()
            self.selected_space = None
            self.moved_rats_this_turn.clear()  # 清空已移动老鼠列表
            self.clear_backup()  # 新游戏时清除备份
            
            # 为第一个玩家保存回合开始前的状态
            self.save_positions_backup()
            first_player = self.game_state.current_player_obj()
            print(f"💾 已为第一个玩家 {first_player.name} 保存回合开始前状态")
            
            self.play_sound('success')
            self.show_notification(f"🎮 新游戏开始: {num_players}人游戏")
            print(f"🎮 新游戏开始: {num_players}人游戏")
        except Exception as e:
            self.play_sound('error')
            self.show_notification(f"❌ 游戏创建失败: {str(e)}")
            print(f"❌ 游戏创建失败: {e}")
    
    def update(self):
        """Update game state."""
        # Keep recent events list manageable
        if len(self.recent_events) > 20:
            self.recent_events = self.recent_events[-10:]  
  
    def render(self):
        """Render the current game state."""
        if self.game_mode == "menu":
            self.render_menu()
        elif self.game_mode == "game":
            self.render_game()
        elif self.game_mode == "game_over":
            self.render_game_over()
        
        # Render notification
        if self.notification_timer > 0:
            self.render_notification()
        
        pygame.display.flip()
    
    def render_notification(self):
        """Render notification message."""
        if not self.notification_text:
            return
        
        # Create notification surface with alpha
        alpha = min(255, int(255 * (self.notification_timer / 2.0)))
        notification_surface = pygame.Surface((400, 60))
        notification_surface.set_alpha(alpha)
        notification_surface.fill((0, 0, 0))
        
        # Add border
        pygame.draw.rect(notification_surface, (255, 255, 255), notification_surface.get_rect(), 2)
        
        # Render text
        text_surface = self.font_medium.render(self.notification_text, True, (255, 255, 255))
        text_rect = text_surface.get_rect()
        text_rect.center = notification_surface.get_rect().center
        notification_surface.blit(text_surface, text_rect)
        
        # Position notification
        notification_rect = notification_surface.get_rect()
        notification_rect.centerx = self.screen_width // 2
        notification_rect.y = 50
        
        self.screen.blit(notification_surface, notification_rect)
    
    def render_menu(self):
        """Render the main menu."""
        # Animated background
        self.screen.fill((50, 50, 100))
        
        # Add some animated stars
        for i in range(20):
            x = (i * 123 + int(self.animation_time * 50)) % self.screen_width
            y = (i * 456 + int(self.animation_time * 30)) % self.screen_height
            brightness = int(128 + 127 * math.sin(self.animation_time + i))
            pygame.draw.circle(self.screen, (brightness, brightness, brightness), (x, y), 2)
        
        # Title with glow effect
        title_text = "萌鼠登月"
        for offset in [(2, 2), (1, 1), (0, 0)]:
            color = (100, 100, 255) if offset != (0, 0) else (255, 255, 255)
            title = self.font_large.render(title_text, True, color)
            title_rect = title.get_rect()
            title_rect.centerx = self.screen_width // 2 + offset[0]
            title_rect.y = 100 + offset[1]
            self.screen.blit(title, title_rect)
        
        subtitle = self.font_medium.render("First Rat to the Moon", True, (200, 200, 200))
        subtitle_rect = subtitle.get_rect()
        subtitle_rect.centerx = self.screen_width // 2
        subtitle_rect.y = 160
        self.screen.blit(subtitle, subtitle_rect)
        
        # Menu options with hover effects
        menu_items = [
            ("1", "新游戏 (2人)"),
            ("2", "新游戏 (3人)"),
            ("3", "新游戏 (4人)"),
            ("D", "演示游戏"),
            ("Q", "退出游戏")
        ]
        
        y_start = 280
        for i, (key, description) in enumerate(menu_items):
            # Animated hover effect
            hover_offset = math.sin(self.animation_time * 3 + i) * 5
            
            key_surface = self.font_medium.render(key, True, (255, 255, 100))
            desc_surface = self.font_medium.render(f" - {description}", True, (255, 255, 255))
            
            key_rect = key_surface.get_rect()
            key_rect.x = self.screen_width // 2 - 100 + hover_offset
            key_rect.y = y_start + i * 50
            
            desc_rect = desc_surface.get_rect()
            desc_rect.x = key_rect.right
            desc_rect.y = key_rect.y
            
            self.screen.blit(key_surface, key_rect)
            self.screen.blit(desc_surface, desc_rect)
        
        # Instructions
        instruction = self.font_small.render("按对应按键开始游戏", True, (150, 150, 150))
        instruction_rect = instruction.get_rect()
        instruction_rect.centerx = self.screen_width // 2
        instruction_rect.y = self.screen_height - 50
        self.screen.blit(instruction, instruction_rect)
    
    def render_game(self):
        """Render the game."""
        if self.game_state:
            # Update renderer animation time
            self.renderer.animation_time = self.animation_time
            self.renderer.render_game(self.game_state)
            
            # Render planned moves overlay
            if self.planned_moves:
                self.renderer.render_planned_moves(self.planned_moves, self.game_state)
            
            # Highlight hovered space
            if self.hover_space is not None and self.hover_space != self.selected_space:
                x, y = asset_manager.get_space_coordinates(self.hover_space)
                # Pulsing hover effect
                alpha = int(128 + 127 * math.sin(self.animation_time * 6))
                hover_surface = pygame.Surface((64, 64))
                hover_surface.set_alpha(alpha)
                hover_surface.fill((255, 255, 255))
                self.screen.blit(hover_surface, (x-2, y-2))
            
            # Highlight selected space
            if self.selected_space is not None:
                x, y = asset_manager.get_space_coordinates(self.selected_space)
                pygame.draw.rect(self.screen, (255, 255, 0), (x-2, y-2, 64, 64), 3)
            
            # 选中的老鼠高亮现在由 RatElement 自己处理
            # Selected rats highlighting is now handled by RatElement itself
            
            # Show help overlay
            if self.show_help:
                self.render_help_overlay()
    
    def render_help_overlay(self):
        """Render help information overlay."""
        # Semi-transparent background
        overlay = pygame.Surface((600, 450))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 50))
        pygame.draw.rect(overlay, (255, 255, 255), overlay.get_rect(), 2)
        
        overlay_rect = overlay.get_rect()
        overlay_rect.center = (self.screen_width // 2, self.screen_height // 2)
        self.screen.blit(overlay, overlay_rect)
        
        # Help text
        help_items = [
            "=== 新移动系统帮助 ===",
            "",
            "🐭 移动流程:",
            "1. 点击老鼠选择移动",
            "2. 点击目标位置 (最大5步)",
            "3. 如果>3步: 立即执行",
            "4. 如果≤3步: 可选更多老鼠",
            "",
            "⌨️ 控制键:",
            "回车键: 确认所有移动",
            "C键: 取消移动序列",
            "R键: 重置移动状态",
            "U键: 回滚到回合开始状态 (可重复)",
            "空格键: 结束回合",
            "H键: 显示/隐藏帮助",
            "ESC键: 返回菜单",
            "",
            "🎯 目标: 让4只老鼠登上火箭！",
            "",
            "按H键关闭帮助"
        ]
        
        y_offset = overlay_rect.y + 20
        for item in help_items:
            if item.startswith("==="):
                text = self.font_medium.render(item, True, (255, 255, 100))
            elif item == "":
                y_offset += 10
                continue
            else:
                text = self.font_small.render(item, True, (255, 255, 255))
            
            text_rect = text.get_rect()
            text_rect.centerx = overlay_rect.centerx
            text_rect.y = y_offset
            self.screen.blit(text, text_rect)
            y_offset += 25
    
    def render_game_over(self):
        """Render game over screen."""
        if self.game_state:
            self.renderer.render_game(self.game_state)
            
            # Game over overlay with animation
            overlay = pygame.Surface((self.screen_width, self.screen_height))
            alpha = int(128 + 64 * math.sin(self.animation_time * 2))
            overlay.set_alpha(alpha)
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, (0, 0))
            
            # Game over text with glow
            game_over_text = "游戏结束"
            for offset in [(3, 3), (2, 2), (1, 1), (0, 0)]:
                color = (100, 0, 0) if offset != (0, 0) else (255, 255, 255)
                text_surface = self.font_large.render(game_over_text, True, color)
                text_rect = text_surface.get_rect()
                text_rect.center = (self.screen_width // 2 + offset[0], self.screen_height // 2 - 50 + offset[1])
                self.screen.blit(text_surface, text_rect)
            
            # Winner text
            if self.game_state.winner_ids:
                winner_names = []
                for winner_id in self.game_state.winner_ids:
                    winner = self.game_state.get_player_by_id(winner_id)
                    if winner:
                        winner_names.append(winner.name)
                
                if len(winner_names) == 1:
                    winner_text = f"🏆 {winner_names[0]} 获胜！"
                else:
                    winner_text = f"🏆 平局：{', '.join(winner_names)}"
                
                winner_surface = self.font_medium.render(winner_text, True, (255, 255, 0))
                winner_rect = winner_surface.get_rect()
                winner_rect.center = (self.screen_width // 2, self.screen_height // 2)
                self.screen.blit(winner_surface, winner_rect)
            
            # Continue instruction
            continue_text = self.font_small.render("按ESC或空格键返回菜单", True, (200, 200, 200))
            continue_rect = continue_text.get_rect()
            continue_rect.center = (self.screen_width // 2, self.screen_height // 2 + 50)
            self.screen.blit(continue_text, continue_rect)


def main():
    """Main entry point for GUI application."""
    try:
        app = FirstRatGUI()
        app.run()
    except Exception as e:
        print(f"GUI启动失败: {e}")
        print("请确保已安装pygame: pip install pygame")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()