#!/usr/bin/env python3
"""
启动萌鼠登月游戏GUI界面

Launch script for First Rat to the Moon GUI.
"""

import sys
import os

def check_dependencies():
    """检查必要的依赖是否安装"""
    missing_deps = []
    
    try:
        import pygame
        print(f"✓ pygame {pygame.version.ver} 已安装")
    except ImportError:
        missing_deps.append("pygame")
    
    if missing_deps:
        print("❌ 缺少必要依赖:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\n请运行以下命令安装依赖:")
        print(f"pip install {' '.join(missing_deps)}")
        return False
    
    return True

def check_assets():
    """检查资源文件是否存在"""
    assets_dir = "assets"
    if not os.path.exists(assets_dir):
        print(f"⚠️  资源目录不存在: {assets_dir}")
        print("将使用默认占位符资源")
        return False
    
    # 检查关键资源文件
    key_files = [
        "coordinates.json",
        "README.md"
    ]
    
    missing_files = []
    for file_path in key_files:
        full_path = os.path.join(assets_dir, file_path)
        if os.path.exists(full_path):
            print(f"✓ 找到资源文件: {file_path}")
        else:
            missing_files.append(file_path)
    
    if missing_files:
        print("⚠️  以下资源文件不存在:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        print("将使用默认资源")
    
    return True

def setup_python_path():
    """设置Python导入路径"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 添加当前目录
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # 添加游戏核心代码目录
    core_dir = os.path.join(current_dir, "first_rat_to_the_moon")
    if core_dir not in sys.path:
        sys.path.insert(0, core_dir)
    
    print(f"✓ 已添加路径: {current_dir}")
    print(f"✓ 已添加路径: {core_dir}")

def main():
    """主函数"""
    print("🚀 启动萌鼠登月游戏...")
    print("=" * 50)
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        print(f"当前版本: {sys.version}")
        return 1
    
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # 检查依赖
    if not check_dependencies():
        return 1
    
    # 检查资源
    check_assets()
    
    # 设置导入路径
    setup_python_path()
    
    print("=" * 50)
    print("🎮 启动游戏界面...")
    
    try:
        # 导入并启动GUI
        from first_rat_local.gui.app import main as gui_main
        return gui_main()
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保游戏文件完整")
        
        # 显示可用的模块路径用于调试
        print("\n🔍 调试信息:")
        print("Python路径:")
        for path in sys.path[:5]:  # 只显示前5个路径
            print(f"  - {path}")
        
        return 1
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code or 0)
    except KeyboardInterrupt:
        print("\n👋 游戏已退出")
        sys.exit(0)
    except Exception as e:
        print(f"💥 意外错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)