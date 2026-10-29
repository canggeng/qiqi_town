"""主应用：3D 小镇、标题/暂停/存档/设置流程。"""

from __future__ import annotations

import math
import os
import sys
from argparse import Namespace
from pathlib import Path

from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from direct.task.Task import Task
from panda3d.core import (
    AmbientLight,
    AntialiasAttrib,
    DirectionalLight,
    Filename,
    MouseButton,
    Point2,
    Point3,
    Vec4,
    WindowProperties,
    loadPrcFileData,
)

from qiqi_town.config import (
    GAME_TITLE,
    LOCATION_LABELS,
    PALETTE,
    SYSTEM_CJK_FONT_CANDIDATES,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from qiqi_town.core.clock import GameClock
from qiqi_town.core.save_repository import SaveError, SaveRepository
from qiqi_town.core.settings import SettingsRepository
from qiqi_town.core.state import GameState, MinigameState, QuestState
from qiqi_town.entities.camera_rig import CameraRig
from qiqi_town.entities.player import PlayerController
from qiqi_town.paths import app_data_root, assets_dir, build_dir, saves_dir
from qiqi_town.systems.dialogue import DialogueRunner
from qiqi_town.systems.dialogue_data import load_dialogue_nodes
from qiqi_town.ui.dialogue import DialogueUi
from qiqi_town.ui.diary import DiaryUi
from qiqi_town.ui.ending import EndingUi
from qiqi_town.ui.minigame import MinigameUi
from qiqi_town.ui.screens import UiManager
from qiqi_town.world import meshkit
from qiqi_town.world.character_builder import build_qiqi, build_villager
from qiqi_town.world.interactables import Interactable
from qiqi_town.world.interiors import build_home, build_kindergarten, build_library
from qiqi_town.world.town import WORLD_HALF, build_town


class QiqiTownApp(ShowBase):
    def __init__(self, args: Namespace) -> None:
        super().__init__()
        self.args = args
        self.mode = "title"
        self.save_return_mode = "title"
        self.settings_return_mode = "title"

        self.disableMouse()
        self.camLens.setFov(48)
        self.camLens.setNearFar(0.1, 300)
        self.setBackgroundColor(*PALETTE["sky"])
        self.render.setAntialias(AntialiasAttrib.MMultisample)

        self.settings_repo = SettingsRepository()
        self.settings = self.settings_repo.load()
        self.save_repo = SaveRepository()
        self.font = self._load_font()
        self.state = GameState.new_game()
        self.clock = GameClock(day=1, minutes=8 * 60, paused=True)

        self.scene = build_town(self.render)
        self.town_scene = self.scene
        self.interiors = {
            "home": build_home(self.render),
            "kindergarten": build_kindergarten(self.render),
            "library": build_library(self.render),
        }
        self.current_scene_id = "town"
        self.scene_roots = {
            "town": self.town_scene.root,
            **{key: scene.root for key, scene in self.interiors.items()},
        }
        self.scene_navs = {
            "town": self.town_scene.nav,
            **{key: scene.nav for key, scene in self.interiors.items()},
        }
        self.player = PlayerController(self.render, build_qiqi(self.render), self.scene.nav)
        self.player.height_fn = self.town_scene.height_at
        self.player.set_position(*self.scene.player_start, facing=math.pi)
        self.camera_rig = CameraRig(
            self.cam, distance=7.2, pitch=0.48, sensitivity=self.settings.camera_sensitivity
        )
        self.camera_rig.update(0.016, self.player.position, self.player.z)

        self._setup_lighting()
        self._setup_marker()
        self._setup_hover()
        self._setup_npcs()
        self.dialogue_ui = DialogueUi(self)
        self.minigame_ui = MinigameUi(self)
        self.dialogue_nodes = load_dialogue_nodes()
        self._pending_interaction: Interactable | None = None
        self._hovered: Interactable | None = None
        self._setup_input()
        self._last_mouse: tuple[float, float] | None = None
        self._marker_time = 0.0
        self._hint_time = 0.0
        self.ui = UiManager(self)
        self.diary_ui = DiaryUi(self)
        self.ending_ui = EndingUi(self)
        self.ui.show_title()

        self.taskMgr.add(self._update, "qiqi_update")
        self.accept("escape", self._on_escape)

    # ---------------------------------------------------------------- setup
    def _load_font(self):
        bundled = assets_dir() / "fonts" / "NotoSansSC-Regular.otf"
        candidates = [str(bundled), *SYSTEM_CJK_FONT_CANDIDATES]
        for path in candidates:
            if not Path(path).exists():
                continue
            try:
                path_str = Filename.fromOsSpecific(path).getFullpath()
                font = self.loader.loadFont(path_str)
                if font is not None:
                    return font
            except Exception:  # noqa: BLE001, S112
                continue
        return None

    def _setup_lighting(self) -> None:
        ambient = AmbientLight("ambient")
        ambient.setColor(Vec4(0.46, 0.50, 0.54, 1.0))
        self.render.setLight(self.render.attachNewNode(ambient))

        sun = DirectionalLight("sun")
        sun.setColor(Vec4(0.62, 0.57, 0.47, 1.0))
        sun_np = self.render.attachNewNode(sun)
        sun_np.setHpr(-38, -48, 0)
        self.render.setLight(sun_np)

    def _setup_marker(self) -> None:
        self.marker = meshkit.add_disc(
            self.render,
            "click_marker",
            (0, 0, 0.04),
            0.26,
            (1.0, 0.78, 0.28, 0.85),
            segments=18,
            alpha=0.85,
        )
        self.marker.setDepthWrite(False)
        self.marker.setBin("transparent", 1)
        self.marker.hide()

    def _setup_hover(self) -> None:
        self.hover_ring = meshkit.add_disc(
            self.render,
            "hover_ring",
            (0, 0, 0.045),
            0.48,
            (1.0, 0.86, 0.45, 0.42),
            segments=24,
            alpha=0.42,
        )
        self.hover_ring.setDepthWrite(False)
        self.hover_ring.setBin("transparent", 0)
        self.hover_ring.hide()

    def _setup_npcs(self) -> None:
        self.npcs = {}
        lin = build_villager(
            self.interiors["kindergarten"].root,
            name="lin",
            dress_color=(0.36, 0.62, 0.58, 1.0),
            hair_color=(0.30, 0.20, 0.14, 1.0),
            height_scale=1.12,
            hairstyle="bun",
            accessory="glasses",
        )
        lin.root.setPos(1.6, 3.0, 0.0)
        lin.root.setH(180)
        self.npcs["lin"] = lin

        xiaoman = build_villager(
            self.scene.root,
            name="xiaoman",
            dress_color=(0.94, 0.52, 0.46, 1.0),
            hair_color=(0.13, 0.10, 0.09, 1.0),
            height_scale=0.92,
            hairstyle="pigtails",
        )
        xiaoman.root.setPos(3.4, -6.0, 0.0)
        xiaoman.root.setH(180)
        self.npcs["xiaoman"] = xiaoman

        gu = build_villager(
            self.interiors["library"].root,
            name="gu",
            dress_color=(0.46, 0.36, 0.27, 1.0),
            hair_color=(0.68, 0.66, 0.62, 1.0),
            height_scale=1.06,
            hairstyle="short",
            accessory="scarf",
        )
        gu.root.setPos(-2.0, 2.1, 0.0)
        gu.root.setH(180)
        self.npcs["gu"] = gu

        su = build_villager(
            self.scene.root,
            name="su",
            dress_color=(0.92, 0.78, 0.42, 1.0),
            hair_color=(0.28, 0.19, 0.14, 1.0),
            height_scale=1.05,
            hairstyle="bun",
            accessory="apron",
        )
        su.root.setPos(22.0, -10.0, 0.0)
        su.root.setH(180)
        self.npcs["su"] = su

        chen = build_villager(
            self.scene.root,
            name="chen",
            dress_color=(0.36, 0.62, 0.58, 1.0),
            hair_color=(0.18, 0.14, 0.12, 1.0),
            height_scale=1.0,
            hairstyle="pigtails",
            accessory="apron",
        )
        chen.root.setPos(-24.0, -10.0, 0.0)
        chen.root.setH(180)
        self.npcs["chen"] = chen

        self.town_interactables: list[Interactable] = [
            Interactable(
                "xiaoman",
                "和小满说话",
                (3.4, -6.0, 0.55),
                (3.4, -7.4),
                self.talk_xiaoman,
                radius=2.3,
                kind="npc",
            ),
            Interactable(
                "home_door",
                "进入家",
                (-10.0, -15.6, 0.9),
                (-10.0, -17.0),
                lambda: self.enter_interior("home"),
                radius=2.5,
                kind="door",
            ),
            Interactable(
                "kindergarten_door",
                "进入幼儿园",
                (12.0, 2.6, 0.9),
                (12.0, 0.8),
                lambda: self.enter_interior("kindergarten"),
                radius=2.6,
                kind="door",
            ),
            Interactable(
                "library_door",
                "进入图书馆",
                (-14.0, 1.6, 0.9),
                (-14.0, -0.3),
                lambda: self.enter_interior("library"),
                radius=2.6,
                kind="door",
            ),
            Interactable(
                "su",
                "和苏阿姨说话",
                (22.0, -10.0, 0.7),
                (22.0, -11.6),
                self.talk_su,
                radius=2.4,
                kind="npc",
            ),
            Interactable(
                "chen",
                "和陈阿姨说话",
                (-24.0, -10.0, 0.7),
                (-24.0, -11.6),
                self.talk_chen,
                radius=2.4,
                kind="npc",
            ),
            Interactable(
                "summit_view",
                "在山顶看风景",
                (0.0, 33.6, 6.9),
                (0.0, 32.2),
                self.summit_view,
                radius=2.6,
                kind="view",
            ),
        ]
        home_interactables: list[Interactable] = [
            Interactable(
                "bed",
                "睡觉",
                (-3.1, 1.9, 0.7),
                (-3.1, 0.0),
                self.sleep_to_next_day,
                radius=2.6,
                kind="prop",
            ),
            Interactable(
                "home_exit",
                "出门",
                (0.0, -3.7, 0.9),
                (0.0, -2.6),
                self.exit_to_town,
                radius=2.2,
                kind="door",
            ),
        ]
        kg_interactables: list[Interactable] = [
            Interactable(
                "lin",
                "和林老师说话",
                (1.6, 3.0, 0.8),
                (1.6, 1.9),
                self.talk_lin,
                radius=2.4,
                kind="npc",
            ),
            Interactable(
                "shape_game",
                "玩形状配对",
                (3.2, 1.4, 0.8),
                (3.2, 0.2),
                self.start_shape_game,
                radius=2.4,
                kind="game",
            ),
            Interactable(
                "kg_exit",
                "出门",
                (0.0, -4.2, 0.9),
                (0.0, -3.1),
                self.exit_to_town,
                radius=2.2,
                kind="door",
            ),
        ]
        library_interactables: list[Interactable] = [
            Interactable(
                "gu",
                "和顾爷爷说话",
                (-2.0, 2.1, 0.8),
                (-2.0, 0.8),
                self.talk_gu,
                radius=2.4,
                kind="npc",
            ),
            Interactable(
                "library_exit",
                "出门",
                (0.0, -3.7, 0.9),
                (0.0, -2.6),
                self.exit_to_town,
                radius=2.2,
                kind="door",
            ),
        ]
        self.scene_interactables = {
            "town": self.town_interactables,
            "home": home_interactables,
            "kindergarten": kg_interactables,
            "library": library_interactables,
        }
        self.scene_active_npcs = {
            "town": [self.npcs["xiaoman"], self.npcs["su"], self.npcs["chen"]],
            "home": [],
            "kindergarten": [self.npcs["lin"]],
            "library": [self.npcs["gu"]],
        }
        self.interactables = self.scene_interactables["town"]
        self.active_npcs = self.scene_active_npcs["town"]

    def _setup_input(self) -> None:
        self.accept("mouse1", self._on_left_click)
        self.accept("wheel_up", self._on_wheel_up)
        self.accept("wheel_down", self._on_wheel_down)

    # ---------------------------------------------------------------- input
    def _on_escape(self) -> None:
        if self.mode == "playing":
            self.pause_game()
        elif self.mode == "paused":
            self.resume_game()
        elif self.mode == "diary":
            self.close_diary()
        elif self.mode == "ending":
            self.finish_ending()

    def _on_left_click(self) -> None:
        if self.mode == "dialogue":
            self.dialogue_ui.handle_click()
            return
        if self.mode != "playing":
            return
        if self.mouseWatcherNode is None or not self.mouseWatcherNode.hasMouse():
            return
        if self.mouseWatcherNode.isButtonDown(MouseButton.three()):
            return
        # 菜单按钮所在区域交给 DirectButton，不触发地面移动。
        if self.mouseWatcherNode.getMouseX() > 0.75 and self.mouseWatcherNode.getMouseY() > 0.8:
            return

        hovered = self._find_hovered()
        if hovered is not None:
            self._request_interaction(hovered)
            return

        point = self._mouse_to_ground()
        if point is None:
            return
        target = self.scene.nav.nearest_walkable((point.x, point.y))
        if target is None:
            self._show_hint("那边过不去，换条路试试。")
            return
        self._pending_interaction = None
        if self.player.move_to(target):
            self.marker.setPos(target[0], target[1], 0.04)
            self.marker.show()
            self.marker.setScale(1.0)
            self._marker_time = 0.75
        else:
            self._show_hint("那边过不去，换条路试试。")

    def _mouse_to_ground(self) -> Point3 | None:
        if self.mouseWatcherNode is None or not self.mouseWatcherNode.hasMouse():
            return None
        near = Point3()
        far = Point3()
        self.camLens.extrude(self.mouseWatcherNode.getMouse(), near, far)
        near_world = self.cam.getRelativePoint(self.render, near)
        far_world = self.cam.getRelativePoint(self.render, far)
        direction = far_world - near_world
        if abs(direction.z) < 1e-6:
            return None
        # 先快速求平面交点，再沿线段采样地形高度；兼容山道斜坡。
        t_plane = (0.03 - near_world.z) / direction.z
        if t_plane <= 0:
            return None
        steps = 120
        for i in range(1, steps + 1):
            t = i / steps
            point = near_world + direction * t
            if abs(point.x) > WORLD_HALF - 1 or abs(point.y) > WORLD_HALF - 1:
                continue
            height = self._ground_height(point.x, point.y)
            if point.z <= height + 0.05:
                return Point3(point.x, point.y, height)
        return None

    def _ground_height(self, x: float, y: float) -> float:
        if self.current_scene_id == "town":
            return self.town_scene.height_at(x, y)
        return 0.0

    def _on_wheel_up(self) -> None:
        if self.mode == "playing":
            self.camera_rig.zoom(-1.0)

    def _on_wheel_down(self) -> None:
        if self.mode == "playing":
            self.camera_rig.zoom(1.0)

    # ---------------------------------------------------------------- update
    def _update(self, task):
        dt = min(0.05, globalClock.getDt())

        if self.mode == "playing":
            self.player.update(dt)
            self.clock.tick(dt)
            self.state.playtime_seconds += dt
            self._update_orbit(dt)
            self._update_marker(dt)
            self._update_hint(dt)
            self._update_hover()
            self._update_pending_interaction()
            self._update_hud()
        elif self.mode == "dialogue":
            self.player.rig.update(dt, False)
            self.dialogue_ui.update(dt)
            self.hover_ring.hide()
        elif self.mode in {"minigame", "diary", "ending"}:
            self.player.rig.update(dt, False)
            self.hover_ring.hide()
        else:
            self.player.rig.update(dt, False)
            self.hover_ring.hide()

        self.camera_rig.update(dt, self.player.position, self.player.z)
        for npc in self.active_npcs:
            npc.update(dt, talking=self.mode == "dialogue")
        return Task.cont

    def _update_orbit(self, dt: float) -> None:
        if self.mouseWatcherNode is None or not self.mouseWatcherNode.hasMouse():
            self._last_mouse = None
            return
        mouse = self.mouseWatcherNode.getMouse()
        right_down = self.mouseWatcherNode.isButtonDown(MouseButton.three())
        if right_down:
            if self._last_mouse is not None:
                dx = mouse.x - self._last_mouse[0]
                dy = mouse.y - self._last_mouse[1]
                self.camera_rig.orbit(dx, dy)
            self._last_mouse = (mouse.x, mouse.y)
        else:
            self._last_mouse = None

    def _update_marker(self, dt: float) -> None:
        if self._marker_time <= 0:
            return
        self._marker_time -= dt
        if self._marker_time <= 0:
            self.marker.hide()
            return
        pulse = 1.0 + math.sin(self._marker_time * 18.0) * 0.12
        self.marker.setScale(pulse)

    def _update_hint(self, dt: float) -> None:
        if self._hint_time <= 0:
            return
        self._hint_time -= dt
        if self._hint_time <= 0:
            self.ui.hud_hint["text"] = "左键点击地面移动 · 右键拖动转镜头 · 滚轮缩放"

    def _show_hint(self, text: str) -> None:
        self.ui.hud_hint["text"] = text
        self._hint_time = 2.2

    # ---------------------------------------------------------------- hover/interact
    def _find_hovered(self) -> Interactable | None:
        if self.mouseWatcherNode is None or not self.mouseWatcherNode.hasMouse():
            return None
        mouse = self.mouseWatcherNode.getMouse()
        best: Interactable | None = None
        best_distance = 0.13
        for interactable in self.interactables:
            point = Point3(*interactable.world_pos)
            cam_point = self.cam.getRelativePoint(self.render, point)
            screen = Point2()
            if not self.camLens.project(cam_point, screen):
                continue
            distance = math.hypot(screen.x - mouse.x, screen.y - mouse.y)
            if distance < best_distance:
                best_distance = distance
                best = interactable
        return best

    def _update_hover(self) -> None:
        if self.mode != "playing":
            self.hover_ring.hide()
            self._hovered = None
            return
        hovered = self._find_hovered()
        if hovered is not None:
            self._hovered = hovered
            self.hover_ring.setPos(hovered.ground_pos[0], hovered.ground_pos[1], 0.045)
            self.hover_ring.show()
            label = hovered.label
            if hovered.id == "home_door" and self._daily_complete(self.clock.day):
                label = "回家睡觉"
            self.ui.hud_hint["text"] = label
        else:
            self._hovered = None
            self.hover_ring.hide()
            if self._hint_time <= 0:
                self.ui.hud_hint["text"] = "左键点击地面移动 · 右键拖动转镜头 · 滚轮缩放"

    def _request_interaction(self, interactable: Interactable) -> None:
        px, py = self.player.position
        ax, ay = interactable.approach_pos
        if math.hypot(px - ax, py - ay) <= 0.9:
            self._pending_interaction = None
            interactable.on_interact()
            return
        if self.player.move_to(interactable.approach_pos):
            self._pending_interaction = interactable
            self.marker.setPos(ax, ay, 0.04)
            self.marker.show()
            self.marker.setScale(0.8)
            self._marker_time = 0.75
        else:
            self._show_hint("那边过不去，换条路试试。")

    def _update_pending_interaction(self) -> None:
        pending = self._pending_interaction
        if pending is None or self.player.moving:
            return
        px, py = self.player.position
        ax, ay = pending.approach_pos
        if math.hypot(px - ax, py - ay) <= 1.0:
            self._pending_interaction = None
            pending.on_interact()
        else:
            self._pending_interaction = None
            self._show_hint("没能走到那里。")

    # ---------------------------------------------------------------- dialogue
    def talk_lin(self) -> None:
        if self.clock.day == 1 and not self._day1_complete():
            self.start_dialogue("lin_intro_1")
        else:
            self.start_dialogue("lin_after_1")

    def talk_xiaoman(self) -> None:
        self.start_dialogue("xiaoman_intro_1")

    def talk_gu(self) -> None:
        if self.clock.day == 2 and not self._daily_complete(2):
            self.start_dialogue("gu_day2_1")
        else:
            self.start_dialogue("gu_intro_1")

    def talk_su(self) -> None:
        if self.clock.day == 3 and not self._daily_complete(3):
            self.start_dialogue("su_day3_1")
        else:
            self.start_dialogue("su_intro_1")

    def talk_chen(self) -> None:
        if self.clock.day == 4 and not self._daily_complete(4):
            self.start_dialogue("chen_day4_1")
        else:
            self.start_dialogue("chen_intro_1")

    def summit_view(self) -> None:
        if self.clock.day == 5 and not self.state.story_complete:
            self.start_dialogue("summit_day5_1")
        else:
            self.start_dialogue("summit_view_1")

    def start_dialogue(self, node_id: str) -> None:
        if not self.dialogue_nodes:
            self.ui.toast("对话数据没有加载成功。")
            return
        runner = DialogueRunner.from_data(self.dialogue_nodes, self.state)
        if not runner.start(node_id):
            self.ui.toast("现在没有可说的话。")
            return
        self.mode = "dialogue"
        self.clock.paused = True
        self.player.stop()
        self._pending_interaction = None
        self.hover_ring.hide()
        self.ui.hide_all()
        self.dialogue_ui.show(runner)

    def end_dialogue(self) -> None:
        self.dialogue_ui.hide()
        self.mode = "playing"
        self.clock.paused = False
        self.ui.show_hud()
        self._update_hud()
        day = self.clock.day
        if self._daily_complete(day) and not self.state.flags.get(f"day{day}_reported"):
            self.state.flags[f"day{day}_reported"] = True
            if day == 5 and self.state.story_complete:
                self.show_ending()
                return
            self.ui.toast("今天的主线完成啦！回家找妈妈睡觉吧。", 3.0)
            self._auto_save()

    # ---------------------------------------------------------------- minigames
    def start_shape_game(self) -> None:
        self.start_minigame("day1_shapes")

    def start_minigame(self, game_id: str) -> None:
        if self.mode != "playing":
            return
        self.mode = "minigame"
        self.clock.paused = True
        self.player.stop()
        self._pending_interaction = None
        self.hover_ring.hide()
        self.ui.hide_all()
        self.minigame_ui.start(game_id)

    def end_minigame(self, *, success: bool, game_id: str) -> None:
        self.minigame_ui.hide()
        self.mode = "playing"
        self.clock.paused = False
        self.ui.show_hud()
        self._update_hud()
        if not success:
            self.ui.toast("下次再玩吧。", 1.8)
            return

        previous = self.state.minigames.get(game_id)
        plays = (previous.plays if previous else 0) + 1
        best = max(previous.best if previous else 0, 3)
        self.state.minigames[game_id] = MinigameState(completed=True, best=best, plays=plays)
        rewards = {
            "day1_shapes": ("sticker_shapes", "journal_shapes"),
        }
        sticker_id, journal_id = rewards.get(game_id, ("", ""))
        new_sticker = bool(sticker_id) and self.state.add_sticker(sticker_id)
        if journal_id:
            self.state.add_journal(journal_id)
        self.state.add_friendship("lin", 1)
        if new_sticker:
            self.ui.toast("获得回忆贴纸：形状小管家！", 2.6)
        else:
            self.ui.toast("又完成了一次形状配对。", 2.0)
        self._sync_state_from_world()
        self._auto_save()

    # ---------------------------------------------------------------- quests/day
    def _daily_complete(self, day: int) -> bool:
        quest = self.state.quests.get(f"day{day}_main")
        return quest is not None and quest.status == "complete"

    def _day1_complete(self) -> bool:
        return self._daily_complete(1)

    def _current_objective(self) -> str:
        if self.state.story_complete:
            return "目标：在小镇里自由生活"
        day = self.clock.day
        targets = {
            1: "目标：去幼儿园找林老师",
            2: "目标：去图书馆找顾爷爷",
            3: "目标：去公园找苏阿姨",
            4: "目标：去游乐场找陈阿姨",
            5: "目标：爬上青禾山，到山顶看灯",
        }
        if self._daily_complete(day):
            return "目标：回家睡觉" if day < 5 else "目标：在山顶看灯会"
        return targets.get(day, "目标：在小镇里逛逛")

    def interact_home(self) -> None:
        if not self._daily_complete(self.clock.day):
            self.ui.toast("妈妈：今天还有一件事没做完呢，先在镇上逛逛吧。", 3.0)
            return
        self.sleep_to_next_day()

    def sleep_to_next_day(self) -> None:
        if self.clock.day >= 5:
            if self.state.story_complete:
                self.ui.toast("灯会已经结束啦。可以继续在小镇里逛逛。", 2.6)
            else:
                self.ui.toast("今天是灯会，去山顶看灯吧。", 2.6)
            return
        if not self._daily_complete(self.clock.day):
            self.ui.toast("今天还有一件事没做完呢。先在镇上逛逛，或者再去和小镇居民说说话。", 3.2)
            return
        self.clock.advance_day()
        self.state.day = self.clock.day
        self.state.time_minutes = self.clock.minute_int
        quest_id = f"day{self.state.day}_main"
        if quest_id not in self.state.quests:
            from qiqi_town.core.state import QuestState

            self.state.quests[quest_id] = QuestState(step=0, status="active")
        self._activate_scene("home", self.interiors["home"].spawn, 0.0)
        self.state.location = "home"
        self.mode = "playing"
        self.clock.paused = False
        self.ui.show_hud()
        self._update_hud()
        self._sync_state_from_world()
        self._auto_save()
        self.ui.toast(f"第 {self.clock.day} 天开始了。", 2.0)

    def show_ending(self) -> None:
        self.mode = "ending"
        self.clock.paused = True
        self.player.stop()
        self._pending_interaction = None
        self.hover_ring.hide()
        self.ui.hide_all()
        self.ending_ui.show()
        self._sync_state_from_world()
        self._auto_save()

    def finish_ending(self) -> None:
        self.ending_ui.hide()
        self.mode = "playing"
        self.clock.paused = False
        self.ui.show_hud()
        self._update_hud()
        self._auto_save()

    # ---------------------------------------------------------------- hud
    def _update_hud(self) -> None:
        self.ui.update_hud(
            self.clock.day,
            self.clock.display_time,
            self.clock.phase_label,
            self._current_objective(),
            LOCATION_LABELS.get(self.current_scene_id, "青禾镇"),
        )

    # ---------------------------------------------------------------- scenes
    def _activate_scene(
        self,
        scene_id: str,
        position: tuple[float, float] | None = None,
        facing: float = 0.0,
    ) -> None:
        if scene_id not in self.scene_roots:
            scene_id = "town"
        for sid, root in self.scene_roots.items():
            if sid == scene_id:
                root.show()
            else:
                root.hide()
        self.current_scene_id = scene_id
        self.scene = self.town_scene if scene_id == "town" else self.interiors[scene_id]
        self.player.nav = self.scene_navs[scene_id]
        self.player.height_fn = (
            self.town_scene.height_at if scene_id == "town" else (lambda x, y: 0.0)
        )
        if position is None:
            if scene_id == "town":
                position = self.town_scene.player_start
            else:
                position = self.interiors[scene_id].spawn
        x, y = position
        if not self.scene_navs[scene_id].is_walkable((x, y)):
            if scene_id == "town":
                x, y = self.town_scene.player_start
            else:
                x, y = self.interiors[scene_id].spawn
        self.player.set_position(x, y, facing)
        self.interactables = self.scene_interactables[scene_id]
        self.active_npcs = self.scene_active_npcs[scene_id]
        self._pending_interaction = None
        self._hovered = None
        if hasattr(self, "hover_ring"):
            self.hover_ring.hide()
        self.camera_rig.snap_to(self.player.position, self.player.z)
        self._update_hud()

    def enter_interior(self, scene_id: str) -> None:
        if scene_id not in self.interiors:
            return
        self._activate_scene(scene_id, self.interiors[scene_id].spawn, 0.0)
        names = {"home": "家", "kindergarten": "幼儿园", "library": "图书馆"}
        self.ui.toast(f"进入{names.get(scene_id, '房间')}。", 1.5)

    def exit_to_town(self) -> None:
        spawns = {
            "home": (-10.0, -17.0),
            "kindergarten": (12.0, 0.8),
            "library": (-14.0, -0.3),
        }
        position = spawns.get(self.current_scene_id, self.town_scene.player_start)
        self._activate_scene("town", position, 0.0)

    # ---------------------------------------------------------------- modes
    def pause_game(self) -> None:
        if self.mode != "playing":
            return
        self.player.stop()
        self._pending_interaction = None
        self.hover_ring.hide()
        self.mode = "paused"
        self.clock.paused = True
        self.ui.show_pause()

    def resume_game(self) -> None:
        if self.mode not in {"paused", "save", "settings"}:
            return
        self.mode = "playing"
        self.clock.paused = False
        self.ui.show_hud()
        self.ui.hide_confirm()
        self._update_hud()

    def open_save(self, save_mode: str) -> None:
        if self.mode not in {"title", "paused", "save"}:
            return
        if self.mode != "save":
            self.save_return_mode = self.mode
        self.mode = "save"
        self.clock.paused = True
        self.player.stop()
        self.ui.show_save(save_mode)

    def close_save(self) -> None:
        if self.save_return_mode == "title":
            self._do_return_to_title()
        else:
            self.mode = "paused"
            self.ui.show_pause()

    def open_settings(self) -> None:
        if self.mode not in {"title", "paused", "settings"}:
            return
        if self.mode != "settings":
            self.settings_return_mode = self.mode
        self.mode = "settings"
        self.clock.paused = True
        self.player.stop()
        self.ui.show_settings(self.settings_return_mode)

    def close_settings(self) -> None:
        if self.settings_return_mode == "title":
            self._do_return_to_title()
        else:
            self.mode = "paused"
            self.ui.show_pause()

    def open_diary(self) -> None:
        if self.mode not in {"playing", "paused", "diary"}:
            return
        self.mode = "diary"
        self.clock.paused = True
        self.player.stop()
        self._pending_interaction = None
        self.hover_ring.hide()
        self.ui.hide_all()
        self.diary_ui.show()

    def close_diary(self) -> None:
        self.diary_ui.hide()
        self.mode = "paused"
        self.ui.show_pause()

    def return_to_title(self) -> None:
        self.ui.show_confirm("返回标题？当前未保存的进度会丢失。", self._do_return_to_title)

    def _do_return_to_title(self) -> None:
        self.mode = "title"
        self.clock.paused = True
        self.player.stop()
        self.ui.show_title()

    def quit_game(self) -> None:
        self.userExit()

    def has_saves(self) -> bool:
        return self.save_repo.has_any()

    # ---------------------------------------------------------------- new/load
    def new_game(self) -> None:
        if self.has_saves():
            self.ui.show_confirm(
                "开始新的故事？已有存档不会被删除，自动档会在新进度中更新。",
                self._begin_new_game,
            )
        else:
            self._begin_new_game()

    def _begin_new_game(self, *, auto_save: bool = True) -> None:
        self.state = GameState.new_game()
        self.state.location = "town"
        self.state.player.x, self.state.player.y = self.town_scene.player_start
        self.state.player.facing = math.pi
        self.clock = GameClock(day=self.state.day, minutes=self.state.time_minutes)
        self.clock.paused = False
        self._activate_scene("town", self.town_scene.player_start, math.pi)
        self.mode = "playing"
        self.ui.hide_confirm()
        self.ui.show_hud()
        self._update_hud()
        self.ui.toast("新的一天开始了。")
        self._sync_state_from_world()
        if auto_save:
            self._auto_save()

    def continue_game(self) -> None:
        latest = self.save_repo.latest()
        if latest is None:
            self.ui.toast("还没有可继续的存档。")
            return
        try:
            state = self.save_repo.load("auto" if latest.is_auto else latest.slot)
        except SaveError as exc:
            self.ui.toast(f"读取失败：{exc.message}")
            return
        self.apply_state(state, notify=True)

    def on_slot_clicked(self, slot: int, is_auto: bool) -> None:
        if self.ui.delete_mode:
            if is_auto or slot == 0:
                return
            self.ui.show_confirm(f"删除槽位 {slot:02d} 的存档？", lambda: self._delete_slot(slot))
            return

        if self.ui.save_mode == "save":
            if is_auto or slot == 0:
                return
            info = self.save_repo.list_slots()[slot - 1]
            if info.exists:
                self.ui.show_confirm(
                    f"覆盖槽位 {slot:02d} 的存档？",
                    lambda: self._do_save_slot(slot),
                )
            else:
                self._do_save_slot(slot)
            return

        self._do_load_slot(slot, is_auto)

    def _do_save_slot(self, slot: int) -> None:
        self._sync_state_from_world()
        try:
            self.save_repo.save_manual(slot, self.state)
        except SaveError as exc:
            self.ui.toast(f"保存失败：{exc.message}")
            return
        self.ui.refresh_save()
        self.ui.toast(f"已保存到槽位 {slot:02d}。")

    def _do_load_slot(self, slot: int, is_auto: bool) -> None:
        try:
            state = self.save_repo.load("auto" if is_auto else slot)
        except SaveError as exc:
            self.ui.toast(f"读取失败：{exc.message}")
            return
        self.apply_state(state)

    def _delete_slot(self, slot: int) -> None:
        try:
            self.save_repo.delete_manual(slot)
        except SaveError as exc:
            self.ui.toast(f"删除失败：{exc.message}")
            return
        self.ui.refresh_save()
        self.ui.toast(f"槽位 {slot:02d} 已删除。")

    def apply_state(self, state: GameState, *, notify: bool = False) -> None:
        self.state = state
        self.clock = GameClock(day=state.day, minutes=state.time_minutes)
        self.clock.paused = False
        scene_id = state.location if state.location in self.scene_roots else "town"
        self.state.location = scene_id
        self._activate_scene(scene_id, (state.player.x, state.player.y), state.player.facing)
        self.mode = "playing"
        self.ui.hide_confirm()
        self.ui.show_hud()
        self._update_hud()
        if notify:
            self.ui.toast("已读取存档。")

    def _sync_state_from_world(self) -> None:
        self.state.day = self.clock.day
        self.state.time_minutes = self.clock.minute_int
        self.state.location = self.current_scene_id
        self.state.player.x = self.player.position[0]
        self.state.player.y = self.player.position[1]
        self.state.player.facing = self.player.facing

    def _auto_save(self) -> None:
        self._sync_state_from_world()
        try:
            self.save_repo.save_auto(self.state)
        except SaveError:
            pass

    # ---------------------------------------------------------------- settings
    def save_settings(self) -> None:
        self.settings_repo.save(self.settings)
        self.camera_rig.set_sensitivity(self.settings.camera_sensitivity)

    def toggle_fullscreen(self) -> None:
        self.settings.fullscreen = not self.settings.fullscreen
        props = WindowProperties()
        props.setFullscreen(self.settings.fullscreen)
        self.win.requestProperties(props)
        self.save_settings()
        self.ui.toast("显示模式已切换。" if self.settings.fullscreen else "已切换到窗口模式。")

    def open_save_folder(self) -> None:
        try:
            os.startfile(str(saves_dir()))  # type: ignore[attr-defined]
        except OSError:
            self.ui.toast(f"无法打开文件夹：{saves_dir()}")

    # ---------------------------------------------------------------- smoke
    def run_smoke_test(self) -> int:
        self.clock.paused = True
        try:
            for _ in range(4):
                self.taskMgr.step()
            self.graphicsEngine.renderFrame()
            self.win.getScreenshot().write(
                Filename.fromOsSpecific(str(build_dir() / "title.png"))
            )
            self._begin_new_game(auto_save=False)
            for _ in range(6):
                self.taskMgr.step()
            self.graphicsEngine.renderFrame()
            self.win.getScreenshot().write(
                Filename.fromOsSpecific(str(build_dir() / "smoke.png"))
            )
            self._activate_scene("town", (18.0, -22.0), 0.0)
            for _ in range(2):
                self.taskMgr.step()
            self.graphicsEngine.renderFrame()
            self.win.getScreenshot().write(
                Filename.fromOsSpecific(str(build_dir() / "park.png"))
            )
            self._activate_scene("town", (-20.0, -22.0), 0.0)
            for _ in range(2):
                self.taskMgr.step()
            self.graphicsEngine.renderFrame()
            self.win.getScreenshot().write(
                Filename.fromOsSpecific(str(build_dir() / "playground.png"))
            )
            self._activate_scene("town", (0.0, 30.5), 0.0)
            self.camera_rig.yaw = math.pi
            self.camera_rig.update(0.016, self.player.position, self.player.z)
            for _ in range(2):
                self.taskMgr.step()
            self.graphicsEngine.renderFrame()
            self.win.getScreenshot().write(
                Filename.fromOsSpecific(str(build_dir() / "summit.png"))
            )
            self.camera_rig.yaw = 0.0
            self._activate_scene("town", self.town_scene.player_start, math.pi)
            self.enter_interior("kindergarten")
            for _ in range(3):
                self.taskMgr.step()
            self.graphicsEngine.renderFrame()
            self.win.getScreenshot().write(
                Filename.fromOsSpecific(str(build_dir() / "kindergarten.png"))
            )
            self.start_shape_game()
            for _ in range(2):
                self.taskMgr.step()
            self.graphicsEngine.renderFrame()
            self.win.getScreenshot().write(
                Filename.fromOsSpecific(str(build_dir() / "minigame.png"))
            )
            self.minigame_ui._select_item("red_circle")
            self.minigame_ui._choose_slot("circle")
            self.minigame_ui._select_item("blue_square")
            self.minigame_ui._choose_slot("square")
            self.minigame_ui._select_item("yellow_triangle")
            self.minigame_ui._choose_slot("triangle")
            for _ in range(2):
                self.taskMgr.step()
            self.graphicsEngine.renderFrame()
            self.win.getScreenshot().write(
                Filename.fromOsSpecific(str(build_dir() / "minigame_done.png"))
            )
            self.end_minigame(success=True, game_id="day1_shapes")
            self.enter_interior("home")
            for _ in range(3):
                self.taskMgr.step()
            self.graphicsEngine.renderFrame()
            self.win.getScreenshot().write(
                Filename.fromOsSpecific(str(build_dir() / "home.png"))
            )
            self._activate_scene("town", self.town_scene.player_start, math.pi)
            self.ui.show_hud()
            old_speed = self.settings.text_speed
            self.settings.text_speed = 999.0
            self.start_dialogue("lin_intro_1")
            for _ in range(4):
                self.taskMgr.step()
            self.dialogue_ui.update(2.0)
            self.dialogue_ui.handle_click()
            self.dialogue_ui.update(2.0)
            for _ in range(2):
                self.taskMgr.step()
            self.graphicsEngine.renderFrame()
            self.win.getScreenshot().write(
                Filename.fromOsSpecific(str(build_dir() / "dialogue.png"))
            )
            # 走完林老师的示例对话，验证选项效果与主线完成。
            self.dialogue_ui._choose(0)
            self.dialogue_ui.update(2.0)
            self.dialogue_ui.handle_click()
            self.dialogue_ui.update(2.0)
            self.dialogue_ui._choose(0)
            self.dialogue_ui.update(2.0)
            self.dialogue_ui.handle_click()
            self.dialogue_ui.update(2.0)
            self.dialogue_ui.handle_click()
            for _ in range(2):
                self.taskMgr.step()
            self.graphicsEngine.renderFrame()
            self.win.getScreenshot().write(
                Filename.fromOsSpecific(str(build_dir() / "after_dialogue.png"))
            )
            self.settings.text_speed = old_speed
            if self.mode == "dialogue":
                self.end_dialogue()
            self._do_save_slot(1)
            self.pause_game()
            self.open_save("save")
            for _ in range(2):
                self.taskMgr.step()
            self.graphicsEngine.renderFrame()
            self.win.getScreenshot().write(
                Filename.fromOsSpecific(str(build_dir() / "save.png"))
            )
            self._do_load_slot(1, False)
            for _ in range(2):
                self.taskMgr.step()
            self.graphicsEngine.renderFrame()
            self.win.getScreenshot().write(
                Filename.fromOsSpecific(str(build_dir() / "load.png"))
            )
            self.pause_game()
            self.open_diary()
            for _ in range(2):
                self.taskMgr.step()
            self.graphicsEngine.renderFrame()
            self.win.getScreenshot().write(
                Filename.fromOsSpecific(str(build_dir() / "diary.png"))
            )
            self.close_diary()
            self.open_settings()
            for _ in range(2):
                self.taskMgr.step()
            self.graphicsEngine.renderFrame()
            self.win.getScreenshot().write(
                Filename.fromOsSpecific(str(build_dir() / "settings.png"))
            )
            # 第五天结局界面。
            self.clock.day = 5
            self.clock.minutes = 18 * 60
            self.state.day = 5
            self.state.story_complete = False
            self.state.quests["day5_main"] = QuestState(step=0, status="active")
            self._activate_scene("town", (0.0, 30.5), 0.0)
            self.mode = "playing"
            self.ui.show_hud()
            self.settings.text_speed = 999.0
            self.start_dialogue("summit_day5_1")
            self.dialogue_ui.update(2.0)
            self.dialogue_ui._choose(0)
            self.dialogue_ui.update(2.0)
            self.dialogue_ui.handle_click()
            self.dialogue_ui.update(2.0)
            self.dialogue_ui.handle_click()
            for _ in range(2):
                self.taskMgr.step()
            self.graphicsEngine.renderFrame()
            self.win.getScreenshot().write(
                Filename.fromOsSpecific(str(build_dir() / "ending.png"))
            )
        except Exception as exc:  # noqa: BLE001
            print(f"SMOKE FAILED: {exc}", file=sys.stderr)
            self.destroy()
            return 2
        print(f"SMOKE OK: {build_dir() / 'smoke.png'}")
        try:
            (app_data_root() / "smoke.ok").write_text("ok\n", encoding="utf-8")
        except OSError:
            pass
        self.destroy()
        return 0


def configure_prc(args: Namespace) -> None:
    loadPrcFileData("", f"window-title {GAME_TITLE}")
    loadPrcFileData("", f"win-size {WINDOW_WIDTH} {WINDOW_HEIGHT}")
    loadPrcFileData("", "framebuffer-multisample 1")
    loadPrcFileData("", "multisamples 4")
    loadPrcFileData("", "vsync 1")
    loadPrcFileData("", "audio-library-name null")
    loadPrcFileData("", "notify-level warning")
    loadPrcFileData("", "default-directnotify-level warning")
    if args.smoke_test:
        loadPrcFileData("", "window-type offscreen")
        loadPrcFileData("", "win-size 1280 720")
