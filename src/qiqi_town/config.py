"""全局常量与配色。"""

from __future__ import annotations

GAME_TITLE = "淇淇的小镇"
GAME_VERSION = "0.1.0"

WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 900
MIN_WINDOW_WIDTH = 1280
MIN_WINDOW_HEIGHT = 720

SAVE_SLOT_COUNT = 20
SAVE_SCHEMA_VERSION = 1

DAY_START_MINUTE = 8 * 60
DAY_END_MINUTE = 20 * 60
GAME_MINUTES_PER_SECOND = 1.0

TOWN_SIZE = 140.0
CELL_SIZE = 0.5

# 以奶油白、珊瑚红、蜂蜜黄、湖水青、草地绿、木头棕为主的糖果色。
PALETTE: dict[str, tuple[float, float, float, float]] = {
    "cream": (1.0, 0.965, 0.89, 1.0),
    "sky": (0.66, 0.85, 0.92, 1.0),
    "grass": (0.56, 0.78, 0.53, 1.0),
    "grass_light": (0.68, 0.86, 0.62, 1.0),
    "path": (0.85, 0.76, 0.61, 1.0),
    "water": (0.45, 0.73, 0.82, 1.0),
    "coral": (0.95, 0.52, 0.47, 1.0),
    "balloon": (0.92, 0.18, 0.16, 1.0),
    "honey": (0.98, 0.80, 0.42, 1.0),
    "teal": (0.36, 0.64, 0.61, 1.0),
    "wood": (0.64, 0.48, 0.35, 1.0),
    "wood_dark": (0.45, 0.32, 0.24, 1.0),
    "ink": (0.22, 0.20, 0.19, 1.0),
    "hair": (0.16, 0.13, 0.12, 1.0),
    "hair_highlight": (0.24, 0.19, 0.17, 1.0),
    "skin": (1.0, 0.80, 0.68, 1.0),
    "skin_shadow": (0.94, 0.70, 0.60, 1.0),
    "lace": (1.0, 0.98, 0.93, 1.0),
    "eye": (0.30, 0.18, 0.12, 1.0),
    "eye_highlight": (1.0, 1.0, 1.0, 1.0),
    "white": (1.0, 1.0, 1.0, 1.0),
    "shadow": (0.15, 0.14, 0.13, 0.22),
    "lantern": (1.0, 0.55, 0.25, 1.0),
    "leaf": (0.33, 0.60, 0.34, 1.0),
    "leaf_light": (0.48, 0.72, 0.40, 1.0),
    "stone": (0.68, 0.67, 0.64, 1.0),
    "ui_panel": (1.0, 0.965, 0.89, 0.96),
    "ui_panel_dark": (0.30, 0.25, 0.22, 0.92),
    "ui_text": (0.22, 0.20, 0.19, 1.0),
    "ui_accent": (0.93, 0.48, 0.42, 1.0),
    "ui_focus": (0.98, 0.80, 0.42, 1.0),
}

LOCATION_LABELS = {
    "town": "青禾镇",
    "home": "家",
    "kindergarten": "幼儿园",
    "library": "图书馆",
    "park": "公园",
    "playground": "游乐场",
    "mountain": "青禾山",
    "square": "中心广场",
}

DAY_TITLES = {
    1: "新朋友",
    2: "旧书里的地图",
    3: "公园野餐",
    4: "游乐场的约定",
    5: "山顶的灯会",
}

# 开发期字体（发布前换为随包的 OFL 字体）。
SYSTEM_CJK_FONT_CANDIDATES = (
    "C:/Windows/Fonts/simhei.ttf",
    "C:/Windows/Fonts/msyh.ttf",
    "C:/Windows/Fonts/msjh.ttf",
)
