"""网格导航：A* 寻路、最近可走点、视线平滑。

地面坐标为 Panda3D 的 X/Y；本模块不依赖 Panda3D，方便测试。
"""

from __future__ import annotations

import heapq
import math
from collections import deque
from typing import Iterable

Point = tuple[float, float]

_NEIGHBORS = (
    (1, 0, 1.0),
    (-1, 0, 1.0),
    (0, 1, 1.0),
    (0, -1, 1.0),
    (1, 1, math.sqrt(2)),
    (1, -1, math.sqrt(2)),
    (-1, 1, math.sqrt(2)),
    (-1, -1, math.sqrt(2)),
)


class NavGrid:
    def __init__(
        self,
        walkable: list[list[bool]],
        *,
        origin: Point = (0.0, 0.0),
        cell_size: float = 0.5,
    ) -> None:
        if not walkable or not walkable[0]:
            raise ValueError("导航网格不能为空")
        self.walkable = walkable
        self.origin = origin
        self.cell_size = float(cell_size)
        self.height = len(walkable)
        self.width = len(walkable[0])
        if any(len(row) != self.width for row in walkable):
            raise ValueError("导航网格每行宽度必须一致")

    def to_cell(self, point: Point) -> tuple[int, int]:
        return (
            int(math.floor((point[0] - self.origin[0]) / self.cell_size)),
            int(math.floor((point[1] - self.origin[1]) / self.cell_size)),
        )

    def to_world(self, cell: tuple[int, int]) -> Point:
        cx, cy = cell
        return (
            self.origin[0] + (cx + 0.5) * self.cell_size,
            self.origin[1] + (cy + 0.5) * self.cell_size,
        )

    def in_bounds(self, cell: tuple[int, int]) -> bool:
        cx, cy = cell
        return 0 <= cx < self.width and 0 <= cy < self.height

    def is_walkable_cell(self, cell: tuple[int, int]) -> bool:
        cx, cy = cell
        return self.in_bounds(cell) and bool(self.walkable[cy][cx])

    def is_walkable(self, point: Point) -> bool:
        return self.is_walkable_cell(self.to_cell(point))

    def nearest_walkable(self, point: Point, *, max_radius: int = 20) -> Point | None:
        start = self.to_cell(point)
        if self.is_walkable_cell(start):
            return self.to_world(start)
        seen = {start}
        queue: deque[tuple[tuple[int, int], int]] = deque([(start, 0)])
        while queue:
            cell, dist = queue.popleft()
            if dist >= max_radius:
                continue
            for dx, dy, _ in _NEIGHBORS:
                nxt = (cell[0] + dx, cell[1] + dy)
                if nxt in seen:
                    continue
                seen.add(nxt)
                if self.is_walkable_cell(nxt):
                    return self.to_world(nxt)
                queue.append((nxt, dist + 1))
        return None

    def line_of_sight(self, a: Point, b: Point) -> bool:
        distance = math.hypot(b[0] - a[0], b[1] - a[1])
        steps = max(1, int(distance / (self.cell_size * 0.5)))
        for i in range(steps + 1):
            t = i / steps
            x = a[0] + (b[0] - a[0]) * t
            y = a[1] + (b[1] - a[1]) * t
            if not self.is_walkable((x, y)):
                return False
        return True

    def find_path(self, start: Point, goal: Point) -> list[Point]:
        start_fixed = self.nearest_walkable(start)
        goal_fixed = self.nearest_walkable(goal)
        if start_fixed is None or goal_fixed is None:
            return []
        start_cell = self.to_cell(start_fixed)
        goal_cell = self.to_cell(goal_fixed)
        if start_cell == goal_cell:
            return [start_fixed]

        open_heap: list[tuple[float, tuple[int, int]]] = [(0.0, start_cell)]
        came_from: dict[tuple[int, int], tuple[int, int]] = {}
        g_score: dict[tuple[int, int], float] = {start_cell: 0.0}
        closed: set[tuple[int, int]] = set()

        while open_heap:
            _, current = heapq.heappop(open_heap)
            if current in closed:
                continue
            if current == goal_cell:
                cells = self._reconstruct(came_from, current)
                points = [self.to_world(cell) for cell in cells]
                if self.is_walkable(goal_fixed):
                    points[-1] = goal_fixed
                return self.smooth_path(points)
            closed.add(current)
            for dx, dy, cost in _NEIGHBORS:
                nxt = (current[0] + dx, current[1] + dy)
                if not self.is_walkable_cell(nxt):
                    continue
                # 禁止斜穿两个阻挡格之间的角。
                if dx and dy:
                    if not self.is_walkable_cell((current[0] + dx, current[1])):
                        continue
                    if not self.is_walkable_cell((current[0], current[1] + dy)):
                        continue
                tentative = g_score[current] + cost
                if tentative < g_score.get(nxt, math.inf):
                    came_from[nxt] = current
                    g_score[nxt] = tentative
                    f = tentative + _octile(nxt, goal_cell)
                    heapq.heappush(open_heap, (f, nxt))
        return []

    def smooth_path(self, points: Iterable[Point]) -> list[Point]:
        raw = list(points)
        if len(raw) <= 2:
            return raw
        result = [raw[0]]
        anchor = 0
        while anchor < len(raw) - 1:
            furthest = len(raw) - 1
            while furthest > anchor + 1 and not self.line_of_sight(raw[anchor], raw[furthest]):
                furthest -= 1
            result.append(raw[furthest])
            anchor = furthest
        return result

    def _reconstruct(
        self, came_from: dict[tuple[int, int], tuple[int, int]], current: tuple[int, int]
    ) -> list[tuple[int, int]]:
        cells = [current]
        while current in came_from:
            current = came_from[current]
            cells.append(current)
        cells.reverse()
        return cells


def _octile(a: tuple[int, int], b: tuple[int, int]) -> float:
    dx = abs(a[0] - b[0])
    dy = abs(a[1] - b[1])
    return (dx + dy) + (math.sqrt(2) - 2) * min(dx, dy)
