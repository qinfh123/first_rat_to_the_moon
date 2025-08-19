#!/usr/bin/env python3
"""
Simple script to run the First Rat game.

萌鼠登月游戏启动脚本
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from first_rat_local.cli.app import main

if __name__ == "__main__":
    main()