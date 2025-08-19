"""
Main CLI application for First Rat game.

This module provides the main game loop and user interface.
主CLI应用程序，提供主游戏循环和用户界面。
"""

import os
import sys
from typing import List, Optional
from ..core.setup import new_game, create_demo_game, get_setup_summary
from ..core.config import Config
from ..core.models import GameState
from ..core.events import DomainEvent
from .render import render_full_game_state, render_events
from .input_schemas import parse_command, InputParseError, get_command_help, suggest_corrections


def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def get_player_setup() -> tuple[int, List[str]]:
    """
    Get player count and names from user input.
    
    获取玩家数量和姓名。
    
    Returns:
        Tuple of (player_count, player_names)
    """
    print("=== 萌鼠登月 - 游戏设置 ===\n")
    
    # Get number of players
    while True:
        try:
            num_players = int(input("请输入玩家数量 (2-4): "))
            if 2 <= num_players <= 4:
                break
            else:
                print("玩家数量必须在2-4之间！")
        except ValueError:
            print("请输入有效数字！")
    
    # Get player names
    names = []
    for i in range(num_players):
        while True:
            name = input(f"请输入玩家{i+1}的姓名: ").strip()
            if name:
                if name not in names:
                    names.append(name)
                    break
                else:
                    print("玩家姓名不能重复！")
            else:
                print("玩家姓名不能为空！")
    
    return num_players, names


def show_welcome():
    """Display welcome message."""
    welcome_text = """
╔══════════════════════════════════════╗
║            萌鼠登月游戏              ║
║         First Rat Local Game         ║
╚══════════════════════════════════════╝

欢迎来到萌鼠登月！在这个游戏中，你将控制老鼠们
在棋盘上移动，收集资源，建造火箭，最终登上月球！

游戏目标：
- 移动老鼠收集资源
- 在商店购买升级或偷窃物品
- 建造火箭部件获得分数
- 让老鼠登上火箭前往月球
- 成为第一个让4只老鼠登船的玩家获胜！

输入 'help' 查看命令帮助
输入 'quit' 退出游戏

"""
    print(welcome_text)


def show_game_setup_menu() -> GameState:
    """
    Show game setup menu and return initialized game state.
    
    显示游戏设置菜单并返回初始化的游戏状态。
    """
    print("=== 游戏设置 ===")
    print("1. 新游戏")
    print("2. 演示游戏 (预设3人游戏)")
    print("3. 退出")
    
    while True:
        choice = input("\n请选择 (1-3): ").strip()
        
        if choice == "1":
            num_players, names = get_player_setup()
            config = Config.default()
            return new_game(num_players, names, config)
        
        elif choice == "2":
            return create_demo_game()
        
        elif choice == "3":
            print("感谢游玩！再见！")
            sys.exit(0)
        
        else:
            print("无效选择，请输入1-3！")


def handle_game_action(state: GameState, config: Config, command: str) -> tuple[bool, List[DomainEvent], Optional[str]]:
    """
    Handle a game action command.
    
    处理游戏动作命令。
    
    Args:
        state: Current game state
        config: Game configuration
        command: User command string
    
    Returns:
        Tuple of (success, events, error_message)
    """
    try:
        # Parse command
        action = parse_command(command)
        
        # Apply action to game state
        current_player = state.current_player_obj()
        events = state.apply(action, current_player.player_id, config)
        
        return True, events, None
    
    except InputParseError as e:
        return False, [], str(e)
    
    except ValueError as e:
        # Game rule violation
        error_msg = str(e)
        if "Invalid action:" in error_msg:
            error_msg = error_msg.replace("Invalid action: ", "")
        return False, [], f"动作无效: {error_msg}"
    
    except Exception as e:
        return False, [], f"未知错误: {str(e)}"


