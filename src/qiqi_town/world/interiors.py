"""三个可进入的室内场景：家、幼儿园、图书馆。"""

from __future__ import annotations

from dataclasses import dataclass, field

from panda3d.core import NodePath

from qiqi_town.config import PALETTE
from qiqi_town.world import meshkit
from qiqi_town.world.nav import NavGrid

CELL = 0.5


@dataclass
class InteriorScene:
    id: str
    name: str
    root: NodePath
    nav: NavGrid
    spawn: tuple[float, float]
    exit_pos: tuple[float, float]
    width: float
    depth: float
    blockers: list[tuple[float, float, float, float]] = field(default_factory=list)


def build_home(parent: NodePath) -> InteriorScene:
    scene = _new_room(parent, "home", 10.0, 8.0, (0.95, 0.87, 0.73, 1.0))
    root = scene.root
    # 床
    _bed(root, (-3.1, 1.9), (2.5, 3.0), (0.83, 0.45, 0.38, 1.0))
    # 地毯
    meshkit.add_box(root, "rug", (0.2, 0.3, 0.025), (4.8, 3.2, 0.03), (0.90, 0.71, 0.55, 1.0))
    # 桌子与椅子
    _table(root, (2.3, 1.2), (2.2, 1.2))
    _chair(root, (1.3, 0.4), 0)
    _chair(root, (3.3, 0.4), 180)
    # 书架
    _bookshelf(root, (4.2, 2.2), heading=270, width=2.2)
    # 窗与灯
    _window(root, (-1.8, 3.9), 2.2)
    _lamp(root, (4.0, -1.5))
    scene.blockers.extend(
        [
            (-3.1, 1.9, 2.9, 3.4),
            (2.3, 1.2, 2.6, 1.6),
            (4.2, 2.2, 1.2, 2.6),
        ]
    )
    scene.nav = _make_nav(scene.width, scene.depth, scene.blockers)
    return scene


