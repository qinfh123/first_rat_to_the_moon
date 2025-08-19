"""
Core enumerations for First Rat game.

This module defines all the enums used throughout the game engine.
"""

from enum import Enum, auto


class Color(Enum):
    """棋盘格子颜色 - Board space colors"""
    GREEN = "GREEN"      # 绿色
    YELLOW = "YELLOW"    # 黄色
    RED = "RED"          # 红色
    BLUE = "BLUE"        # 蓝色


class Resource(Enum):
    """游戏资源类型 - Game resource types"""
    CHEESE = "CHEESE"           # 奶酪
    TIN_CAN = "TIN_CAN"         # 罐头
    SODA = "SODA"               # 苏打粉
    LIGHTBULB = "LIGHTBULB"     # 灯泡
    BOTTLECAP = "BOTTLECAP"     # 瓶盖


class SpaceKind(Enum):
    """棋盘格子类型 - Board space types"""
    RESOURCE = "RESOURCE"               # 资源格 - 产出指定资源
    SHOP_MOLE = "SHOP_MOLE"            # 鼹鼠店 - 扩容背包
    SHOP_FROG = "SHOP_FROG"            # 青蛙店 - 获得一次性 X2 饮料
    SHOP_CROW = "SHOP_CROW"            # 乌鸦店 - 获得/交换瓶盖加分
    LIGHTBULB_TRACK = "LIGHTBULB_TRACK"  # 推进灯泡轨道
    SHORTCUT = "SHORTCUT"              # 捷径 - 可能需要支付或有风险的通过
    HAZARD = "HAZARD"                  # 危险/惩罚 - 如被打回等
    START = "START"                    # 起点
    LAUNCH_PAD = "LAUNCH_PAD"          # 发射台 - 抵达可登船


class ActionType(Enum):
    """玩家动作类型 - Player action types"""
    MOVE = "MOVE"                      # 移动老鼠
    BUY = "BUY"                        # 购买商店物品
    STEAL = "STEAL"                    # 偷窃商店物品
    BUILD_ROCKET = "BUILD_ROCKET"      # 建造火箭部件
    DONATE_CHEESE = "DONATE_CHEESE"    # 捐赠奶酪
    END_TURN = "END_TURN"              # 结束回合


class RocketPart(Enum):
    """火箭部件类型 - Rocket part types"""
    NOSE = "NOSE"        # 火箭头
    TANK = "TANK"        # 燃料箱
    ENGINE = "ENGINE"    # 引擎
    FIN_A = "FIN_A"      # 尾翼A
    FIN_B = "FIN_B"      # 尾翼B


class DomainEventType(Enum):
    """领域事件类型 - Domain event types for logging and replay"""
    RESOURCE_GAINED = "RESOURCE_GAINED"         # 获得资源
    RESOURCE_SPENT = "RESOURCE_SPENT"           # 消耗资源
    INVENTORY_CHANGED = "INVENTORY_CHANGED"     # 背包变化
    TRACK_ADVANCED = "TRACK_ADVANCED"           # 轨道推进
    SHOP_BOUGHT = "SHOP_BOUGHT"                 # 商店购买
    SHOP_STOLEN = "SHOP_STOLEN"                 # 商店偷窃
    SENT_HOME = "SENT_HOME"                     # 老鼠被送回起点
    ON_ROCKET = "ON_ROCKET"                     # 老鼠登船
    NEW_RAT_GAINED = "NEW_RAT_GAINED"           # 获得新老鼠
    SCORE_CHANGED = "SCORE_CHANGED"             # 分数变化
    PART_BUILT = "PART_BUILT"                   # 火箭部件建造
    CHEESE_DONATED = "CHEESE_DONATED"           # 奶酪捐赠
    TURN_ENDED = "TURN_ENDED"                   # 回合结束
    GAME_ENDED = "GAME_ENDED"                   # 游戏结束
    LOG = "LOG"                                 # 一般日志