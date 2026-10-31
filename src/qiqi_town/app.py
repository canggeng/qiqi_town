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
    TextNode,
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
from qiqi_town.systems.audio import AudioSystem
from qiqi_town.systems.daily_content import GameSlot, slot_by_id, slot_for
from qiqi_town.systems.dialogue import DialogueRunner
from qiqi_town.systems.dialogue_data import load_dialogue_nodes
from qiqi_town.systems.minigames.find_game import default_find_game
from qiqi_town.systems.tutorial import Tutorial
from qiqi_town.ui.catch_game import CatchUi
from qiqi_town.ui.dialogue import DialogueUi
from qiqi_town.ui.diary import DiaryUi
from qiqi_town.ui.ending import EndingUi
from qiqi_town.ui.memory import MemoryUi
from qiqi_town.ui.minigame import MinigameUi
from qiqi_town.ui.night import NightTransitionUi
from qiqi_town.ui.rhythm import RhythmUi
from qiqi_town.ui.screens import UiManager
from qiqi_town.ui.story_order import StoryOrderUi
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
        if args.windowed:
            self.settings.fullscreen = False
        self.save_repo = SaveRepository()
        self.font = self._load_font()
        self.audio = AudioSystem(self, self.settings)
        if not args.smoke_test and self.settings.fullscreen:
            self._apply_fullscreen(True)
        self._step_timer = 0.0
        self._last_audio_key: tuple[str, int, str] | None = None
        self.state = GameState.new_game()
        self._in_game = False
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
        self._setup_find_game()
        self._setup_events()
        self._setup_game_markers()
        self.dialogue_ui = DialogueUi(self)
        self.minigame_ui = MinigameUi(self)
        self.story_order_ui = StoryOrderUi(self)
        self.rhythm_ui = RhythmUi(self)
        self.catch_ui = CatchUi(self)
        self.memory_ui = MemoryUi(self)
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
        self.night_ui = NightTransitionUi(self)
        self.tutorial = Tutorial(self)
        self.ui.show_title()
        self._update_music_for_state()

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
        lin.root.setPos(1.5, -1.2, 0.0)
        lin.root.setH(180)
        self.npcs["lin"] = lin

        an = build_villager(
            self.interiors["kindergarten"].root,
            name="an",
            dress_color=(0.94, 0.62, 0.72, 1.0),
            hair_color=(0.20, 0.14, 0.11, 1.0),
            height_scale=0.84,
            hairstyle="pigtails",
        )
        an.root.setPos(2.8, -0.2, 0.0)
        an.root.setH(180)
        self.npcs["an"] = an

        shao = build_villager(
            self.interiors["kindergarten"].root,
            name="shao",
            dress_color=(0.38, 0.58, 0.84, 1.0),
            hair_color=(0.14, 0.11, 0.09, 1.0),
            height_scale=0.84,
            hairstyle="short",
        )
        shao.root.setPos(-2.8, -0.2, 0.0)
        shao.root.setH(180)
        self.npcs["shao"] = shao

        mom = build_villager(
            self.interiors["home"].root,
            name="mom",
            dress_color=(0.72, 0.46, 0.42, 1.0),
            hair_color=(0.16, 0.11, 0.09, 1.0),
            height_scale=1.08,
            hairstyle="bob",
            accessory="apron",
        )
        mom.root.setPos(2.3, -0.6, 0.0)
        mom.root.setH(180)
        self.npcs["mom"] = mom

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
            Interactable(
                "swing_game",
                "玩秋千节奏",
                (-17.2, -14.8, 0.9),
                (-17.2, -16.2),
                self.start_rhythm_game,
                radius=2.4,
                kind="game",
            ),
            Interactable(
                "park_catch",
                "接住花瓣",
                (13.0, -12.0, 0.9),
                (13.0, -13.1),
                self.start_catch_game,
                radius=2.4,
                kind="game",
            ),
            Interactable(
                "memory_game",
                "玩山路记忆",
                (2.8, 14.8, 1.4),
                (2.8, 13.4),
                self.start_memory_game,
                radius=2.4,
                kind="game",
            ),
        ]
        home_interactables: list[Interactable] = [
            Interactable(
                "mom",
                "和妈妈说话",
                (2.3, -0.6, 0.7),
                (2.3, -1.8),
                self.talk_mom,
                radius=2.5,
                kind="npc",
            ),
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
                (1.5, -1.2, 0.8),
                (1.5, -2.4),
                self.talk_lin,
                radius=2.4,
                kind="npc",
            ),
            Interactable(
                "an",
                "和安思宜说话",
                (2.8, -0.2, 0.6),
                (2.8, -1.5),
                self.talk_an,
                radius=2.4,
                kind="npc",
            ),
            Interactable(
                "shao",
                "和邵文星说话",
                (-2.8, -0.2, 0.6),
                (-2.8, -1.5),
                self.talk_shao,
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
                "story_game",
                "整理故事卡片",
                (0.0, 0.8, 0.9),
                (0.0, -0.4),
                self.start_story_game,
                radius=2.4,
                kind="game",
            ),
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
            "home": [self.npcs["mom"]],
            "kindergarten": [self.npcs["lin"], self.npcs["an"], self.npcs["shao"]],
            "library": [self.npcs["gu"]],
        }
        self.interactables = self.scene_interactables["town"]
        self.active_npcs = self.scene_active_npcs["town"]

    def _setup_find_game(self) -> None:
        self.find_game = default_find_game()
        self._find_slot: GameSlot | None = None
        self.find_nodes: dict[str, object] = {}
        self.find_interactable_ids: set[str] = set()
        self._sparkle_time = 0.0
        for target_id, (x, y, z) in self.find_game.targets.items():
            group = self.scene.root.attachNewNode(f"sparkle_{target_id}")
            group.setPos(x, y, z)
            meshkit.add_sphere(
                group,
                "sparkle_core",
                (0, 0, 0),
                0.18,
                (1.0, 0.88, 0.40, 1.0),
                rings=8,
                segments=12,
            )
            meshkit.add_disc(
                group,
                "sparkle_ring",
                (0, 0, -z + 0.04),
                0.34,
                (1.0, 0.78, 0.28, 0.38),
                segments=18,
                alpha=0.38,
            )
            group.hide()
            self.find_nodes[target_id] = group
        meshkit.add_box(
            self.scene.root,
            "find_sign_post",
            (4.0, -3.0, 0.7),
            (0.12, 0.12, 1.4),
            PALETTE["wood_dark"],
        )
        meshkit.add_box(
            self.scene.root,
            "find_sign_board",
            (4.0, -3.0, 1.35),
            (1.4, 0.1, 0.55),
            PALETTE["honey"],
        )
        self.town_interactables.append(
            Interactable(
                "find_game",
                "玩小镇找一找",
                (4.0, -3.0, 1.2),
                (4.0, -4.4),
                self.start_find_game,
                radius=2.4,
                kind="game",
            )
        )

    def _setup_events(self) -> None:
        # 简单的场景道具，让环境事件有可见的落点。
        town = self.scene.root
        library = self.interiors["library"].root
        kindergarten = self.interiors["kindergarten"].root
        meshkit.add_box(town, "notice_post", (-4.0, 4.0, 0.7), (0.1, 0.1, 1.4), PALETTE["wood_dark"])
        meshkit.add_box(town, "notice_board", (-4.0, 4.0, 1.4), (1.5, 0.1, 0.8), PALETTE["honey"])
        meshkit.add_box(town, "picnic_blanket", (22.0, -14.0, 0.02), (2.4, 1.8, 0.03), (0.82, 0.45, 0.40, 1.0))
        meshkit.add_cylinder(town, "picnic_basket", (23.0, -14.0, 0.05), 0.28, 0.24, 0.35, PALETTE["wood"], segments=12)
        meshkit.add_sphere(town, "tree_balloon", (-16.5, -13.5, 2.4), 0.22, PALETTE["balloon"], rings=8, segments=12)
        meshkit.add_line(town, "tree_balloon_string", (-16.5, -13.5, 2.18), (-16.5, -13.5, 1.5), PALETTE["lace"], thickness=1.0)
        meshkit.add_sphere(town, "squirrel_body", (2.0, 20.0, 3.0), 0.16, (0.55, 0.36, 0.23, 1.0), rings=7, segments=10, scale=(1.0, 1.2, 0.8))
        meshkit.add_sphere(town, "squirrel_head", (2.0, 20.15, 3.15), 0.10, (0.62, 0.42, 0.27, 1.0), rings=6, segments=9)
        meshkit.add_sphere(town, "squirrel_tail", (1.82, 19.9, 3.2), 0.12, (0.48, 0.30, 0.20, 1.0), rings=6, segments=9, scale=(0.7, 0.8, 1.4))
        meshkit.add_box(kindergarten, "art_red", (-0.9, 4.28, 1.6), (0.55, 0.06, 0.7), PALETTE["coral"])
        meshkit.add_box(kindergarten, "art_yellow", (0.0, 4.28, 1.6), (0.55, 0.06, 0.7), PALETTE["honey"])
        meshkit.add_box(kindergarten, "art_blue", (0.9, 4.28, 1.6), (0.55, 0.06, 0.7), PALETTE["water"])
        meshkit.add_box(kindergarten, "lost_mitten", (-4.6, 2.4, 0.12), (0.34, 0.24, 0.12), (0.93, 0.45, 0.42, 1.0))
        # 图书馆的猫。
        meshkit.add_sphere(library, "cat_body", (3.8, 2.2, 0.3), 0.28, (0.95, 0.72, 0.46, 1.0), rings=8, segments=12, scale=(1.2, 0.9, 0.6))
        meshkit.add_sphere(library, "cat_head", (4.0, 2.2, 0.5), 0.18, (0.97, 0.76, 0.52, 1.0), rings=7, segments=10)
        for x in (-0.08, 0.08):
            meshkit.add_box(library, "cat_ear", (4.0 + x, 2.2, 0.66), (0.09, 0.04, 0.12), (0.80, 0.54, 0.38, 1.0))
        meshkit.add_sphere(library, "cat_tail", (3.45, 2.2, 0.26), 0.08, (0.88, 0.62, 0.40, 1.0), rings=5, segments=8, scale=(1.6, 0.7, 0.7))

        town_events = [
            ("notice", "看看广场告示牌", (-4.0, 4.0, 1.3), (-4.0, 2.8)),
            ("fountain", "在喷泉边许愿", (0.0, 0.0, 1.2), (0.0, 3.2)),
            ("scarf", "长椅上的围巾", (22.0, -14.0, 0.8), (22.0, -15.2)),
            ("balloon", "树上的气球", (-16.5, -13.5, 2.3), (-16.5, -14.8)),
            ("sandcastle", "沙坑里的城堡", (-20.0, -14.0, 0.6), (-20.0, -15.5)),
            ("squirrel", "山道边的松鼠", (2.0, 20.0, 3.1), (2.0, 18.8)),
            ("lantern", "山顶的灯笼", (2.5, 33.5, 7.4), (2.5, 32.2)),
        ]
        for event_id, label, pos, approach in town_events:
            self.town_interactables.append(
                Interactable(
                    f"event_{event_id}",
                    label,
                    pos,
                    approach,
                    lambda eid=event_id: self.trigger_event(eid),
                    radius=2.5,
                    kind="event",
                )
            )
        self.town_interactables.append(
            Interactable(
                "ducks_talk",
                "和鸭子一家说话",
                (18.2, -16.0, 0.7),
                (18.2, -18.0),
                self.talk_ducks,
                radius=2.8,
                kind="npc",
            )
        )
        for event_id, label, pos, approach in [
            ("cat", "看看猫窝里的团子", (3.8, 2.2, 0.7), (3.8, 1.0)),
            ("books", "地上的书", (-1.6, 2.0, 0.8), (-2.6, 0.8)),
        ]:
            self.scene_interactables["library"].append(
                Interactable(
                    f"event_{event_id}",
                    label,
                    pos,
                    approach,
                    lambda eid=event_id: self.trigger_event(eid),
                    radius=2.5,
                    kind="event",
                )
            )
        for event_id, label, pos, approach in [
            ("art", "教室里的画", (0.0, 4.2, 1.6), (0.0, 3.0)),
            ("mitten", "储物格下的小手套", (-4.6, 2.4, 0.5), (-4.6, 1.2)),
        ]:
            self.scene_interactables["kindergarten"].append(
                Interactable(
                    f"event_{event_id}",
                    label,
                    pos,
                    approach,
                    lambda eid=event_id: self.trigger_event(eid),
                    radius=2.5,
                    kind="event",
                )
            )

    def _setup_game_markers(self) -> None:
        self.game_marker_nodes: dict[str, object] = {}
        self.game_marker_ids: set[str] = set()
        self._refresh_game_markers()

    def _game_marker_configs(
        self,
    ) -> dict[str, tuple[str, tuple[float, float, float], tuple[float, float]]]:
        return {
            "shape": ("kindergarten", (3.2, 1.4, 0.75), (3.2, 0.2)),
            "catch": ("town", (13.0, -12.0, 0.95), (13.0, -13.1)),
            "rhythm": ("town", (-17.2, -14.8, 1.25), (-17.2, -16.2)),
            "story": ("library", (0.0, 0.8, 0.95), (0.0, -0.4)),
            "find": ("town", (4.0, -3.0, 1.35), (4.0, -4.4)),
            "memory": ("town", (2.8, 14.8, 1.70), (2.8, 13.4)),
        }

    def _refresh_game_markers(self) -> None:
        """只显示今天的每日小游戏；完成后显示 √，换天时重建。"""
        if not hasattr(self, "scene_interactables"):
            return
        for node in self.game_marker_nodes.values():
            node.removeNode()
        self.game_marker_nodes = {}
        for items in self.scene_interactables.values():
            items[:] = [item for item in items if item.id not in self.game_marker_ids]
        self.game_marker_ids.clear()

        for kind, (scene_id, pos, approach) in self._game_marker_configs().items():
            slot = slot_for(self.clock.day, kind)
            if slot is None:
                continue
            previous = self.state.minigames.get(slot.id)
            completed = bool(previous and previous.completed)
            symbol = "√" if completed else "?"
            color = (
                Vec4(0.28, 0.78, 0.44, 1.0)
                if completed
                else Vec4(1.0, 0.72, 0.16, 1.0)
            )
            text = TextNode(f"game_marker_{slot.id}")
            text.setText(symbol)
            if self.font is not None:
                text.setFont(self.font)
            text.setTextColor(color)
            text.setAlign(TextNode.ACenter)
            text.setShadow(0.035, 0.035)
            parent = (
                self.town_scene.root
                if scene_id == "town"
                else self.interiors[scene_id].root
            )
            node = parent.attachNewNode(text)
            node.setPos(*pos)
            node.setScale(0.55)
            node.setBillboardPointEye()
            node.setDepthTest(False)
            node.setDepthWrite(False)
            node.setLightOff()
            node.setBin("fixed", 60)
            halo = meshkit.add_disc(
                node,
                f"game_marker_halo_{slot.id}",
                (0, 0, -0.12),
                0.34,
                (1.0, 0.82, 0.30, 1.0),
                segments=24,
                alpha=0.42 if not completed else 0.30,
            )
            halo.setDepthTest(False)
            halo.setDepthWrite(False)
            halo.setLightOff()
            halo.setBin("fixed", 59)
            self.game_marker_nodes[slot.id] = node

            interaction_id = f"game_marker_{slot.id}"
            self.game_marker_ids.add(interaction_id)
            label = f"{'再玩' if completed else '开始'}：{slot.title}"
            self.scene_interactables[scene_id].append(
                Interactable(
                    interaction_id,
                    label,
                    pos,
                    approach,
                    lambda k=kind: self._start_today_game(k),
                    radius=2.7,
                    kind="game",
                )
            )

    def _start_today_game(self, kind: str) -> None:
        if self.mode != "playing":
            return
        starters = {
            "shape": self.start_shape_game,
            "catch": self.start_catch_game,
            "rhythm": self.start_rhythm_game,
            "story": self.start_story_game,
            "find": self.start_find_game,
            "memory": self.start_memory_game,
        }
        starter = starters.get(kind)
        if starter is not None:
            starter()

    def trigger_event(self, event_id: str) -> None:
        flag = f"event_{event_id}_seen"
        if self.state.flags.get(flag):
            self.ui.toast("这里已经看过啦。", 1.6)
            return
        self.start_dialogue(f"ev_{event_id}_1")

    def talk_ducks(self) -> None:
        self.start_dialogue("ducks_talk_1")

    def _setup_input(self) -> None:
        self.accept("mouse1", self._on_left_click)
        self.accept("wheel_up", self._on_wheel_up)
        self.accept("wheel_down", self._on_wheel_down)
        self.accept("f11", self.toggle_fullscreen)
        self.accept("window-close", self._on_window_close)

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
        return self._screen_to_ground(self.mouseWatcherNode.getMouse())

    def _screen_to_ground(self, mouse: Point2) -> Point3 | None:
        near = Point3()
        far = Point3()
        self.camLens.extrude(mouse, near, far)
        # extrude 返回相机空间坐标；转换到世界空间要用 render 相对 cam。
        near_world = self.render.getRelativePoint(self.cam, near)
        far_world = self.render.getRelativePoint(self.cam, far)
        direction = far_world - near_world
        if abs(direction.z) < 1e-6:
            return None

        # 平坦地面优先用解析交点，避免低角度点击时采样过粗。
        t_plane = (0.03 - near_world.z) / direction.z
        if t_plane > 0:
            plane_point = near_world + direction * t_plane
            if (
                abs(plane_point.x) <= WORLD_HALF - 1
                and abs(plane_point.y) <= WORLD_HALF - 1
                and abs(self._ground_height(plane_point.x, plane_point.y)) < 0.12
            ):
                return Point3(
                    plane_point.x,
                    plane_point.y,
                    self._ground_height(plane_point.x, plane_point.y),
                )

        # 山道/斜坡：沿射线找第一次低于地面的位置。
        steps = 240
        last = near_world
        for i in range(1, steps + 1):
            t = i / steps
            point = near_world + direction * t
            if abs(point.x) > WORLD_HALF - 1 or abs(point.y) > WORLD_HALF - 1:
                last = point
                continue
            height = self._ground_height(point.x, point.y)
            if point.z <= height + 0.05 and last.z > height:
                return Point3(point.x, point.y, height)
            last = point
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
            if self.find_game.active:
                self._sparkle_time += dt
                for index, node in enumerate(self.find_nodes.values()):
                    node.setR(self._sparkle_time * 70 + index * 40)
                    node.setScale(1.0 + math.sin(self._sparkle_time * 3 + index) * 0.12)
            if self.player.moving:
                self._step_timer -= dt
                if self._step_timer <= 0:
                    self.audio.play_sfx("step", volume=0.35)
                    self._step_timer = 0.36
            else:
                self._step_timer = 0.0
            self._update_orbit(dt)
            self._update_marker(dt)
            self._update_hint(dt)
            self._update_hover()
            self._update_pending_interaction()
            self._update_hud()
            audio_key = (self.current_scene_id, self.clock.day, self.clock.phase)
            if audio_key != self._last_audio_key:
                self._last_audio_key = audio_key
                self._update_music_for_state()
            self._check_sticker_milestones()
        elif self.mode == "dialogue":
            self.player.rig.update(dt, False)
            self.dialogue_ui.update(dt)
            self.hover_ring.hide()
        elif self.mode in {"minigame", "diary", "ending"}:
            self.player.rig.update(dt, False)
            self.hover_ring.hide()
            if self.mode == "minigame":
                self.rhythm_ui.update(dt)
                self.catch_ui.update(dt)
                self.memory_ui.update(dt)
        elif self.mode == "transition":
            self.player.rig.update(dt, False)
            self.hover_ring.hide()
            self.night_ui.update(dt)
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

    def talk_an(self) -> None:
        self.start_dialogue("an_intro_1")

    def talk_shao(self) -> None:
        self.start_dialogue("shao_intro_1")

    def talk_mom(self) -> None:
        if self.clock.phase == "morning":
            self.start_dialogue("mom_morning_1")
        elif self.clock.phase == "dusk":
            self.start_dialogue("mom_night_1")
        else:
            self.start_dialogue("mom_afternoon_1")

    def _mom_auto_greeting(self) -> None:
        if self.mode != "playing" or self.current_scene_id != "home":
            return
        day = self.clock.day
        if self.clock.phase == "morning":
            key = f"mom_morning_{day}"
            message = "妈妈：早上好，淇淇。今天也要开开心心的。"
        elif self.clock.phase == "dusk":
            key = f"mom_night_{day}"
            message = "妈妈：晚安，淇淇。做个好梦。"
        else:
            key = f"mom_hug_{day}"
            message = "妈妈抱了抱淇淇，还亲了亲额头。"
        if self.state.flags.get(key):
            return
        self.state.flags[key] = True
        self.audio.play_sfx("success", volume=0.4)
        self.ui.toast(message, 3.2)

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
        self.audio.play_sfx("page")
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
            self._check_sticker_milestones()
            self._auto_save()

    # ---------------------------------------------------------------- minigames
    def _slot_for_kind(self, kind: str) -> GameSlot | None:
        slot = slot_for(self.clock.day, kind)
        if slot is None:
            self.ui.toast("今天的小游戏不在这个地点，看看日记里的安排吧。", 2.6)
        return slot

    def _begin_aux_minigame(self) -> bool:
        if self.mode != "playing":
            return False
        self.audio.play_sfx("click")
        self.mode = "minigame"
        self.clock.paused = True
        self.player.stop()
        self._pending_interaction = None
        self.hover_ring.hide()
        self.ui.hide_all()
        return True

    def start_shape_game(self) -> None:
        slot = self._slot_for_kind("shape")
        if slot is not None:
            self.start_minigame(slot.id)

    def start_story_game(self) -> None:
        slot = self._slot_for_kind("story")
        if slot is not None and self._begin_aux_minigame():
            self.story_order_ui.start(slot.id)

    def start_rhythm_game(self) -> None:
        slot = self._slot_for_kind("rhythm")
        if slot is not None and self._begin_aux_minigame():
            self.rhythm_ui.start(slot.id)

    def start_catch_game(self) -> None:
        slot = self._slot_for_kind("catch")
        if slot is not None and self._begin_aux_minigame():
            self.catch_ui.start(slot.id)

    def start_memory_game(self) -> None:
        slot = self._slot_for_kind("memory")
        if slot is not None and self._begin_aux_minigame():
            self.memory_ui.start(slot.id)

    def start_find_game(self) -> None:
        if self.mode != "playing" or self.current_scene_id != "town":
            self.ui.toast("回中心广场再开始找一找吧。")
            return
        if self.find_game.active:
            return
        slot = self._slot_for_kind("find")
        if slot is None:
            return
        self._find_slot = slot
        self.find_game.start()
        for node in self.find_nodes.values():
            node.show()
        approaches = {
            "fountain": (3.8, 1.8),
            "park": (13.0, -11.0),
            "playground": (-18.0, -10.6),
            "library": (-12.0, -1.6),
            "trail": (0.0, 21.0),
        }
        for target_id, (x, y, z) in self.find_game.targets.items():
            interaction_id = f"find_sparkle_{target_id}"
            self.find_interactable_ids.add(interaction_id)
            self.town_interactables.append(
                Interactable(
                    interaction_id,
                    self.find_game.labels.get(target_id, "闪光的小东西"),
                    (x, y, z),
                    approaches.get(target_id, (x, y - 1.0)),
                    lambda tid=target_id: self._collect_sparkle(tid),
                    radius=2.4,
                    kind="sparkle",
                )
            )
        self.audio.play_sfx("page")
        self.ui.toast(f"今日小游戏：{slot.title}。小镇里藏着 5 个闪光的小东西。", 3.0)
        self._update_hud()

    def _collect_sparkle(self, target_id: str) -> None:
        result = self.find_game.collect(target_id)
        if result not in {"collected", "complete"}:
            return
        node = self.find_nodes.get(target_id)
        if node is not None:
            node.hide()
        interaction_id = f"find_sparkle_{target_id}"
        self.find_interactable_ids.discard(interaction_id)
        self.town_interactables[:] = [
            item for item in self.town_interactables if item.id != interaction_id
        ]
        self.audio.play_sfx("success", volume=0.6)
        if result == "complete":
            self.find_game.stop()
            for item in self.find_nodes.values():
                item.hide()
            slot = self._find_slot
            self._find_slot = None
            if slot is not None:
                previous = self.state.minigames.get(slot.id)
                plays = (previous.plays if previous else 0) + 1
                self.state.minigames[slot.id] = MinigameState(completed=True, best=5, plays=plays)
                self.state.add_sticker(slot.sticker)
                self.state.add_journal(slot.journal)
                self.state.add_friendship(slot.friend, 1)
            self.ui.toast("找到了全部闪光！获得回忆贴纸：小镇侦探。", 3.2)
            self._sync_state_from_world()
            self._refresh_game_markers()
            self._auto_save()
        else:
            self.ui.toast(f"找到一个闪光（{len(self.find_game.found)}/{self.find_game.total}）。", 2.0)
        self._update_hud()

    def _stop_find_game(self, *, silent: bool = False) -> None:
        if not hasattr(self, "find_game"):
            return
        self.find_game.stop()
        self._find_slot = None
        for node in self.find_nodes.values():
            node.hide()
        for interaction_id in list(self.find_interactable_ids):
            self.town_interactables[:] = [
                item for item in self.town_interactables if item.id != interaction_id
            ]
        self.find_interactable_ids.clear()
        if not silent:
            self.ui.toast("找一找先停下来了。", 1.8)

    def start_minigame(self, game_id: str) -> None:
        if not self._begin_aux_minigame():
            return
        self.minigame_ui.start(game_id)

    def end_minigame(self, *, success: bool, game_id: str) -> None:
        self.minigame_ui.hide()
        self._finish_minigame_result(success=success, game_id=game_id)

    def end_extra_minigame(self, *, success: bool, game_id: str) -> None:
        self.story_order_ui.hide()
        self.rhythm_ui.hide()
        self.catch_ui.hide()
        self.memory_ui.hide()
        self._finish_minigame_result(success=success, game_id=game_id)

    def _finish_minigame_result(self, *, success: bool, game_id: str) -> None:
        self.mode = "playing"
        self.clock.paused = False
        self.ui.show_hud()
        self._update_hud()
        if not success:
            self.audio.play_sfx("error")
            self.ui.toast("下次再玩吧。", 1.8)
            return
        self.audio.play_sfx("success")
        previous = self.state.minigames.get(game_id)
        plays = (previous.plays if previous else 0) + 1
        best = max(previous.best if previous else 0, 3)
        self.state.minigames[game_id] = MinigameState(completed=True, best=best, plays=plays)
        slot = slot_by_id(game_id)
        if slot is not None:
            new_sticker = self.state.add_sticker(slot.sticker)
            self.state.add_journal(slot.journal)
            self.state.add_friendship(slot.friend, 1)
            name = slot.title
        else:
            fallback = {
                "day1_shapes": ("sticker_shapes", "journal_shapes", "lin", "形状小管家"),
                "library_story": ("sticker_story", "journal_story", "gu", "故事排排队"),
                "playground_rhythm": ("sticker_swing", "journal_swing", "chen", "秋千节奏"),
                "park_catch": ("sticker_ducks", "journal_ducks", "su", "接住花瓣"),
                "mountain_memory": ("sticker_memory", "journal_memory", "zhou", "山路记忆"),
            }
            sticker, journal, friend, name = fallback.get(game_id, ("", "", "", "小游戏"))
            new_sticker = bool(sticker) and self.state.add_sticker(sticker)
            if journal:
                self.state.add_journal(journal)
            if friend:
                self.state.add_friendship(friend, 1)
        if new_sticker:
            self.ui.toast(f"获得回忆贴纸：{name}！", 2.6)
        else:
            self.ui.toast(f"又完成了一次{name}。", 2.0)
        self._sync_state_from_world()
        self._check_sticker_milestones()
        self._refresh_game_markers()
        self._auto_save()

    # ---------------------------------------------------------------- quests/day
    def _daily_complete(self, day: int) -> bool:
        quest = self.state.quests.get(f"day{day}_main")
        return quest is not None and quest.status == "complete"

    def _check_sticker_milestones(self) -> bool:
        added = False
        if self.current_scene_id == "town" and self.player.position[1] >= 31.0:
            added = self.state.add_sticker("sticker_summit") or added
        friends = ("xiaoman", "lin", "gu", "su", "chen", "an", "shao", "mom")
        if all(self.state.friendship.get(name, 0) >= 1 for name in friends):
            added = self.state.add_sticker("sticker_friend_all") or added
        if len(self.state.stickers) >= 10:
            added = self.state.add_sticker("sticker_diary") or added
        if all(
            self.state.flags.get(f"event_{name}_seen")
            for name in ("books", "cat", "notice")
        ):
            added = self.state.add_sticker("sticker_rain") or added
        if added:
            self.ui.toast("获得新的回忆贴纸！", 2.2)
        return added

    def _day1_complete(self) -> bool:
        return self._daily_complete(1)

    def _current_objective(self) -> str:
        if getattr(self, "find_game", None) is not None and self.find_game.active:
            return (
                f"目标：找到小镇里的闪光（{len(self.find_game.found)}/{self.find_game.total}）"
            )
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
        if self.mode != "playing":
            return
        if self.clock.day >= 5:
            if self.state.story_complete:
                self.ui.toast("灯会已经结束啦。可以继续在小镇里逛逛。", 2.6)
            else:
                self.ui.toast("今天是灯会，去山顶看灯吧。", 2.6)
            return
        if not self._daily_complete(self.clock.day):
            self.ui.toast("今天还有一件事没做完呢。先在镇上逛逛，或者再去和小镇居民说说话。", 3.2)
            return
        self.mode = "transition"
        self.clock.paused = True
        self.player.stop()
        self._pending_interaction = None
        self.hover_ring.hide()
        self.ui.hide_all()
        self.audio.play_sfx("page", volume=0.5)
        self.night_ui.start(
            self.clock.day + 1,
            self._advance_to_next_day,
            self._finish_night_transition,
            night_message="妈妈轻轻抱了抱你：晚安，淇淇。",
        )

    def _advance_to_next_day(self) -> None:
        self.clock.advance_day()
        self.state.day = self.clock.day
        self.state.time_minutes = self.clock.minute_int
        quest_id = f"day{self.state.day}_main"
        if quest_id not in self.state.quests:
            from qiqi_town.core.state import QuestState

            self.state.quests[quest_id] = QuestState(step=0, status="active")
        self._refresh_game_markers()
        self._activate_scene("home", self.interiors["home"].spawn, 0.0)
        self.state.location = "home"
        self._sync_state_from_world()

    def _finish_night_transition(self) -> None:
        self.mode = "playing"
        self.clock.paused = False
        self.ui.show_hud()
        self._update_hud()
        self._sync_state_from_world()
        self.ui.toast(f"第 {self.clock.day} 天开始了。", 2.0)
        self._mom_auto_greeting()
        self._auto_save()

    def show_ending(self) -> None:
        self.mode = "ending"
        self.clock.paused = True
        self.player.stop()
        self._pending_interaction = None
        self.hover_ring.hide()
        self.ui.hide_all()
        self.audio.play_music("dusk")
        self.audio.stop_ambient()
        self.audio.play_sfx("lantern")
        self.ending_ui.show()
        self._sync_state_from_world()
        self._auto_save()

    def finish_ending(self) -> None:
        self.audio.play_sfx("choose")
        self.ending_ui.hide()
        self.mode = "playing"
        self.clock.paused = False
        self.ui.show_hud()
        self._last_audio_key = None
        self._update_music_for_state()
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
        self.ui.set_interior(self.current_scene_id != "town")

    # ---------------------------------------------------------------- scenes
    def _activate_scene(
        self,
        scene_id: str,
        position: tuple[float, float] | None = None,
        facing: float = 0.0,
    ) -> None:
        if (
            hasattr(self, "find_game")
            and self.find_game.active
            and scene_id != "town"
        ):
            self._stop_find_game(silent=True)
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
        self._last_audio_key = None
        self._update_music_for_state()
        self._update_hud()

    def enter_interior(self, scene_id: str) -> None:
        if scene_id not in self.interiors:
            return
        self.audio.play_sfx("door")
        self._activate_scene(scene_id, self.interiors[scene_id].spawn, 0.0)
        names = {"home": "家", "kindergarten": "幼儿园", "library": "图书馆"}
        self.ui.toast(f"进入{names.get(scene_id, '房间')}。", 1.5)
        self._mom_auto_greeting()

    def exit_to_town(self) -> None:
        spawns = {
            "home": (-10.0, -17.0),
            "kindergarten": (12.0, 0.8),
            "library": (-14.0, -0.3),
        }
        self.audio.play_sfx("door")
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
        self.tutorial.stop()
        self._in_game = False
        self.mode = "title"
        self.clock.paused = True
        self.player.stop()
        self.audio.stop_all()
        self.audio.play_music("town_day")
        self.audio.play_ambient("ambience_town")
        self.ui.show_title()

    def quit_game(self) -> None:
        if self._in_game:
            self._auto_save()
        self.userExit()

    def _on_window_close(self) -> None:
        self.quit_game()

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
        if hasattr(self, "find_game") and self.find_game.active:
            self._stop_find_game(silent=True)
        self._in_game = True
        self.state = GameState.new_game()
        self.state.location = "town"
        self.state.player.x, self.state.player.y = self.town_scene.player_start
        self.state.player.facing = math.pi
        self.clock = GameClock(day=self.state.day, minutes=self.state.time_minutes)
        self.clock.paused = False
        self._refresh_game_markers()
        self._activate_scene("town", self.town_scene.player_start, math.pi)
        self.mode = "playing"
        self.ui.hide_confirm()
        self.ui.show_hud()
        self._update_hud()
        self.ui.toast("新的一天开始了。")
        self.tutorial.start()
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
            self.audio.play_sfx("error")
            self.ui.toast(f"保存失败：{exc.message}")
            return
        self.audio.play_sfx("save")
        self.ui.refresh_save()
        self.ui.toast(f"已保存到槽位 {slot:02d}。")

    def _do_load_slot(self, slot: int, is_auto: bool) -> None:
        try:
            state = self.save_repo.load("auto" if is_auto else slot)
        except SaveError as exc:
            self.audio.play_sfx("error")
            self.ui.toast(f"读取失败：{exc.message}")
            return
        self.audio.play_sfx("choose")
        self.apply_state(state)

    def _delete_slot(self, slot: int) -> None:
        try:
            self.save_repo.delete_manual(slot)
        except SaveError as exc:
            self.audio.play_sfx("error")
            self.ui.toast(f"删除失败：{exc.message}")
            return
        self.audio.play_sfx("choose")
        self.ui.refresh_save()
        self.ui.toast(f"槽位 {slot:02d} 已删除。")

    def apply_state(self, state: GameState, *, notify: bool = False) -> None:
        if hasattr(self, "find_game") and self.find_game.active:
            self._stop_find_game(silent=True)
        self._in_game = True
        self.state = state
        self.clock = GameClock(day=state.day, minutes=state.time_minutes)
        self.clock.paused = False
        scene_id = state.location if state.location in self.scene_roots else "town"
        self.state.location = scene_id
        self._refresh_game_markers()
        self._activate_scene(scene_id, (state.player.x, state.player.y), state.player.facing)
        self.mode = "playing"
        self.ui.hide_confirm()
        self.ui.show_hud()
        self._update_hud()
        self._mom_auto_greeting()
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

    # ---------------------------------------------------------------- audio
    def _update_music_for_state(self) -> None:
        if self.current_scene_id == "town":
            track = "dusk" if (self.clock.day == 5 or self.clock.phase == "dusk") else "town_day"
            ambient = "ambience_town"
        else:
            track = "interior"
            ambient = "ambience_interior"
        self.audio.play_music(track)
        self.audio.play_ambient(ambient)

    # ---------------------------------------------------------------- settings
    def save_settings(self) -> None:
        self.settings_repo.save(self.settings)
        self.camera_rig.set_sensitivity(self.settings.camera_sensitivity)
        self.audio.set_volumes(
            self.settings.master_volume,
            self.settings.music_volume,
            self.settings.sfx_volume,
        )

    def toggle_fullscreen(self) -> None:
        if self.args.smoke_test:
            return
        self.settings.fullscreen = not self.settings.fullscreen
        self._apply_fullscreen(self.settings.fullscreen)
        self.save_settings()
        self.ui.toast("已进入全屏模式（F11 切换）。" if self.settings.fullscreen else "已切换到窗口模式（F11 切换）。")

    def _apply_fullscreen(self, enabled: bool) -> None:
        props = WindowProperties()
        if enabled:
            # 无边框全屏比切换显示分辨率更稳，不会因显卡/远程桌面拒绝模式切换。
            props.setFullscreen(False)
            props.setUndecorated(True)
            props.setOrigin(0, 0)
            props.setSize(self.pipe.getDisplayWidth(), self.pipe.getDisplayHeight())
        else:
            props.setFullscreen(False)
            props.setUndecorated(False)
            props.setSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.win.requestProperties(props)

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
            self.end_minigame(success=True, game_id=self.minigame_ui._game_id)
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
    if args.smoke_test:
        loadPrcFileData("", "audio-library-name null")
    else:
        loadPrcFileData("", "audio-library-name p3openal_audio")
    loadPrcFileData("", "notify-level warning")
    loadPrcFileData("", "default-directnotify-level warning")
    if args.smoke_test:
        loadPrcFileData("", "window-type offscreen")
        loadPrcFileData("", "win-size 1600 900")
