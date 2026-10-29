"""DirectGUI 界面：标题、HUD、暂停、存档、设置、确认框。"""

from __future__ import annotations

from collections.abc import Callable

from direct.gui import DirectGuiGlobals as DGG
from direct.gui.DirectGui import DirectButton, DirectFrame, DirectSlider
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import NodePath, TextNode, TransparencyAttrib


class UiManager:
    def __init__(self, app) -> None:
        self.app = app
        self.font = app.font
        self.root = app.aspect2d.attachNewNode("ui_root")
        self.title_root = self._new_root("title")
        self.pause_root = self._new_root("pause")
        self.save_root = self._new_root("save")
        self.settings_root = self._new_root("settings")
        self.confirm_root = self._new_root("confirm")
        self.hud_root = self._new_root("hud")
        self._save_mode = "load"
        self._delete_mode = False
        self._settings_return = "pause"
        self._confirm_yes: Callable[[], None] | None = None

        self._build_title()
        self._build_pause()
        self._build_save_shell()
        self._build_settings()
        self._build_confirm()
        self._build_hud()
        self.toast_text = self._label(
            self.root,
            "",
            (0.0, 0.94),
            0.036,
            TextNode.ACenter,
            fg=(0.16, 0.14, 0.12, 1.0),
            shadow=(1.0, 0.98, 0.9, 0.9),
        )
        self.toast_text.hide()
        self.hide_all()

    # --------------------------------------------------------------- helpers
    def _new_root(self, name: str) -> NodePath:
        root = self.root.attachNewNode(name)
        root.hide()
        return root

    def _dim(self, root: NodePath, alpha: float = 0.62) -> DirectFrame:
        frame = DirectFrame(
            parent=root,
            frameColor=(0.06, 0.05, 0.045, alpha),
            frameSize=(-2.2, 2.2, -1.6, 1.6),
            relief=DGG.FLAT,
        )
        frame.setTransparency(TransparencyAttrib.MAlpha)
        return frame

    def _panel(
        self,
        root: NodePath,
        frame_size: tuple[float, float, float, float],
        *,
        pos: tuple[float, float, float] = (0, 0, 0),
    ) -> DirectFrame:
        panel = DirectFrame(
            parent=root,
            frameColor=(0.98, 0.945, 0.87, 0.97),
            frameSize=frame_size,
            pos=pos,
            relief=DGG.FLAT,
        )
        panel.setTransparency(TransparencyAttrib.MAlpha)
        return panel

    def _label(
        self,
        root: NodePath,
        text: str,
        pos: tuple[float, float],
        scale: float,
        align=TextNode.ALeft,
        *,
        fg: tuple[float, float, float, float] = (0.18, 0.16, 0.15, 1.0),
        shadow: tuple[float, float, float, float] = (1.0, 0.98, 0.9, 0.75),
    ) -> OnscreenText:
        return OnscreenText(
            parent=root,
            text=text,
            font=self.font,
            pos=pos,
            scale=scale,
            align=align,
            fg=fg,
            shadow=shadow,
            shadowOffset=(0.025, 0.025),
            mayChange=True,
        )

    def _button(
        self,
        root: NodePath,
        text: str,
        pos: tuple[float, float],
        command: Callable[[], None],
        *,
        width: float = 0.46,
        height: float = 0.09,
        text_scale: float = 0.042,
        enabled: bool = True,
        dark: bool = False,
    ) -> DirectButton:
        normal = (0.93, 0.52, 0.43, 0.97) if not dark else (0.34, 0.29, 0.25, 0.95)
        text_fg = (1.0, 0.98, 0.94, 1.0) if enabled else (0.55, 0.52, 0.48, 1.0)
        button = DirectButton(
            parent=root,
            text=text,
            text_font=self.font,
            text_fg=text_fg,
            text_scale=text_scale,
            frameColor=normal,
            frameSize=(-width / 2, width / 2, -height / 2, height / 2),
            pos=(pos[0], 0, pos[1]),
            relief=DGG.FLAT,
            command=command,
        )
        button.setTransparency(TransparencyAttrib.MAlpha)
        if not enabled:
            button["state"] = DGG.DISABLED
        return button

    def _small_button(
        self,
        root: NodePath,
        text: str,
        pos: tuple[float, float],
        command: Callable[[], None],
        *,
        width: float = 0.75,
        height: float = 0.085,
        text_scale: float = 0.031,
    ) -> DirectButton:
        return self._button(
            root,
            text,
            pos,
            command,
            width=width,
            height=height,
            text_scale=text_scale,
        )

    def _show_only(self, root: NodePath | None) -> None:
        for other in (
            self.title_root,
            self.pause_root,
            self.save_root,
            self.settings_root,
            self.confirm_root,
            self.hud_root,
        ):
            if other is root:
                other.show()
            else:
                other.hide()

    # --------------------------------------------------------------- title
    def _build_title(self) -> None:
        self._dim(self.title_root, 0.58)
        self._label(
            self.title_root,
            "淇淇的小镇",
            (0.0, 0.58),
            0.16,
            TextNode.ACenter,
            fg=(1.0, 0.98, 0.92, 1.0),
            shadow=(0.10, 0.08, 0.06, 0.8),
        )
        self._label(
            self.title_root,
            "青禾镇 · 夏日灯会前的五天",
            (0.0, 0.44),
            0.045,
            TextNode.ACenter,
            fg=(1.0, 0.93, 0.80, 1.0),
            shadow=(0.10, 0.08, 0.06, 0.8),
        )
        self.continue_button = self._button(
            self.title_root, "继续游戏", (0, 0.20), self.app.continue_game
        )
        self._button(self.title_root, "新的故事", (0, 0.06), self.app.new_game)
        self._button(self.title_root, "读取存档", (0, -0.08), lambda: self.show_save("load"))
        self._button(self.title_root, "设置", (0, -0.22), self.app.open_settings)
        self._button(self.title_root, "退出游戏", (0, -0.36), self.app.quit_game, dark=True)
        self._label(
            self.title_root,
            "鼠标操作 · 温馨小镇生活",
            (0.0, -0.63),
            0.032,
            TextNode.ACenter,
            fg=(0.95, 0.88, 0.76, 0.9),
        )

    def show_title(self) -> None:
        self._show_only(self.title_root)
        has_saves = self.app.has_saves()
        self.continue_button["state"] = DGG.NORMAL if has_saves else DGG.DISABLED
        self.continue_button["text_fg"] = (
            (1.0, 0.98, 0.94, 1.0) if has_saves else (0.55, 0.52, 0.48, 1.0)
        )

    # --------------------------------------------------------------- pause
    def _build_pause(self) -> None:
        self._dim(self.pause_root, 0.55)
        self._panel(self.pause_root, (-0.56, 0.56, -0.78, 0.78))
        self._label(
            self.pause_root,
            "暂停",
            (0.0, 0.66),
            0.09,
            TextNode.ACenter,
        )
        self._button(self.pause_root, "继续游戏", (0, 0.46), self.app.resume_game)
        self._button(self.pause_root, "保存进度", (0, 0.33), lambda: self.show_save("save"))
        self._button(self.pause_root, "读取存档", (0, 0.20), lambda: self.show_save("load"))
        self._button(self.pause_root, "日记", (0, 0.07), self.app.open_diary)
        self._button(self.pause_root, "设置", (0, -0.06), self.app.open_settings)
        self._button(self.pause_root, "返回标题", (0, -0.19), self.app.return_to_title)
        self._button(self.pause_root, "退出游戏", (0, -0.32), self.app.quit_game, dark=True)

    def show_pause(self) -> None:
        self._show_only(self.pause_root)

    # --------------------------------------------------------------- save/load
    def _build_save_shell(self) -> None:
        self._dim(self.save_root, 0.62)
        self._panel(self.save_root, (-1.25, 1.25, -0.88, 0.88))
        self.save_title = self._label(
            self.save_root,
            "读取存档",
            (0.0, 0.78),
            0.07,
            TextNode.ACenter,
        )
        self.save_hint = self._label(
            self.save_root,
            "",
            (0.0, 0.70),
            0.028,
            TextNode.ACenter,
            fg=(0.45, 0.40, 0.35, 1.0),
        )
        self.auto_slot_root = self.save_root.attachNewNode("auto_slot")
        self.slot_root = self.save_root.attachNewNode("slots")
        self.delete_button = self._small_button(
            self.save_root,
            "删除模式：关",
            (-0.64, -0.79),
            self.toggle_delete_mode,
            width=0.52,
            height=0.075,
            text_scale=0.027,
        )
        self._small_button(
            self.save_root,
            "返回",
            (0.64, -0.79),
            self.back_from_save,
            width=0.42,
            height=0.075,
            text_scale=0.031,
        )

    def show_save(self, mode: str) -> None:
        self._save_mode = mode
        self._delete_mode = False
        if hasattr(self, "delete_button"):
            self.delete_button["text"] = "删除模式：关"
        self._show_only(self.save_root)
        self._refresh_save_screen()

    def _refresh_save_screen(self) -> None:
        is_save = self._save_mode == "save"
        self.save_title["text"] = "保存进度" if is_save else "读取存档"
        self.save_hint["text"] = (
            "选择一个槽位保存当前进度。手动存档最多 20 个。"
            if is_save
            else "选择一个存档继续。自动存档不计入手动档数量。"
        )
        for node in self.slot_root.getChildren():
            node.removeNode()
        for node in self.auto_slot_root.getChildren():
            node.removeNode()

        auto_info = self.app.save_repo.list_all()[0]
        auto_text = self._slot_text(auto_info, "自动存档")
        self._slot_button(
            self.auto_slot_root,
            auto_text,
            (0.0, 0.61),
            1.65,
            0.12,
            lambda: self.app.on_slot_clicked(0, True),
            enabled=not is_save and auto_info.available,
            text_scale=0.032,
        )

        infos = self.app.save_repo.list_slots()
        x_positions = (-0.9, -0.3, 0.3, 0.9)
        y_positions = (0.42, 0.17, -0.08, -0.33, -0.58)
        for index, info in enumerate(infos):
            col = index % 4
            row = index // 4
            label = self._slot_text(info, f"槽位 {info.slot:02d}")
            enabled = True
            if not info.exists:
                enabled = is_save or self._delete_mode
            elif not info.available:
                enabled = False
            if self._delete_mode:
                enabled = info.exists
            self._slot_button(
                self.slot_root,
                label,
                (x_positions[col], y_positions[row]),
                0.56,
                0.21,
                lambda slot=info.slot: self.app.on_slot_clicked(slot, False),
                enabled=enabled,
                text_scale=0.03,
                is_delete=self._delete_mode,
            )

    def _slot_text(self, info, prefix: str) -> str:
        if not info.exists:
            return f"{prefix}\n空"
        if not info.available or info.meta is None:
            return f"{prefix}\n存档损坏"
        meta = info.meta
        return (
            f"{prefix} · 第{meta.day}天 {meta.display_time}\n"
            f"{meta.location_label} · {meta.quest_title}"
        )

    def _slot_button(
        self,
        parent: NodePath,
        text: str,
        pos: tuple[float, float],
        width: float,
        height: float,
        command: Callable[[], None],
        *,
        enabled: bool,
        text_scale: float,
        is_delete: bool = False,
    ) -> DirectButton:
        color = (0.34, 0.30, 0.27, 0.95) if is_delete else (0.92, 0.86, 0.74, 0.97)
        button = DirectButton(
            parent=parent,
            text=text,
            text_font=self.font,
            text_fg=(1.0, 0.98, 0.94, 1.0) if is_delete else (0.22, 0.19, 0.17, 1.0),
            text_scale=text_scale,
            text_align=TextNode.ACenter,
            frameColor=color,
            frameSize=(-width / 2, width / 2, -height / 2, height / 2),
            pos=(pos[0], 0, pos[1]),
            relief=DGG.FLAT,
            command=command,
        )
        button.setTransparency(TransparencyAttrib.MAlpha)
        if not enabled:
            button["state"] = DGG.DISABLED
            button["frameColor"] = (0.72, 0.68, 0.61, 0.55)
        return button

    def toggle_delete_mode(self) -> None:
        self._delete_mode = not self._delete_mode
        self.delete_button["text"] = "删除模式：开" if self._delete_mode else "删除模式：关"
        self._refresh_save_screen()

    def back_from_save(self) -> None:
        self.app.close_save()

    def refresh_save(self) -> None:
        if self.save_root.isHidden():
            return
        self._refresh_save_screen()

    @property
    def save_mode(self) -> str:
        return self._save_mode

    @property
    def delete_mode(self) -> bool:
        return self._delete_mode

    # --------------------------------------------------------------- settings
    def _build_settings(self) -> None:
        self._dim(self.settings_root, 0.58)
        self._panel(self.settings_root, (-0.7, 0.7, -0.72, 0.72))
        self._label(
            self.settings_root,
            "设置",
            (0.0, 0.62),
            0.08,
            TextNode.ACenter,
        )
        settings = self.app.settings
        self.master_label = self._label(self.settings_root, "主音量", (-0.56, 0.40), 0.036)
        self.music_label = self._label(self.settings_root, "音乐", (-0.56, 0.22), 0.036)
        self.sfx_label = self._label(self.settings_root, "音效", (-0.56, 0.04), 0.036)
        self.text_label = self._label(self.settings_root, "文字速度", (-0.56, -0.14), 0.036)
        self.camera_label = self._label(self.settings_root, "镜头灵敏度", (-0.56, -0.32), 0.036)

        self.master_slider = self._slider(
            self.settings_root, (-0.18, 0.40), settings.master_volume, self._on_master
        )
        self.music_slider = self._slider(
            self.settings_root, (-0.18, 0.22), settings.music_volume, self._on_music
        )
        self.sfx_slider = self._slider(
            self.settings_root, (-0.18, 0.04), settings.sfx_volume, self._on_sfx
        )
        self.text_slider = self._slider(
            self.settings_root,
            (-0.18, -0.14),
            (settings.text_speed - 5.0) / 115.0,
            self._on_text_speed,
        )
        self.camera_slider = self._slider(
            self.settings_root,
            (-0.18, -0.32),
            (settings.camera_sensitivity - 0.2) / 2.8,
            self._on_camera,
        )
        self._button(self.settings_root, "窗口 / 全屏", (0, -0.49), self.app.toggle_fullscreen, width=0.52, height=0.075, text_scale=0.03)
        self._button(self.settings_root, "打开存档文件夹", (0, -0.59), self.app.open_save_folder, width=0.52, height=0.07, text_scale=0.026)
        self._button(self.settings_root, "返回", (0, -0.68), self.back_from_settings, width=0.42, height=0.07, text_scale=0.03)
        self._refresh_settings_labels()

    def _slider(self, root: NodePath, pos: tuple[float, float], value: float, command) -> DirectSlider:
        slider = DirectSlider(
            parent=root,
            range=(0.0, 1.0),
            value=max(0.0, min(1.0, float(value))),
            pageSize=0.1,
            frameColor=(0.86, 0.80, 0.69, 0.95),
            thumb_frameColor=(0.93, 0.52, 0.43, 1.0),
            frameSize=(-0.32, 0.32, -0.025, 0.025),
            pos=(pos[0], 0, pos[1]),
            command=command,
        )
        slider.setTransparency(TransparencyAttrib.MAlpha)
        return slider

    def _on_master(self, *args) -> None:
        self.app.settings.master_volume = float(self.master_slider["value"])
        self._refresh_settings_labels()
        self.app.save_settings()

    def _on_music(self, *args) -> None:
        self.app.settings.music_volume = float(self.music_slider["value"])
        self._refresh_settings_labels()
        self.app.save_settings()

    def _on_sfx(self, *args) -> None:
        self.app.settings.sfx_volume = float(self.sfx_slider["value"])
        self._refresh_settings_labels()
        self.app.save_settings()

    def _on_text_speed(self, *args) -> None:
        self.app.settings.text_speed = 5.0 + float(self.text_slider["value"]) * 115.0
        self._refresh_settings_labels()
        self.app.save_settings()

    def _on_camera(self, *args) -> None:
        sensitivity = 0.2 + float(self.camera_slider["value"]) * 2.8
        self.app.settings.camera_sensitivity = sensitivity
        self.app.camera_rig.set_sensitivity(sensitivity)
        self._refresh_settings_labels()
        self.app.save_settings()

    def _refresh_settings_labels(self) -> None:
        s = self.app.settings
        if not hasattr(self, "master_label"):
            return
        self.master_label["text"] = f"主音量  {int(s.master_volume * 100)}%"
        self.music_label["text"] = f"音乐  {int(s.music_volume * 100)}%"
        self.sfx_label["text"] = f"音效  {int(s.sfx_volume * 100)}%"
        self.text_label["text"] = f"文字速度  {int(s.text_speed)}"
        self.camera_label["text"] = f"镜头灵敏度  {s.camera_sensitivity:.1f}"

    def show_settings(self, return_to: str = "pause") -> None:
        self._settings_return = return_to
        self._refresh_settings_labels()
        self._show_only(self.settings_root)

    def back_from_settings(self) -> None:
        self.app.close_settings()

    # --------------------------------------------------------------- confirm
    def _build_confirm(self) -> None:
        self._dim(self.confirm_root, 0.68)
        self._panel(self.confirm_root, (-0.55, 0.55, -0.30, 0.30))
        self.confirm_label = self._label(
            self.confirm_root,
            "",
            (0.0, 0.08),
            0.042,
            TextNode.ACenter,
        )
        self._button(
            self.confirm_root,
            "确定",
            (-0.22, -0.16),
            self._on_confirm_yes,
            width=0.30,
            height=0.08,
            text_scale=0.035,
        )
        self._button(
            self.confirm_root,
            "取消",
            (0.22, -0.16),
            self.hide_confirm,
            width=0.30,
            height=0.08,
            text_scale=0.035,
            dark=True,
        )

    def show_confirm(self, text: str, on_yes: Callable[[], None]) -> None:
        self._confirm_yes = on_yes
        self.confirm_label["text"] = text
        self.confirm_root.show()

    def hide_confirm(self) -> None:
        self._confirm_yes = None
        self.confirm_root.hide()

    def _on_confirm_yes(self) -> None:
        callback = self._confirm_yes
        self.hide_confirm()
        if callback is not None:
            callback()

    # --------------------------------------------------------------- hud
    def _build_hud(self) -> None:
        self.hud_title = self._label(
            self.hud_root,
            "青禾镇 · 第 1 天",
            (-1.27, 0.87),
            0.055,
            TextNode.ALeft,
            fg=(0.18, 0.16, 0.15, 1.0),
            shadow=(1.0, 0.98, 0.9, 0.85),
        )
        self.hud_time = self._label(
            self.hud_root,
            "08:00",
            (-1.27, 0.79),
            0.036,
            TextNode.ALeft,
            fg=(0.18, 0.16, 0.15, 1.0),
            shadow=(1.0, 0.98, 0.9, 0.85),
        )
        self.hud_objective = self._label(
            self.hud_root,
            "目标：去幼儿园找林老师",
            (-1.27, 0.72),
            0.036,
            TextNode.ALeft,
            fg=(0.18, 0.16, 0.15, 1.0),
            shadow=(1.0, 0.98, 0.9, 0.85),
        )
        self.hud_hint = self._label(
            self.hud_root,
            "左键点击地面移动 · 右键拖动转镜头 · 滚轮缩放",
            (-1.27, -0.93),
            0.028,
            TextNode.ALeft,
            fg=(0.18, 0.16, 0.15, 1.0),
            shadow=(1.0, 0.98, 0.9, 0.85),
        )
        self.hud_menu_button = DirectButton(
            parent=self.hud_root,
            text="菜单",
            text_font=self.font,
            text_fg=(0.18, 0.16, 0.15, 1.0),
            text_scale=0.034,
            frameColor=(0.98, 0.92, 0.80, 0.95),
            frameSize=(-0.13, 0.13, -0.045, 0.045),
            pos=(1.13, 0, 0.89),
            relief=DGG.FLAT,
            command=self.app.pause_game,
        )
        self.hud_menu_button.setTransparency(TransparencyAttrib.MAlpha)

    def update_hud(
        self,
        day: int,
        time_text: str,
        phase: str,
        objective: str,
        location_label: str = "青禾镇",
    ) -> None:
        if hasattr(self, "hud_title"):
            self.hud_title["text"] = f"{location_label} · 第 {day} 天 · {phase}"
            self.hud_time["text"] = time_text
            self.hud_objective["text"] = objective

    def show_hud(self) -> None:
        self._show_only(self.hud_root)

    def hide_all(self) -> None:
        for root in (
            self.title_root,
            self.pause_root,
            self.save_root,
            self.settings_root,
            self.confirm_root,
            self.hud_root,
        ):
            root.hide()
        if hasattr(self, "toast_text"):
            self.toast_text.hide()

    # --------------------------------------------------------------- toast
    def toast(self, text: str, seconds: float = 2.0) -> None:
        self.toast_text["text"] = text
        self.toast_text.show()
        self.app.taskMgr.remove("ui_toast")
        self.app.taskMgr.doMethodLater(seconds, self._hide_toast, "ui_toast")

    def _hide_toast(self, task):
        self.toast_text.hide()
        return task.done
