"""第三人称跟随相机：右键旋转、滚轮缩放、平滑跟随。"""

from __future__ import annotations

import math

from panda3d.core import NodePath, Vec3


class CameraRig:
    def __init__(
        self,
        camera: NodePath,
        *,
        yaw: float = 0.0,
        pitch: float = 0.42,
        distance: float = 7.5,
        min_pitch: float = 0.18,
        max_pitch: float = 1.15,
        min_distance: float = 4.0,
        max_distance: float = 11.0,
        sensitivity: float = 1.0,
    ) -> None:
        self.camera = camera
        self.yaw = float(yaw)
        self.pitch = float(pitch)
        self.distance = float(distance)
        self.min_pitch = min_pitch
        self.max_pitch = max_pitch
        self.min_distance = min_distance
        self.max_distance = max_distance
        self.sensitivity = sensitivity
        self._smooth_target = Vec3(0, 0, 0.8)
        self._initialized = False

    def orbit(self, dx: float, dy: float) -> None:
        self.yaw -= dx * 2.6 * self.sensitivity
        self.pitch = max(
            self.min_pitch, min(self.max_pitch, self.pitch + dy * 2.0 * self.sensitivity)
        )

    def zoom(self, amount: float) -> None:
        self.distance = max(
            self.min_distance, min(self.max_distance, self.distance + amount * 0.8)
        )

    def set_sensitivity(self, value: float) -> None:
        self.sensitivity = max(0.2, float(value))

    def update(self, dt: float, target_xy: tuple[float, float], target_z: float) -> None:
        desired = Vec3(target_xy[0], target_xy[1], target_z + 0.8)
        if not self._initialized:
            self._smooth_target = desired
            self._initialized = True
        factor = 1.0 - math.exp(-max(0.0, dt) * 8.0)
        self._smooth_target += (desired - self._smooth_target) * factor
        self._apply_camera()

    def snap_to(self, target_xy: tuple[float, float], target_z: float) -> None:
        """场景切换/读档后立即把镜头放到目标附近，避免跨场景漂移。"""
        self._smooth_target = Vec3(target_xy[0], target_xy[1], target_z + 0.8)
        self._initialized = True
        self._apply_camera()

    def _apply_camera(self) -> None:
        horiz = math.cos(self.pitch) * self.distance
        cam_pos = Vec3(
            self._smooth_target.x + math.sin(self.yaw) * horiz,
            self._smooth_target.y - math.cos(self.yaw) * horiz,
            self._smooth_target.z + math.sin(self.pitch) * self.distance,
        )
        # 简单的地面保护，避免镜头钻入地下。
        cam_pos.z = max(0.35, cam_pos.z)
        self.camera.setPos(cam_pos)
        self.camera.lookAt(self._smooth_target)
