# 游戏资源文件说明

这个目录包含萌鼠登月游戏的所有图像和配置资源。

## 📁 目录结构

```
assets/
├── README.md                    # 本说明文件
├── coordinates.json             # 格子坐标配置文件
├── coordinates_template.json    # 坐标配置模板
├── board/                       # 棋盘相关资源
│   ├── background.png           # 游戏背景图
│   └── spaces/                  # 格子图像
│       ├── start.png            # 起点格子
│       ├── launch.png           # 发射台格子
│       ├── resource.png         # 资源格子
│       ├── shop_mole.png        # 鼹鼠店格子
│       ├── shop_frog.png        # 青蛙店格子
│       ├── shop_crow.png        # 乌鸦店格子
│       └── track.png            # 轨道格子
├── pieces/                      # 游戏棋子资源
│   ├── rats/                    # 老鼠图像
│   │   ├── player_1.png         # 玩家1老鼠
│   │   ├── player_2.png         # 玩家2老鼠
│   │   ├── player_3.png         # 玩家3老鼠
│   │   └── player_4.png         # 玩家4老鼠
│   ├── resources/               # 资源图像
│   │   ├── cheese.png           # 奶酪
│   │   ├── tin_can.png          # 罐头
│   │   ├── soda.png             # 苏打
│   │   ├── lightbulb.png        # 灯泡
│   │   └── bottlecap.png        # 瓶盖
│   └── shops/                   # 商店物品图像
│       ├── mole_capacity.png    # 鼹鼠店背包
│       ├── frog_x2.png          # 青蛙店X2效果
│       └── crow_bottlecap.png   # 乌鸦店瓶盖
└── ui/                          # 界面元素
    ├── button_normal.png        # 普通按钮
    ├── button_hover.png         # 悬停按钮
    ├── panel_bg.png             # 面板背景
    └── icons/                   # 图标
        ├── rocket.png           # 火箭图标
        ├── score.png            # 分数图标
        └── turn.png             # 回合图标
```

## 🎨 图像规格建议

### 棋盘背景
- **background.png**: 1200x800像素，游戏主背景

### 格子图像 (spaces/)
- 尺寸: 60x60像素
- 格式: PNG (支持透明)
- 风格: 清晰、易识别的图标风格

### 老鼠图像 (rats/)
- 尺寸: 40x40像素
- 格式: PNG (支持透明)
- 建议: 不同颜色区分不同玩家

### 资源图像 (resources/)
- 尺寸: 30x30像素
- 格式: PNG (支持透明)
- 建议: 简洁明了的图标

## ⚙️ 坐标配置

### coordinates.json 格式
```json
{
  "config": {
    "board_offset": [100, 100],
    "space_size": 70,
    "ui_panel_width": 300,
    "window_size": [1200, 800]
  },
  "spaces": {
    "0": [100, 100],
    "1": [170, 100],
    "2": [240, 100],
    ...
  }
}
```

### 坐标说明
- `board_offset`: 棋盘在屏幕上的起始位置 [x, y]
- `space_size`: 格子之间的间距
- `spaces`: 每个格子的精确坐标 {"格子索引": [x, y]}

## 🚀 快速开始

### 1. 使用默认资源
如果没有自定义图像，游戏会自动生成彩色方块作为占位符。

### 2. 添加自定义图像
1. 将图像文件放入对应目录
2. 确保文件名与上述规格匹配
3. 重启游戏即可看到效果

### 3. 自定义坐标
1. 运行游戏一次生成 `coordinates_template.json`
2. 编辑模板文件调整格子位置
3. 重命名为 `coordinates.json`
4. 重启游戏应用新坐标

## 🎯 制作建议

### 美术风格
- 建议使用卡通或像素艺术风格
- 保持色彩鲜明，易于区分
- 考虑色盲友好的配色方案

### 文件优化
- 使用PNG格式保持透明度
- 适当压缩文件大小
- 保持图像清晰度

### 测试
- 在不同分辨率下测试显示效果
- 确保所有元素都清晰可见
- 测试颜色对比度

## 📝 注意事项

1. **文件命名**: 严格按照上述命名规范，区分大小写
2. **图像尺寸**: 建议遵循推荐尺寸，避免拉伸变形
3. **透明背景**: 棋子和资源图像建议使用透明背景
4. **版权**: 确保使用的图像资源有合法使用权

## 🔧 故障排除

### 图像不显示
1. 检查文件路径和命名是否正确
2. 确认图像格式是否支持 (PNG/JPG)
3. 查看控制台是否有错误信息

### 坐标不准确
1. 检查 coordinates.json 格式是否正确
2. 确认坐标值是否在屏幕范围内
3. 重新生成坐标模板文件

---

🎨 **祝你制作出精美的游戏界面！**