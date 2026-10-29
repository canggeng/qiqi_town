"""首版小镇场景：中心广场、家、幼儿园、图书馆与山脚。

后续会把这里拆成更细的场景数据；当前先提供可自由走动的纵切场景。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from panda3d.core import NodePath

from qiqi_town.config import PALETTE
from qiqi_town.world import meshkit
from qiqi_town.world.nav import NavGrid

WORLD_HALF = 35.0
CELL = 0.5


@dataclass
class TownScene:
    root: NodePath
    nav: NavGrid
    player_start: tuple[float, float] = (0.0, -8.0)
    interactables: list[dict] = field(default_factory=list)

    def height_at(self, x: float, y: float) -> float:
        return town_height(x, y)


def town_height(x: float, y: float) -> float:
    """地面高度：南侧平坦，北侧沿步道缓慢上升。"""
    if y < 15.0:
        return 0.0
    if y <= 30.0 and abs(x) <= 2.6:
        return min(6.0, (y - 15.0) / 15.0 * 6.0)
    if y > 30.0 and abs(x) <= 4.2:
        return 6.0
    return 0.0


def build_town(parent: NodePath) -> TownScene:
    root = parent.attachNewNode("town")
    blockers: list[tuple[float, float, float, float]] = []
    circles: list[tuple[float, float, float]] = []

    _build_ground(root)

    # 家：南边，门朝向广场。
    _build_house(
        root,
        name="home",
        center=(-10.0, -13.0),
        size=(7.0, 5.0),
        wall_color=(0.98, 0.86, 0.58, 1.0),
        roof_color=(0.91, 0.42, 0.36, 1.0),
        door_color=PALETTE["wood_dark"],
        window_color=(1.0, 0.87, 0.55, 1.0),
        sign_color=(0.95, 0.62, 0.44, 1.0),
    )
    blockers.append((-10.0, -13.0, 7.6, 5.6))

    # 幼儿园：东边。
    _build_house(
        root,
        name="kindergarten",
        center=(12.0, 6.0),
        size=(9.0, 6.0),
        wall_color=(0.78, 0.92, 0.84, 1.0),
        roof_color=(0.28, 0.56, 0.55, 1.0),
        door_color=(0.96, 0.63, 0.35, 1.0),
        window_color=(1.0, 0.92, 0.62, 1.0),
        sign_color=(0.98, 0.74, 0.36, 1.0),
    )
    blockers.append((12.0, 6.0, 9.6, 6.6))

    # 图书馆：西边。
    _build_house(
        root,
        name="library",
        center=(-14.0, 5.0),
        size=(7.5, 6.5),
        wall_color=(0.88, 0.76, 0.61, 1.0),
        roof_color=(0.43, 0.30, 0.23, 1.0),
        door_color=(0.50, 0.33, 0.22, 1.0),
        window_color=(1.0, 0.86, 0.56, 1.0),
        sign_color=(0.62, 0.76, 0.63, 1.0),
    )
    blockers.append((-14.0, 5.0, 8.1, 7.1))

    # 中心喷泉。
    _build_fountain(root, (0.0, 0.0))
    circles.append((0.0, 0.0, 2.25))

    # 公园与游乐场。
    _build_park(root, (18.0, -14.0))
    circles.append((18.0, -14.0, 3.6))
    _build_playground(root, (-20.0, -14.0))

    # 通往北侧山道的路。
    meshkit.add_box(root, "path_mountain", (0, 9.0, 0.018), (4.2, 14.0, 0.02), PALETTE["path"])
    _build_mountain_trail(root)
    # 山道两侧不可走。
    blockers.extend([])

    # 树、长椅、花。
    tree_positions = [
        (-20.0, -8.0, 1.0),
        (-5.0, 11.0, 1.1),
        (20.0, -6.0, 1.15),
        (22.0, 14.0, 0.9),
        (-23.0, 14.0, 1.0),
        (7.0, -13.0, 1.0),
        (-2.0, 18.0, 0.9),
        (18.0, 20.0, 1.1),
    ]
    for x, y, s in tree_positions:
        _build_tree(root, (x, y), s)
        circles.append((x, y, 0.55 * s))

    for x, y, h in [(-5.0, -3.0, 0.0), (5.0, -3.0, 180.0), (-5.0, 4.0, 90.0), (5.0, 4.0, -90.0)]:
        _build_bench(root, (x, y), h)

    for i in range(18):
        angle = i * 2.4
        radius = 10 + (i % 4) * 1.2
        x = math.cos(angle) * radius
        y = math.sin(angle) * radius
        _build_flower(root, (x, y), i)

    # 远处山体。
    for x, y, h, color in [
        (-12.0, 30.0, 16.0, (0.42, 0.57, 0.46, 1.0)),
        (12.0, 32.0, 18.0, (0.35, 0.50, 0.43, 1.0)),
        (-26.0, 46.0, 20.0, (0.42, 0.57, 0.46, 1.0)),
        (2.0, 52.0, 26.0, (0.35, 0.50, 0.43, 1.0)),
        (27.0, 47.0, 18.0, (0.45, 0.59, 0.48, 1.0)),
    ]:
        meshkit.add_cylinder(
            root,
            "mountain",
            (x, y, 0),
            12.0 if y < 40 else 14.0,
            0.0,
            h,
            color,
            segments=7,
        )

    # 云朵。
    for x, y, z, s in [(-18, 26, 20, 1.2), (8, 30, 22, 1.4), (26, 24, 19, 1.0)]:
        for dx, dy, dz, r in [
            (0, 0, 0, 2.2 * s),
            (2.2 * s, 0.2, 0.2, 1.6 * s),
            (-2.0 * s, -0.3, 0.1, 1.4 * s),
        ]:
            meshkit.add_sphere(
                root,
                "cloud",
                (x + dx, y + dy, z + dz),
                r,
                (0.99, 0.98, 0.94, 0.85),
                rings=8,
                segments=12,
                scale=(1.2, 0.8, 0.55),
                alpha=0.85,
            )

    nav = _make_nav(blockers, circles)
    return TownScene(root=root, nav=nav, player_start=(0.0, -8.0))


def _build_ground(root: NodePath) -> None:
    meshkit.add_box(
        root, "ground", (0, 0, -0.55), (WORLD_HALF * 2, WORLD_HALF * 2, 1.1), PALETTE["grass"]
    )
    # 草坪色块，增加层次。
    for i, (x, y, w, h) in enumerate([(-18, 18, 9, 8), (17, 17, 8, 9), (24, -12, 7, 6)]):
        meshkit.add_box(
            root,
            f"lawn_{i}",
            (x, y, 0.005),
            (w, h, 0.01),
            PALETTE["grass_light"] if i % 2 == 0 else (0.62, 0.82, 0.55, 1.0),
        )

    # 主路：南北与东西。
    path_color = PALETTE["path"]
    meshkit.add_box(root, "path_ns", (0, 0, 0.015), (5.0, 56.0, 0.02), path_color)
    meshkit.add_box(root, "path_ew", (0, 0, 0.016), (48.0, 4.0, 0.02), path_color)
    meshkit.add_disc(root, "plaza", (0, 0, 0.02), 8.5, (0.91, 0.83, 0.68, 1.0), segments=48)
    meshkit.add_disc(root, "plaza_inner", (0, 0, 0.026), 6.0, (0.95, 0.89, 0.76, 1.0), segments=40)

    # 边界矮篱笆。
    for side in (-1, 1):
        meshkit.add_box(
            root, "fence_ns", (side * (WORLD_HALF - 0.4), 0, 0.35), (0.35, WORLD_HALF * 2, 0.7), PALETTE["wood"]
        )
        meshkit.add_box(
            root, "fence_ew", (0, side * (WORLD_HALF - 0.4), 0.35), (WORLD_HALF * 2, 0.35, 0.7), PALETTE["wood"]
        )


def _build_house(
    root: NodePath,
    *,
    name: str,
    center: tuple[float, float],
    size: tuple[float, float],
    wall_color: tuple[float, float, float, float],
    roof_color: tuple[float, float, float, float],
    door_color: tuple[float, float, float, float],
    window_color: tuple[float, float, float, float],
    sign_color: tuple[float, float, float, float],
) -> None:
    x, y = center
    w, d = size
    group = root.attachNewNode(name)
    group.setPythonTag("building", name)
    meshkit.add_box(group, "walls", (x, y, 1.6), (w, d, 3.2), wall_color)
    meshkit.add_pyramid(group, "roof", (x, y, 3.2), (w + 1.2, d + 1.2), 2.1, roof_color)
    # 门朝南（-Y），玩家从广场方向进入。
    meshkit.add_box(group, "door", (x, y - d / 2 - 0.06, 0.8), (1.2, 0.12, 1.6), door_color)
    meshkit.add_box(group, "step", (x, y - d / 2 - 0.45, 0.09), (1.7, 0.7, 0.18), PALETTE["stone"])
    # 窗。
    for wx in (-w * 0.28, w * 0.28):
        meshkit.add_box(
            group, "window", (x + wx, y - d / 2 - 0.07, 1.9), (1.15, 0.1, 0.95), window_color
        )
        meshkit.add_box(
            group,
            "window_frame",
            (x + wx, y - d / 2 - 0.13, 1.9),
            (1.3, 0.06, 1.1),
            (0.98, 0.93, 0.82, 1.0),
        )
        meshkit.add_box(
            group,
            "window_mullion",
            (x + wx, y - d / 2 - 0.14, 1.9),
            (0.07, 0.05, 1.0),
            PALETTE["wood"],
        )
    # 屋檐下的招牌/装饰。
    meshkit.add_box(
        group, "door_canopy", (x, y - d / 2 - 0.45, 2.55), (2.5, 0.9, 0.12), sign_color
    )
    meshkit.add_box(group, "chimney", (x + w * 0.28, y + d * 0.2, 5.2), (0.6, 0.6, 1.6), PALETTE["stone"])


def _build_park(root: NodePath, center: tuple[float, float]) -> None:
    x, y = center
    group = root.attachNewNode("park")
    meshkit.add_disc(group, "park_lawn", (x, y, 0.012), 9.0, (0.63, 0.82, 0.56, 1.0), segments=40)
    # 池塘
    meshkit.add_cylinder(group, "pond_rim", (x, y, 0.02), 3.8, 3.8, 0.22, PALETTE["stone"], segments=36)
    meshkit.add_disc(group, "pond_water", (x, y, 0.25), 3.45, PALETTE["water"], segments=36)
    for i in range(8):
        angle = i * math.pi / 4
        px = x + math.cos(angle) * 3.9
        py = y + math.sin(angle) * 3.9
        meshkit.add_sphere(group, "reed", (px, py, 0.55), 0.035, PALETTE["leaf"], rings=4, segments=6)
        meshkit.add_box(group, "reed_leaf", (px, py, 0.85), (0.05, 0.28, 0.4), PALETTE["leaf_light"])
    # 鸭子一家
    for dx, dy in [(-1.8, -2.4), (0.2, -3.0), (1.8, -2.1)]:
        duck = group.attachNewNode("duck")
        meshkit.add_sphere(duck, "duck_body", (x + dx, y + dy, 0.45), 0.24, (0.98, 0.95, 0.86, 1.0), rings=8, segments=12, scale=(1.2, 0.9, 0.7))
        meshkit.add_sphere(duck, "duck_head", (x + dx + 0.18, y + dy, 0.68), 0.14, (0.98, 0.95, 0.86, 1.0), rings=7, segments=10)
        meshkit.add_box(duck, "duck_beak", (x + dx + 0.33, y + dy, 0.66), (0.16, 0.09, 0.06), PALETTE["honey"])
    _build_bench(root, (x - 5.0, y + 2.0), 90.0)
    _build_bench(root, (x + 5.0, y - 1.5), -90.0)
    _build_tree(root, (x - 7.0, y - 5.0), 0.9)
    _build_tree(root, (x + 7.0, y + 5.0), 1.0)
    for i in range(9):
        angle = i * 1.7
        px = x + math.cos(angle) * (5.0 + (i % 3) * 0.8)
        py = y + math.sin(angle) * (5.2 + (i % 2) * 0.8)
        _build_flower(root, (px, py), i)


def _build_playground(root: NodePath, center: tuple[float, float]) -> None:
    x, y = center
    group = root.attachNewNode("playground")
    meshkit.add_disc(group, "sandbox", (x, y, 0.02), 4.6, (0.94, 0.82, 0.59, 1.0), segments=36)
    meshkit.add_cylinder(group, "sandbox_rim", (x, y, 0.02), 4.75, 4.75, 0.14, PALETTE["wood"], segments=36)
    # 滑梯：平台、梯子、滑道
    meshkit.add_box(group, "slide_platform", (x - 1.8, y + 1.2, 1.6), (1.6, 1.6, 0.18), PALETTE["teal"])
    for lx in (-2.4, -1.2):
        meshkit.add_box(group, "slide_post", (x + lx, y + 0.6, 0.8), (0.15, 0.15, 1.6), PALETTE["wood_dark"])
    for i in range(4):
        meshkit.add_box(group, "ladder_rung", (x - 1.8, y + 0.1 + i * 0.3, 0.35 + i * 0.32), (1.0, 0.08, 0.06), PALETTE["wood"])
    slide = meshkit.add_box(group, "slide_board", (x - 1.8, y + 2.7, 0.9), (1.2, 3.2, 0.15), PALETTE["honey"])
    slide.setP(-22)
    meshkit.add_box(group, "slide_side_l", (x - 2.38, y + 2.7, 1.05), (0.08, 3.2, 0.3), PALETTE["teal"]).setP(-22)
    meshkit.add_box(group, "slide_side_r", (x - 1.22, y + 2.7, 1.05), (0.08, 3.2, 0.3), PALETTE["teal"]).setP(-22)
    # 秋千
    swing_x = x + 2.8
    swing_y = y - 0.8
    for sx in (-1.3, 1.3):
        for sy in (-1.2, 1.2):
            post = meshkit.add_box(group, "swing_post", (swing_x + sx, swing_y + sy, 1.4), (0.12, 0.12, 2.8), PALETTE["teal"])
            post.setR(12 if sx < 0 else -12)
    meshkit.add_box(group, "swing_bar", (swing_x, swing_y, 2.75), (3.0, 0.12, 0.12), PALETTE["teal"])
    for sx in (-0.55, 0.55):
        meshkit.add_box(group, "swing_rope", (swing_x + sx, swing_y, 1.7), (0.03, 0.03, 2.1), PALETTE["wood_dark"])
        meshkit.add_box(group, "swing_seat", (swing_x + sx, swing_y, 0.72), (0.45, 0.22, 0.08), PALETTE["coral"])
    # 跷跷板
    meshkit.add_box(group, "seesaw_plank", (x + 2.0, y + 2.8, 0.55), (3.2, 0.25, 0.12), PALETTE["coral"])
    meshkit.add_box(group, "seesaw_fulcrum", (x + 2.0, y + 2.8, 0.25), (0.4, 0.4, 0.5), PALETTE["stone"])
    # 沙坑玩具
    for i in range(4):
        meshkit.add_box(group, "sand_toy", (x - 3.0 + i * 0.5, y - 2.0, 0.18), (0.25, 0.25, 0.25), [PALETTE["coral"], PALETTE["teal"], PALETTE["honey"], PALETTE["leaf"]][i])
    _build_bench(root, (x - 6.0, y + 3.0), 90.0)


def _build_mountain_trail(root: NodePath) -> None:
    group = root.attachNewNode("mountain_trail")
    # 登山步道：视觉台阶 + 侧面扶手。
    for i in range(16):
        y = 15.5 + i
        h = town_height(0.0, y)
        meshkit.add_box(group, "trail_step", (0, y, h / 2), (4.6, 1.05, max(0.08, h)), PALETTE["path"])
        if i % 2 == 0:
            for x in (-2.35, 2.35):
                meshkit.add_box(group, "trail_post", (x, y, h + 0.45), (0.1, 0.1, 0.9), PALETTE["wood"])
                meshkit.add_box(group, "trail_rail", (x, y, h + 0.85), (0.08, 2.0, 0.08), PALETTE["wood"])
    # 山脚指示牌
    meshkit.add_box(group, "trail_sign_post", (2.8, 14.8, 0.8), (0.12, 0.12, 1.6), PALETTE["wood_dark"])
    meshkit.add_box(group, "trail_sign", (2.8, 14.8, 1.5), (1.8, 0.12, 0.7), PALETTE["honey"])
    # 山顶平台与灯柱
    meshkit.add_box(group, "summit", (0, 32.0, 5.95), (8.5, 6.0, 0.35), PALETTE["stone"])
    meshkit.add_box(group, "summit_rail_n", (0, 34.8, 6.7), (8.5, 0.1, 0.8), PALETTE["wood"])
    for x in (-3.8, 3.8):
        meshkit.add_box(group, "summit_lantern_post", (x, 33.8, 6.8), (0.12, 0.12, 1.4), PALETTE["wood_dark"])
        meshkit.add_sphere(group, "summit_lantern", (x, 33.8, 7.55), 0.22, PALETTE["lantern"], rings=8, segments=12)
    _build_bench(root, (0, 33.6), 180.0)


def _build_fountain(root: NodePath, center: tuple[float, float]) -> None:
    x, y = center
    group = root.attachNewNode("fountain")
    meshkit.add_cylinder(group, "basin", (x, y, 0.05), 2.2, 2.0, 0.45, PALETTE["stone"], segments=28)
    meshkit.add_disc(group, "water", (x, y, 0.5), 1.75, PALETTE["water"], segments=28)
    meshkit.add_cylinder(group, "column", (x, y, 0.45), 0.35, 0.25, 1.1, (0.82, 0.81, 0.76, 1.0), segments=16)
    meshkit.add_sphere(group, "top", (x, y, 1.65), 0.35, PALETTE["water"], rings=10, segments=14)
    for i in range(6):
        angle = i * math.pi / 3
        px = x + math.cos(angle) * 1.25
        py = y + math.sin(angle) * 1.25
        meshkit.add_sphere(group, "droplet", (px, py, 0.75), 0.09, (0.78, 0.92, 0.96, 0.9), rings=5, segments=8)


def _build_tree(root: NodePath, center: tuple[float, float], scale: float) -> None:
    x, y = center
    group = root.attachNewNode("tree")
    meshkit.add_cylinder(group, "trunk", (x, y, 0), 0.22 * scale, 0.16 * scale, 2.0 * scale, PALETTE["wood"], segments=10)
    meshkit.add_sphere(
        group,
        "canopy",
        (x, y, 2.5 * scale),
        1.35 * scale,
        PALETTE["leaf"],
        rings=10,
        segments=14,
        scale=(1.0, 0.9, 0.85),
    )
    meshkit.add_sphere(
        group,
        "canopy_light",
        (x - 0.55 * scale, y - 0.25 * scale, 2.75 * scale),
        0.85 * scale,
        PALETTE["leaf_light"],
        rings=8,
        segments=12,
    )


def _build_bench(root: NodePath, center: tuple[float, float], heading: float) -> None:
    x, y = center
    group = root.attachNewNode("bench")
    group.setPos(x, y, 0)
    group.setH(heading)
    meshkit.add_box(group, "seat", (0, 0, 0.48), (2.0, 0.55, 0.12), PALETTE["wood"])
    meshkit.add_box(group, "back", (0, -0.24, 0.82), (2.0, 0.1, 0.55), PALETTE["wood"])
    for lx in (-0.75, 0.75):
        meshkit.add_box(group, "leg", (lx, 0, 0.24), (0.1, 0.45, 0.48), PALETTE["wood_dark"])


def _build_flower(root: NodePath, center: tuple[float, float], index: int) -> None:
    x, y = center
    colors = [PALETTE["coral"], PALETTE["honey"], (0.92, 0.63, 0.82, 1.0), PALETTE["white"]]
    meshkit.add_cylinder(root, "stem", (x, y, 0.02), 0.015, 0.012, 0.35, PALETTE["leaf"], segments=6)
    meshkit.add_sphere(
        root,
        "petal",
        (x, y, 0.4),
        0.095,
        colors[index % len(colors)],
        rings=6,
        segments=8,
        scale=(1.0, 1.0, 0.55),
    )


def _make_nav(
    blockers: list[tuple[float, float, float, float]],
    circles: list[tuple[float, float, float]],
) -> NavGrid:
    cells = int((WORLD_HALF * 2) / CELL)
    grid = [[True for _ in range(cells)] for _ in range(cells)]
    # 边界两格不可走。
    for i in range(cells):
        for border in range(3):
            grid[border][i] = False
            grid[cells - 1 - border][i] = False
            grid[i][border] = False
            grid[i][cells - 1 - border] = False

    def world_to_cell(x: float, y: float) -> tuple[int, int]:
        return int((x + WORLD_HALF) / CELL), int((y + WORLD_HALF) / CELL)

    for cx, cy, w, d in blockers:
        x0, y0 = world_to_cell(cx - w / 2, cy - d / 2)
        x1, y1 = world_to_cell(cx + w / 2, cy + d / 2)
        for gy in range(max(0, y0), min(cells, y1 + 1)):
            for gx in range(max(0, x0), min(cells, x1 + 1)):
                grid[gy][gx] = False

    for cx, cy, radius in circles:
        x0, y0 = world_to_cell(cx - radius, cy - radius)
        x1, y1 = world_to_cell(cx + radius, cy + radius)
        for gy in range(max(0, y0), min(cells, y1 + 1)):
            for gx in range(max(0, x0), min(cells, x1 + 1)):
                wx = -WORLD_HALF + (gx + 0.5) * CELL
                wy = -WORLD_HALF + (gy + 0.5) * CELL
                if math.hypot(wx - cx, wy - cy) <= radius:
                    grid[gy][gx] = False

    # 北侧山体只保留步道与山顶平台可走。
    for gy in range(cells):
        wy = -WORLD_HALF + (gy + 0.5) * CELL
        if wy <= 15.0:
            continue
        for gx in range(cells):
            wx = -WORLD_HALF + (gx + 0.5) * CELL
            on_trail = wy <= 30.0 and abs(wx) <= 2.6
            on_summit = 30.0 < wy <= 34.2 and abs(wx) <= 4.2
            if not (on_trail or on_summit):
                grid[gy][gx] = False

    return NavGrid(grid, origin=(-WORLD_HALF, -WORLD_HALF), cell_size=CELL)