def build_kindergarten(parent: NodePath) -> InteriorScene:
    scene = _new_room(parent, "kindergarten", 12.0, 9.0, (0.83, 0.92, 0.84, 1.0))
    root = scene.root
    # 黑板
    meshkit.add_box(root, "blackboard", (0, 4.35, 1.6), (6.5, 0.1, 1.7), (0.18, 0.27, 0.24, 1.0))
    meshkit.add_box(root, "blackboard_frame", (0, 4.28, 1.6), (6.9, 0.08, 2.0), (0.76, 0.58, 0.38, 1.0))
    # 小桌子
    for i, x in enumerate((-3.2, 0.0, 3.2)):
        _table(root, (x, 1.4), (2.2, 1.6), height=0.58)
        for dx in (-0.75, 0.75):
            _chair(root, (x + dx, 0.35), 180 if dx < 0 else 180)
        _chair(root, (x, 2.6), 0)
    # 地毯
    meshkit.add_box(root, "rug", (-0.2, -1.6, 0.025), (5.0, 2.6, 0.03), (0.96, 0.77, 0.53, 1.0))
    # 玩具积木
    for i in range(6):
        meshkit.add_box(
            root,
            "toy_block",
            (-2.0 + (i % 3) * 0.5, -1.6 + (i // 3) * 0.5, 0.12),
            (0.38, 0.38, 0.38),
            [PALETTE["coral"], PALETTE["teal"], PALETTE["honey"]][i % 3],
        )
    # 储物格
    meshkit.add_box(root, "cubbies", (-4.6, 3.5, 1.1), (2.2, 0.9, 2.0), (0.90, 0.72, 0.45, 1.0))
    for row in range(3):
        for col in range(2):
            meshkit.add_box(
                root,
                "cubby",
                (-4.6 + (col - 0.5) * 0.85, 3.03, 0.55 + row * 0.6),
                (0.7, 0.08, 0.45),
                (0.73, 0.52, 0.34, 1.0),
            )
    _window(root, (2.1, 4.35), 2.0)
    scene.blockers.extend(
        [
            (-3.2, 1.4, 2.6, 2.0),
            (0.0, 1.4, 2.6, 2.0),
            (3.2, 1.4, 2.6, 2.0),
            (-4.6, 3.5, 2.6, 1.2),
        ]
    )
    scene.nav = _make_nav(scene.width, scene.depth, scene.blockers)
    return scene


def build_library(parent: NodePath) -> InteriorScene:
    scene = _new_room(parent, "library", 12.0, 8.0, (0.90, 0.82, 0.69, 1.0))
    root = scene.root
    # 两侧书架
    for side in (-1, 1):
        x = side * 5.0
        for i in range(3):
            y = -1.8 + i * 2.1
            _bookshelf(root, (x, y), heading=90 if side < 0 else 270, width=1.8)
    # 中央阅读桌
    _table(root, (0.0, 0.8), (3.2, 1.8), height=0.62)
    _chair(root, (-1.2, -0.6), 180)
    _chair(root, (1.2, -0.6), 180)
    meshkit.add_box(root, "rug", (0.0, 0.2, 0.025), (5.4, 3.6, 0.03), (0.62, 0.50, 0.38, 1.0))
    # 猫窝
    meshkit.add_cylinder(root, "cat_bed", (3.8, 2.2, 0.02), 0.65, 0.65, 0.18, (0.86, 0.66, 0.51, 1.0), segments=20)
    # 书堆
    for i in range(4):
        meshkit.add_box(
            root,
            "book_stack",
            (-1.6 + i * 0.18, 2.0, 0.08 + i * 0.09),
            (0.9, 0.6, 0.08),
            [PALETTE["coral"], PALETTE["teal"], PALETTE["honey"], PALETTE["leaf"]][i],
        )
    _window(root, (0.0, 3.95), 2.6)
    _lamp(root, (-3.6, -2.4))
    scene.blockers.extend(
        [
            (-5.0, -1.8, 1.4, 2.2),
            (-5.0, 0.3, 1.4, 2.2),
            (-5.0, 2.4, 1.4, 2.2),
            (5.0, -1.8, 1.4, 2.2),
            (5.0, 0.3, 1.4, 2.2),
            (5.0, 2.4, 1.4, 2.2),
            (0.0, 0.8, 3.6, 2.0),
        ]
    )
    scene.nav = _make_nav(scene.width, scene.depth, scene.blockers)
    return scene


def _new_room(
    parent: NodePath, name: str, width: float, depth: float, wall_color: tuple[float, float, float, float]
) -> InteriorScene:
    root = parent.attachNewNode(f"interior_{name}")
    root.hide()
    # 房间外的暗色地面，避免镜头越过南侧时露出天空。
    meshkit.add_box(root, "surround", (0, 0, -0.28), (42, 42, 0.2), (0.30, 0.25, 0.21, 1.0))
    # 地板与地毯
    meshkit.add_box(root, "floor", (0, 0, -0.1), (width, depth, 0.2), (0.82, 0.68, 0.52, 1.0))
    meshkit.add_box(root, "floor_edge", (0, 0, 0.005), (width - 0.2, depth - 0.2, 0.03), (0.88, 0.76, 0.59, 1.0))
    # 三面墙，南面完全打开以便第三人称镜头观察。
    wall_h = 2.9
    meshkit.add_box(root, "wall_n", (0, depth / 2, wall_h / 2), (width, 0.18, wall_h), wall_color)
    meshkit.add_box(root, "wall_w", (-width / 2, 0, wall_h / 2), (0.18, depth, wall_h), wall_color)
    meshkit.add_box(root, "wall_e", (width / 2, 0, wall_h / 2), (0.18, depth, wall_h), wall_color)
    # 门口地垫
    meshkit.add_box(root, "door_mat", (0, -depth / 2 + 0.55, 0.015), (1.8, 0.9, 0.03), (0.62, 0.44, 0.31, 1.0))
    # 护墙板
    meshkit.add_box(root, "wainscot_n", (0, depth / 2 - 0.1, 0.5), (width, 0.03, 0.9), (0.75, 0.57, 0.41, 1.0))
    meshkit.add_box(root, "wainscot_w", (-width / 2 + 0.1, 0, 0.5), (0.03, depth, 0.9), (0.75, 0.57, 0.41, 1.0))
    meshkit.add_box(root, "wainscot_e", (width / 2 - 0.1, 0, 0.5), (0.03, depth, 0.9), (0.75, 0.57, 0.41, 1.0))
    # 天花板灯带
    meshkit.add_box(root, "ceiling_light", (0, 0, 2.8), (width * 0.5, 0.25, 0.06), (1.0, 0.93, 0.76, 1.0))
    return InteriorScene(
        id=name,
        name=name,
        root=root,
        nav=NavGrid([[True]], origin=(-width / 2, -depth / 2), cell_size=CELL),
        spawn=(0.0, -depth / 2 + 1.5),
        exit_pos=(0.0, -depth / 2 + 0.4),
        width=width,
        depth=depth,
    )


def _make_nav(width: float, depth: float, blockers: list[tuple[float, float, float, float]]) -> NavGrid:
    cols = int(width / CELL)
    rows = int(depth / CELL)
    grid = [[True] * cols for _ in range(rows)]
    for y in range(rows):
        for x in range(cols):
            if x < 2 or y < 2 or x >= cols - 2 or y >= rows - 2:
                grid[y][x] = False

    def cell(x: float, y: float) -> tuple[int, int]:
        return int((x + width / 2) / CELL), int((y + depth / 2) / CELL)

    for cx, cy, w, d in blockers:
        x0, y0 = cell(cx - w / 2, cy - d / 2)
        x1, y1 = cell(cx + w / 2, cy + d / 2)
        for gy in range(max(0, y0), min(rows, y1 + 1)):
            for gx in range(max(0, x0), min(cols, x1 + 1)):
                grid[gy][gx] = False
    # 门口区域保持可走。
    for y in range(rows - 3, rows):
        for x in range(cols // 2 - 2, cols // 2 + 2):
            grid[y][x] = True
    return NavGrid(grid, origin=(-width / 2, -depth / 2), cell_size=CELL)


def _bed(root: NodePath, center: tuple[float, float], size: tuple[float, float], color) -> None:
    x, y = center
    w, d = size
    meshkit.add_box(root, "bed_base", (x, y, 0.35), (w, d, 0.5), PALETTE["wood"], )
    meshkit.add_box(root, "mattress", (x, y, 0.65), (w - 0.15, d - 0.15, 0.18), (0.98, 0.95, 0.88, 1.0))
    meshkit.add_box(root, "blanket", (x, y - 0.25, 0.78), (w - 0.15, d * 0.62, 0.08), color)
    meshkit.add_box(root, "pillow", (x, y + d / 2 - 0.35, 0.8), (w - 0.5, 0.55, 0.16), (1.0, 0.98, 0.92, 1.0))
    meshkit.add_box(root, "headboard", (x, y + d / 2 + 0.05, 0.8), (w, 0.12, 1.1), PALETTE["wood"])


def _table(root: NodePath, center: tuple[float, float], size: tuple[float, float], height: float = 0.72) -> None:
    x, y = center
    w, d = size
    meshkit.add_box(root, "table_top", (x, y, height), (w, d, 0.12), PALETTE["wood"])
    for dx in (-w / 2 + 0.15, w / 2 - 0.15):
        for dy in (-d / 2 + 0.15, d / 2 - 0.15):
            meshkit.add_box(root, "table_leg", (x + dx, y + dy, height / 2), (0.1, 0.1, height), PALETTE["wood_dark"])


def _chair(root: NodePath, center: tuple[float, float], heading: float) -> None:
    x, y = center
    group = root.attachNewNode("chair")
    group.setPos(x, y, 0)
    group.setH(heading)
    meshkit.add_box(group, "seat", (0, 0, 0.44), (0.46, 0.46, 0.1), PALETTE["wood"])
    meshkit.add_box(group, "back", (0, -0.21, 0.7), (0.46, 0.08, 0.42), PALETTE["wood"])
    for dx in (-0.17, 0.17):
        for dy in (-0.17, 0.17):
            meshkit.add_box(group, "leg", (dx, dy, 0.22), (0.07, 0.07, 0.44), PALETTE["wood_dark"])


def _bookshelf(root: NodePath, center: tuple[float, float], *, heading: float, width: float) -> None:
    x, y = center
    group = root.attachNewNode("bookshelf")
    group.setPos(x, y, 0)
    group.setH(heading)
    meshkit.add_box(group, "shelf", (0, 0, 1.2), (width, 0.55, 2.3), PALETTE["wood_dark"])
    for row in range(3):
        meshkit.add_box(
            group, "shelf_inner", (0, -0.30, 0.55 + row * 0.65), (width - 0.2, 0.06, 0.5), (0.72, 0.55, 0.40, 1.0)
        )
        for i in range(4):
            meshkit.add_box(
                group,
                "book",
                (-width / 2 + 0.3 + i * (width - 0.6) / 4, -0.37, 0.62 + row * 0.65),
                (0.12, 0.18, 0.38),
                [PALETTE["coral"], PALETTE["teal"], PALETTE["honey"], PALETTE["leaf"]][i % 4],
            )


def _window(root: NodePath, center: tuple[float, float], width: float) -> None:
    x, y = center
    meshkit.add_box(root, "window", (x, y - 0.12, 1.8), (width, 0.05, 1.1), (0.96, 0.92, 0.75, 1.0))
    meshkit.add_box(root, "window_bar_v", (x, y - 0.15, 1.8), (0.06, 0.04, 1.1), PALETTE["wood"])
    meshkit.add_box(root, "window_bar_h", (x, y - 0.15, 1.8), (width, 0.04, 0.06), PALETTE["wood"])


def _lamp(root: NodePath, center: tuple[float, float]) -> None:
    x, y = center
    meshkit.add_cylinder(root, "lamp_stand", (x, y, 0), 0.06, 0.06, 1.4, PALETTE["wood_dark"], segments=10)
    meshkit.add_cylinder(root, "lamp_shade", (x, y, 1.35), 0.3, 0.18, 0.38, (1.0, 0.90, 0.68, 1.0), segments=14)


def _door_frame(root: NodePath, center: tuple[float, float]) -> None:
    x, y = center
    meshkit.add_box(root, "door_frame_l", (x - 0.95, y, 1.0), (0.18, 0.2, 2.0), PALETTE["wood_dark"])
    meshkit.add_box(root, "door_frame_r", (x + 0.95, y, 1.0), (0.18, 0.2, 2.0), PALETTE["wood_dark"])
    meshkit.add_box(root, "door_frame_top", (x, y, 2.0), (2.05, 0.2, 0.18), PALETTE["wood_dark"])
