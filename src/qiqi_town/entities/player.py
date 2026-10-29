"""玩家控制：点击寻路、沿路径移动、朝向与角色动画。"""

from __future__ import annotations

import math

from panda3d.core import NodePath

from qiqi_town.world.character_builder import CharacterRig
from qiqi_town.world.nav import NavGrid, Point


class PlayerController:
    def __init__(
        self,
        parent: NodePath,
        rig: CharacterRig,
        nav: NavGrid,
        *,
        speed: float = 2.4,
        height_fn=None,
    ) -> None:
        self.rig = rig
        self.nav = nav
        self.speed = float(speed)
        self.height_fn = height_fn or (lambda x, y: 0.0)
        self.root = rig.root
        self._path: list[Point] = []
        self._target_index = 0
        self._moving = False
        self._heading = 0.0
        self._position = (0.0, 0.0)
        self.set_position(0.0, 0.0, 0.0)
        self._path_dirty = False

    @property
    def position(self) -> Point:
        return self._position

    @property
    def z(self) -> float:
        return float(self.height_fn(*self._position))

    @property
    def moving(self) -> bool:
        return self._moving

    @property
    def facing(self) -> float:
        return self._heading

    def set_position(self, x: float, y: float, facing: float = 0.0) -> None:
        self._position = (float(x), float(y))
        self._heading = float(facing)
        self.root.setPos(self._position[0], self._position[1], self.height_fn(*self._position))
        self.root.setH(math.degrees(self._heading))
        self._path = []
        self._moving = False

    def move_to(self, target: Point) -> bool:
        path = self.nav.find_path(self._position, target)
        if not path:
            return False
        self._path = path
        self._target_index = 0
        self._moving = True
        # 如果第一个点就是当前位置，直接跳过。
        if len(path) > 1 and _dist(path[0], self._position) < 0.12:
            self._target_index = 1
        return True

    def stop(self) -> None:
        self._path = []
        self._moving = False

    def update(self, dt: float) -> None:
        if self._moving and self._target_index < len(self._path):
            target = self._path[self._target_index]
            current = self._position
            dx = target[0] - current[0]
            dy = target[1] - current[1]
            distance = math.hypot(dx, dy)
            if distance < 0.06:
                self._target_index += 1
                if self._target_index >= len(self._path):
                    self._moving = False
                    self._path = []
            else:
                step = min(distance, self.speed * dt)
                nx = current[0] + dx / distance * step
                ny = current[1] + dy / distance * step
                self._position = (nx, ny)
                self.root.setPos(nx, ny, self.height_fn(nx, ny))
                desired = math.atan2(dx, dy)
                self._heading = _approach_angle(self._heading, desired, dt * 10.0)
                self.root.setH(math.degrees(self._heading))

        self.rig.update(dt, self._moving)


def _dist(a: Point, b: Point) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _approach_angle(current: float, target: float, max_delta: float) -> float:
    diff = (target - current + math.pi) % (2 * math.pi) - math.pi
    if abs(diff) <= max_delta:
        return target
    return current + math.copysign(max_delta, diff)