def main_game_loop(state: GameState, config: Config):
    """
    Main game loop.
    
    主游戏循环。
    
    Args:
        state: Initial game state
        config: Game configuration
    """
    recent_events = []
    
    print("\n" + "="*50)
    print("游戏开始！")
    print(get_setup_summary(state))
    print("="*50)
    
    input("\n按回车键开始游戏...")
    
    while not state.game_over:
        # Clear screen and show current state
        clear_screen()
        
        # Render full game state
        game_display = render_full_game_state(state, recent_events[-5:] if recent_events else None)
        print(game_display)
        
        # Get current player
        current_player = state.current_player_obj()
        
        # Get user input
        print(f"\n{current_player.name} 的回合")
        print("输入命令 (输入 'help' 查看帮助):")
        
        command = input("> ").strip()
        
        # Handle special commands
        if command.lower() in ["help", "帮助"]:
            print(get_command_help())
            input("\n按回车键继续...")
            continue
        
        elif command.lower() in ["quit", "exit", "退出"]:
            confirm = input("确定要退出游戏吗？(y/n): ").strip().lower()
            if confirm in ["y", "yes", "是"]:
                print("感谢游玩！再见！")
                return
            continue
        
        elif command.lower() in ["state", "状态"]:
            # Show detailed state (for debugging)
            print(f"\n当前游戏状态:")
            print(f"回合: {state.round}")
            print(f"当前玩家: {current_player.name}")
            print(f"游戏结束: {state.game_over}")
            input("\n按回车键继续...")
            continue
        
        elif not command:
            print("请输入命令！")
            input("按回车键继续...")
            continue
        
        # Handle game action
        success, events, error_msg = handle_game_action(state, config, command)
        
        if success:
            # Add events to recent events
            recent_events.extend(events)
            
            # Show immediate feedback for important events
            if events:
                print(f"\n✓ 动作执行成功！")
                for event in events[-3:]:  # Show last 3 events
                    from ..core.events import format_event_for_display
                    print(f"  • {format_event_for_display(event)}")
            
            # Check if game ended
            if state.game_over:
                input("\n按回车键查看最终结果...")
                break
            
            input("\n按回车键继续...")
        
        else:
            # Show error message
            print(f"\n❌ {error_msg}")
            
            # Suggest corrections
            suggestions = suggest_corrections(command)
            if suggestions:
                print("\n建议:")
                for suggestion in suggestions:
                    print(f"  • {suggestion}")
            
            input("\n按回车键继续...")
    
    # Game over - show final results
    show_game_results(state)


def show_game_results(state: GameState):
    """
    Show final game results.
    
    显示最终游戏结果。
    """
    clear_screen()
    
    print("🎉 游戏结束！🎉\n")
    
    # Show final state
    from .render import render_players, render_rocket_status
    print(render_players(state))
    print("\n" + render_rocket_status(state))
    
    # Show winners
    if state.winner_ids:
        winner_names = []
        for winner_id in state.winner_ids:
            winner = state.get_player_by_id(winner_id)
            if winner:
                winner_names.append(winner.name)
        
        if len(winner_names) == 1:
            print(f"\n🏆 获胜者: {winner_names[0]}！")
        else:
            print(f"\n🏆 平局！获胜者: {', '.join(winner_names)}！")
    
    # Show final scores
    print(f"\n=== 最终得分 ===")
    sorted_players = sorted(state.players, key=lambda p: p.score, reverse=True)
    for i, player in enumerate(sorted_players, 1):
        print(f"{i}. {player.name}: {player.score} 分")
    
    print(f"\n游戏总回合数: {state.round}")
    print(f"总动作数: {len(state.history)}")


def main():
    """Main entry point for the CLI application."""
    try:
        # Show welcome message
        show_welcome()
        
        # Setup game
        state = show_game_setup_menu()
        config = Config.default()
        
        # Start main game loop
        main_game_loop(state, config)
        
    except KeyboardInterrupt:
        print("\n\n游戏被中断。感谢游玩！")
    except Exception as e:
        print(f"\n发生错误: {e}")
        print("游戏将退出。")
    
    input("\n按回车键退出...")


if __name__ == "__main__":
    main()