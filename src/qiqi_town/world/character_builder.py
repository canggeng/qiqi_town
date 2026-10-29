"""淇淇与小镇居民的程序化角色拼装。

淇淇的外观参考：黑色齐刘海短发、奶白蕾丝头巾、白色无袖连衣裙、红色大气球。
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from panda3d.core import LineSegs, NodePath, TransparencyAttrib

from qiqi_town.config import PALETTE
from qiqi_town.world import meshkit


@dataclass
class CharacterRig:
    root: NodePath
    body: NodePath
    head: NodePath
    arm_l: NodePath
    arm_r: NodePath
    leg_l: NodePath
    leg_r: NodePath
    balloon: NodePath
    eye_l: NodePath
    eye_r: NodePath
    mouth: NodePath
    shadow: NodePath
    balloon_base_z: float
    _time: float = 0.0
    _blink_clock: float = 2.8
    _blink_remaining: float = 0.0
    _moving: bool = False
    _blink_visible: bool = True
    _expression: str = "happy"
    _walk_phase: float = 0.0

    def update(self, dt: float, moving: bool) -> None:
        self._time += max(0.0, dt)
        self._moving = moving
        if moving:
            self._walk_phase += dt * 8.0
        else:
            self._walk_phase += dt * 0.8

        bob = 0.0
        if moving:
            bob = abs(math.sin(self._walk_phase)) * 0.018
            swing = math.sin(self._walk_phase) * 24.0
            self.leg_l.setP(swing)
            self.leg_r.setP(-swing)
            self.arm_l.setP(-swing * 0.7)
            self.arm_r.setP(swing * 0.7)
        else:
            self.leg_l.setP(0.0)
            self.leg_r.setP(0.0)
            breathe = math.sin(self._time * 1.5) * 2.0
            self.arm_l.setP(breathe)
            self.arm_r.setP(-breathe)
        self.body.setZ(bob)

        # 气球轻轻浮动，并有一点滞后感。
        balloon_z = self.balloon_base_z + math.sin(self._time * 1.4) * 0.028
        if moving:
            balloon_z += math.sin(self._walk_phase * 0.5) * 0.01
        self.balloon.setZ(balloon_z)
        self.balloon.setR(math.sin(self._time * 1.1) * 3.0)

        # 眨眼。
        self._blink_clock -= dt
        if self._blink_remaining > 0:
            self._blink_remaining -= dt
            if self._blink_remaining <= 0:
                self.eye_l.setScale(1, 1, 1)
                self.eye_r.setScale(1, 1, 1)
        elif self._blink_clock <= 0:
            self._blink_clock = 3.2 + (self._time % 1.7)
            self._blink_remaining = 0.11
            self.eye_l.setScale(1, 1, 0.12)
            self.eye_r.setScale(1, 1, 0.12)

    def set_expression(self, name: str) -> None:
        self._expression = name
        if name == "surprised":
            self.mouth.setScale(1.0, 1.0, 2.0)
        elif name == "sad":
            self.mouth.setScale(1.2, 1.0, 0.6)
            self.mouth.setR(12)
        elif name == "shy":
            self.mouth.setScale(0.8, 1.0, 0.8)
        else:
            self.mouth.setScale(1.0, 1.0, 1.0)
            self.mouth.setR(0)

    def set_balloon_visible(self, visible: bool) -> None:
        if visible:
            self.balloon.show()
        else:
            self.balloon.hide()


def build_qiqi(parent: NodePath) -> CharacterRig:
    """构建淇淇。父节点坐标即脚底位置，朝向 +Y。"""
    root = parent.attachNewNode("qiqi")
    root.setPythonTag("actor", "qiqi")

    # 柔和圆形假阴影。
    shadow = meshkit.add_disc(
        root,
        "qiqi_shadow",
        (0, 0, 0.012),
        0.34,
        PALETTE["shadow"],
        segments=24,
        alpha=0.30,
    )
    shadow.setTransparency(TransparencyAttrib.MAlpha)
    shadow.setDepthWrite(False)
    shadow.setBin("transparent", 0)

    body = root.attachNewNode("qiqi_body")

    # 腿与鞋（腿部节点放在髋部，便于摆动）。
    leg_l = root.attachNewNode("leg_l")
    leg_l.setPos(-0.075, 0.0, 0.35)
    leg_r = root.attachNewNode("leg_r")
    leg_r.setPos(0.075, 0.0, 0.35)
    for leg in (leg_l, leg_r):
        meshkit.add_cylinder(leg, "leg", (0, 0, -0.27), 0.042, 0.045, 0.27, PALETTE["skin"])
        meshkit.add_box(leg, "shoe", (0, 0.025, -0.285), (0.11, 0.19, 0.075), (0.72, 0.12, 0.12, 1.0))
        meshkit.add_box(leg, "sole", (0, 0.025, -0.31), (0.115, 0.20, 0.025), (0.35, 0.12, 0.10, 1.0))

    # 白色 A 字裙。
    meshkit.add_cylinder(
        body, "dress", (0, 0, 0.28), 0.285, 0.15, 0.42, PALETTE["cream"], segments=24
    )
    meshkit.add_cylinder(
        body, "dress_hem", (0, 0, 0.275), 0.298, 0.288, 0.045, PALETTE["lace"], segments=24
    )
    # 裙摆上的轻微褶皱线。
    for i in range(8):
        phi = 2 * math.pi * i / 8
        x = math.cos(phi) * 0.24
        y = math.sin(phi) * 0.24
        meshkit.add_line(
            body,
            "dress_seam",
            (x * 0.55, y * 0.55, 0.62),
            (x, y, 0.30),
            (0.94, 0.90, 0.82, 1.0),
            thickness=1.0,
        )

    # 胸口/脖子。
    meshkit.add_cylinder(body, "chest", (0, 0, 0.65), 0.145, 0.16, 0.11, PALETTE["cream"], segments=18)
    meshkit.add_cylinder(body, "neck", (0, 0, 0.755), 0.055, 0.05, 0.07, PALETTE["skin"], segments=14)

    # 手臂：肩部枢轴 + 下垂的圆柱。
    arm_l = body.attachNewNode("arm_l")
    arm_l.setPos(-0.185, 0.0, 0.70)
    arm_l.setR(-8)
    arm_r = body.attachNewNode("arm_r")
    arm_r.setPos(0.185, 0.0, 0.70)
    arm_r.setR(8)
    for arm in (arm_l, arm_r):
        meshkit.add_cylinder(arm, "arm", (0, 0, -0.27), 0.042, 0.047, 0.27, PALETTE["skin"], segments=12)
        meshkit.add_sphere(arm, "hand", (0, 0.005, -0.285), 0.055, PALETTE["skin"], rings=8, segments=12)

    # 头部。
    head = body.attachNewNode("head")
    head.setPos(0, 0, 0.965)
    meshkit.add_sphere(head, "face", (0, 0.02, 0), 0.20, PALETTE["skin"], rings=16, segments=22)
    meshkit.add_sphere(
        head, "hair_back", (0, -0.045, 0.015), 0.207, PALETTE["hair"], rings=14, segments=20
    )
    # 齐刘海。
    meshkit.add_sphere(
        head,
        "bangs",
        (0, 0.13, 0.145),
        0.172,
        PALETTE["hair"],
        rings=10,
        segments=18,
        scale=(1.0, 0.38, 0.35),
    )
    # 内扣侧发。
    meshkit.add_sphere(
        head,
        "side_hair_l",
        (-0.175, 0.02, -0.055),
        0.16,
        PALETTE["hair"],
        rings=10,
        segments=14,
        scale=(0.45, 0.75, 1.0),
    )
    meshkit.add_sphere(
        head,
        "side_hair_r",
        (0.175, 0.02, -0.055),
        0.16,
        PALETTE["hair"],
        rings=10,
        segments=14,
        scale=(0.45, 0.75, 1.0),
    )

    # 蕾丝头巾：后部布面 + 面部周围的花边 + 下巴系带。
    meshkit.add_sphere(
        head,
        "bonnet",
        (0, -0.115, 0.035),
        0.235,
        PALETTE["lace"],
        rings=12,
        segments=18,
        scale=(1.08, 0.62, 1.04),
    )
    _add_lace_ring(head, y=0.165, radius_x=0.215, radius_z=0.225)
    # 系带
    meshkit.add_line(
        head, "bonnet_tie_l", (-0.14, 0.15, -0.13), (0.0, 0.20, -0.29), PALETTE["lace"], thickness=3.0
    )
    meshkit.add_line(
        head, "bonnet_tie_r", (0.14, 0.15, -0.13), (0.0, 0.20, -0.29), PALETTE["lace"], thickness=3.0
    )
    meshkit.add_sphere(
        head, "bow_l", (-0.035, 0.205, -0.295), 0.032, PALETTE["lace"], rings=6, segments=10, scale=(1.0, 0.5, 0.8)
    )
    meshkit.add_sphere(
        head, "bow_r", (0.035, 0.205, -0.295), 0.032, PALETTE["lace"], rings=6, segments=10, scale=(1.0, 0.5, 0.8)
    )

    # 眼睛：眼白 + 虹膜 + 高光；两种眼睛节点用于眨眼。
    eye_l = head.attachNewNode("eye_l")
    eye_l.setPos(-0.068, 0.205, 0.035)
    eye_r = head.attachNewNode("eye_r")
    eye_r.setPos(0.068, 0.205, 0.035)
    for eye in (eye_l, eye_r):
        meshkit.add_sphere(eye, "sclera", (0, 0, 0), 0.050, PALETTE["white"], rings=8, segments=12, scale=(1.0, 0.5, 1.2))
        meshkit.add_sphere(eye, "iris", (0, 0.018, 0.002), 0.036, PALETTE["eye"], rings=8, segments=12, scale=(1.0, 0.4, 1.15))
        meshkit.add_sphere(
            eye, "pupil", (0, 0.031, 0.002), 0.019, (0.05, 0.03, 0.02, 1.0), rings=6, segments=10, scale=(1.0, 0.3, 1.1)
        )
        meshkit.add_sphere(
            eye, "glint", (0.014, 0.041, 0.024), 0.011, PALETTE["white"], rings=5, segments=8, scale=(1.0, 0.4, 1.0)
        )
        meshkit.add_sphere(
            eye, "glint_small", (-0.013, 0.041, -0.013), 0.005, PALETTE["white"], rings=4, segments=6
        )

    # 眉毛。
    for x in (-0.07, 0.07):
        meshkit.add_box(head, "brow", (x, 0.205, 0.105), (0.07, 0.012, 0.014), PALETTE["hair"])

    # 鼻子与嘴。
    meshkit.add_sphere(head, "nose", (0, 0.225, 0.0), 0.018, PALETTE["skin_shadow"], rings=6, segments=8)
    mouth = meshkit.add_box(head, "mouth", (0, 0.225, -0.075), (0.055, 0.014, 0.014), (0.64, 0.25, 0.22, 1.0))

    # 腮红。
    for x in (-0.115, 0.115):
        meshkit.add_sphere(
            head,
            "blush",
            (x, 0.205, -0.025),
            0.034,
            (0.96, 0.55, 0.52, 1.0),
            rings=6,
            segments=10,
            scale=(1.15, 0.25, 0.55),
            alpha=0.75,
        )

    # 红气球：挂在身体侧上方，带细绳。
    balloon = root.attachNewNode("balloon")
    balloon_base_z = 1.30
    balloon.setPos(0.46, 0.06, balloon_base_z)
    meshkit.add_sphere(balloon, "balloon", (0, 0, 0), 0.27, PALETTE["balloon"], rings=16, segments=20)
    meshkit.add_sphere(
        balloon, "balloon_glint", (-0.08, 0.16, 0.10), 0.035, (1.0, 0.55, 0.50, 1.0), rings=5, segments=8
    )
    meshkit.add_line(
        root,
        "balloon_string",
        (0.25, 0.02, 0.55),
        (0.46, 0.06, 0.98),
        (0.95, 0.90, 0.78, 1.0),
        thickness=1.0,
    )

    return CharacterRig(
        root=root,
        body=body,
        head=head,
        arm_l=arm_l,
        arm_r=arm_r,
        leg_l=leg_l,
        leg_r=leg_r,
        balloon=balloon,
        eye_l=eye_l,
        eye_r=eye_r,
        mouth=mouth,
        shadow=shadow,
        balloon_base_z=balloon_base_z,
    )


def _add_lace_ring(head: NodePath, *, y: float, radius_x: float, radius_z: float) -> None:
    segs = LineSegs("bonnet_lace")
    segs.setThickness(3.0)
    segs.setColor(1.0, 0.99, 0.95, 1.0)
    points = 40
    for i in range(points):
        angle = 2 * math.pi * i / points
        x = math.cos(angle) * radius_x
        z = math.sin(angle) * radius_z
        if i == 0:
            segs.moveTo(x, y, z)
        else:
            segs.drawTo(x, y, z)
    segs.drawTo(radius_x, y, 0.0)
    head.attachNewNode(segs.create())

    # 花边的小圆点，增加蕾丝感。
    for i in range(20):
        angle = 2 * math.pi * i / 20
        x = math.cos(angle) * radius_x
        z = math.sin(angle) * radius_z
        meshkit.add_sphere(
            head,
            "lace_dot",
            (x, y + 0.008, z),
            0.014,
            PALETTE["lace"],
            rings=4,
            segments=6,
            scale=(1.0, 0.4, 1.0),
        )


@dataclass
class VillagerRig:
    root: NodePath
    body: NodePath
    head: NodePath
    arm_l: NodePath
    arm_r: NodePath
    leg_l: NodePath
    leg_r: NodePath
    _time: float = 0.0

    def update(self, dt: float, talking: bool = False) -> None:
        self._time += max(0.0, dt)
        breathe = math.sin(self._time * 1.4) * 1.8
        self.body.setZ(abs(math.sin(self._time * 1.2)) * 0.006)
        self.arm_l.setP(breathe)
        self.arm_r.setP(-breathe)
        if talking:
            self.head.setR(math.sin(self._time * 8.0) * 2.0)
        else:
            self.head.setR(0.0)


def build_villager(
    parent: NodePath,
    *,
    name: str,
    dress_color: tuple[float, float, float, float],
    hair_color: tuple[float, float, float, float],
    skin_color: tuple[float, float, float, float] | None = None,
    height_scale: float = 1.0,
    hairstyle: str = "bob",
    accessory: str | None = None,
) -> VillagerRig:
    """用同一套基础部件拼出一个居民。"""
    skin = skin_color or PALETTE["skin"]
    root = parent.attachNewNode(name)
    root.setPythonTag("actor", name)
    root.setScale(height_scale)
    body = root.attachNewNode("body")

    leg_l = root.attachNewNode("leg_l")
    leg_l.setPos(-0.07, 0, 0.34)
    leg_r = root.attachNewNode("leg_r")
    leg_r.setPos(0.07, 0, 0.34)
    for leg in (leg_l, leg_r):
        meshkit.add_cylinder(leg, "leg", (0, 0, -0.26), 0.04, 0.045, 0.26, skin)
        meshkit.add_box(leg, "shoe", (0, 0.02, -0.275), (0.105, 0.18, 0.07), PALETTE["wood_dark"])

    # 衣服/裙摆。
    meshkit.add_cylinder(body, "clothes", (0, 0, 0.27), 0.26, 0.16, 0.43, dress_color, segments=20)
    meshkit.add_cylinder(body, "hem", (0, 0, 0.265), 0.27, 0.26, 0.025, (0.95, 0.90, 0.80, 1.0), segments=20)
    meshkit.add_cylinder(body, "torso", (0, 0, 0.64), 0.15, 0.15, 0.13, dress_color, segments=16)
    meshkit.add_cylinder(body, "neck", (0, 0, 0.76), 0.05, 0.045, 0.06, skin, segments=12)

    arm_l = body.attachNewNode("arm_l")
    arm_l.setPos(-0.175, 0, 0.69)
    arm_l.setR(-6)
    arm_r = body.attachNewNode("arm_r")
    arm_r.setPos(0.175, 0, 0.69)
    arm_r.setR(6)
    for arm in (arm_l, arm_r):
        meshkit.add_cylinder(arm, "arm", (0, 0, -0.25), 0.04, 0.045, 0.25, skin, segments=10)
        meshkit.add_sphere(arm, "hand", (0, 0.005, -0.26), 0.05, skin, rings=6, segments=10)

    head = body.attachNewNode("head")
    head.setPos(0, 0, 0.94)
    meshkit.add_sphere(head, "face", (0, 0.02, 0), 0.195, skin, rings=14, segments=20)
    meshkit.add_sphere(head, "hair", (0, -0.045, 0.02), 0.205, hair_color, rings=12, segments=18)
    if hairstyle == "bun":
        meshkit.add_sphere(head, "bun", (0, -0.16, 0.12), 0.12, hair_color, rings=8, segments=12)
    elif hairstyle == "pigtails":
        for x in (-0.21, 0.21):
            meshkit.add_sphere(
                head, "pigtail", (x, -0.02, 0.01), 0.11, hair_color, rings=8, segments=12, scale=(0.8, 0.8, 1.3)
            )
    elif hairstyle == "short":
        meshkit.add_sphere(
            head, "bangs", (0, 0.12, 0.10), 0.17, hair_color, rings=8, segments=14, scale=(1.0, 0.35, 0.45)
        )
    else:
        meshkit.add_sphere(
            head, "bangs", (0, 0.12, 0.11), 0.17, hair_color, rings=8, segments=14, scale=(1.0, 0.35, 0.42)
        )
        meshkit.add_sphere(
            head,
            "side_hair_l",
            (-0.17, 0.01, -0.02),
            0.145,
            hair_color,
            rings=8,
            segments=12,
            scale=(0.45, 0.75, 1.0),
        )
        meshkit.add_sphere(
            head,
            "side_hair_r",
            (0.17, 0.01, -0.02),
            0.145,
            hair_color,
            rings=8,
            segments=12,
            scale=(0.45, 0.75, 1.0),
        )

    for x in (-0.07, 0.07):
        meshkit.add_sphere(head, "eye", (x, 0.205, 0.035), 0.047, PALETTE["white"], rings=6, segments=10, scale=(1.0, 0.4, 1.0))
        meshkit.add_sphere(head, "iris", (x, 0.222, 0.035), 0.028, PALETTE["eye"], rings=6, segments=10, scale=(1.0, 0.3, 1.0))
        meshkit.add_sphere(head, "glint", (x + 0.008, 0.238, 0.045), 0.008, PALETTE["white"], rings=4, segments=6)
    meshkit.add_sphere(head, "nose", (0, 0.225, 0.0), 0.016, PALETTE["skin_shadow"], rings=5, segments=8)
    meshkit.add_box(head, "mouth", (0, 0.225, -0.065), (0.05, 0.012, 0.012), (0.62, 0.25, 0.22, 1.0))

    if accessory == "glasses":
        for x in (-0.07, 0.07):
            _ring_line(head, (x, 0.225, 0.035), 0.055, (0.15, 0.13, 0.12, 1.0), thickness=1.8)
    elif accessory == "apron":
        meshkit.add_box(body, "apron", (0, -0.19, 0.46), (0.34, 0.02, 0.36), (0.95, 0.90, 0.80, 1.0))
    elif accessory == "scarf":
        meshkit.add_cylinder(body, "scarf", (0, 0, 0.72), 0.16, 0.14, 0.05, PALETTE["honey"], segments=16)

    return VillagerRig(root=root, body=body, head=head, arm_l=arm_l, arm_r=arm_r, leg_l=leg_l, leg_r=leg_r)


def _ring_line(
    parent: NodePath,
    center: tuple[float, float, float],
    radius: float,
    color: tuple[float, float, float, float],
    *,
    thickness: float = 1.5,
) -> None:
    segs = LineSegs("ring")
    segs.setThickness(thickness)
    segs.setColor(*color)
    segments = 16
    for i in range(segments + 1):
        angle = 2 * math.pi * i / segments
        x = center[0] + math.cos(angle) * radius
        z = center[2] + math.sin(angle) * radius
        if i == 0:
            segs.moveTo(x, center[1], z)
        else:
            segs.drawTo(x, center[1], z)
    parent.attachNewNode(segs.create())
