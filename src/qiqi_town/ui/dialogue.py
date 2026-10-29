"""对话界面：底部对话框、逐字显示、选项。"""

from __future__ import annotations

from direct.gui import DirectGuiGlobals as DGG
from direct.gui.DirectGui import DirectButton, DirectFrame
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode, TransparencyAttrib

from qiqi_town.systems.dialogue import DialogueRunner


def wrap_cjk(text: str, max_chars: int = 34) -> str:
    """轻量中文换行：按字符数切分，保留原有换行。"""
    lines: list[str] = []
    for paragraph in text.replace("\r", "").split("\n"):
        if not paragraph:
            lines.append("")
            continue
        current = ""
        for char in paragraph:
            current += char
            if len(current) >= max_chars:
                lines.append(current)
                current = ""
        if current:
            lines.append(current)
    return "\n".join(lines)


class DialogueUi:
    def __init__(self, app) -> None:
        self.app = app
        self.font = app.font
        self.root = app.aspect2d.attachNewNode("dialogue_ui")
        self.root.hide()
        self.panel = DirectFrame(
            parent=self.root,
            frameColor=(0.99, 0.96, 0.88, 0.97),
            frameSize=(-1.24, 1.24, -0.98, -0.17),
            pos=(0, 0, 0),
            relief=DGG.FLAT,
        )
        self.panel.setTransparency(TransparencyAttrib.MAlpha)
        self.speaker_text = OnscreenText(
            parent=self.root,
            text="",
            font=self.font,
            pos=(-1.14, -0.28),
            scale=0.045,
            align=TextNode.ALeft,
            fg=(0.82, 0.36, 0.30, 1.0),
            shadow=(1.0, 1.0, 1.0, 0.0),
            mayChange=True,
        )
        self.body_text = OnscreenText(
            parent=self.root,
            text="",
            font=self.font,
            pos=(-1.14, -0.40),
            scale=0.038,
            align=TextNode.ALeft,
            fg=(0.18, 0.16, 0.15, 1.0),
            shadow=(1.0, 1.0, 1.0, 0.0),
            mayChange=True,
        )
        self.continue_text = OnscreenText(
            parent=self.root,
            text="点击继续",
            font=self.font,
            pos=(1.12, -0.91),
            scale=0.026,
            align=TextNode.ARight,
            fg=(0.45, 0.40, 0.34, 0.9),
            mayChange=True,
        )
        self.choice_buttons: list[DirectButton] = []
        self.runner: DialogueRunner | None = None
        self._full_text = ""
        self._shown_chars = 0.0
        self._choice_ready = False

    def show(self, runner: DialogueRunner) -> None:
        self.runner = runner
        self.root.show()
        self._display_current()

    def hide(self) -> None:
        self.root.hide()
        self.runner = None
        self._clear_choices()

    def update(self, dt: float) -> None:
        if self.runner is None or self._choice_ready:
            return
        if self._shown_chars < len(self._full_text):
            self._shown_chars = min(
                len(self._full_text),
                self._shown_chars + self.app.settings.text_speed * dt,
            )
            self.body_text["text"] = self._full_text[: int(self._shown_chars)]
            if self._shown_chars >= len(self._full_text):
                self._on_typing_done()
        if self._shown_chars < len(self._full_text) or self._choice_ready:
            self.continue_text.hide()
        else:
            self.continue_text.show()

    def _display_current(self) -> None:
        if self.runner is None or self.runner.current is None:
            return
        node = self.runner.current
        self.speaker_text["text"] = node.speaker
        self._full_text = wrap_cjk(node.text)
        self._shown_chars = 0.0
        self.body_text["text"] = ""
        self._choice_ready = False
        self.continue_text.show()
        self._clear_choices()
        # 有选项时，正文显示完后显示选项。
        if node.choices:
            self._show_choices_when_ready = True
        else:
            self._show_choices_when_ready = False

    def _on_typing_done(self) -> None:
        self.continue_text.show()
        if self.runner is not None and self.runner.current and self.runner.current.choices:
            self._choice_ready = True
            self._create_choices()

    def _create_choices(self) -> None:
        self._clear_choices()
        if self.runner is None or self.runner.current is None:
            return
        choices = self.runner.current.choices or []
        y = -0.61
        for index, choice in enumerate(choices[:3]):
            button = DirectButton(
                parent=self.root,
                text=choice.text,
                text_font=self.font,
                text_fg=(0.22, 0.19, 0.16, 1.0),
                text_scale=0.03,
                text_align=TextNode.ALeft,
                text_pos=(-0.68, 0.0),
                frameColor=(0.94, 0.84, 0.68, 0.97),
                frameSize=(-0.72, 0.72, -0.035, 0.035),
                pos=(0.42, 0, y),
                relief=DGG.FLAT,
                command=self._choose,
                extraArgs=[index],
            )
            button.setTransparency(TransparencyAttrib.MAlpha)
            self.choice_buttons.append(button)
            y -= 0.095
        self.continue_text.hide()

    def _clear_choices(self) -> None:
        for button in self.choice_buttons:
            button.destroy()
        self.choice_buttons.clear()

    def _choose(self, index: int) -> None:
        if self.runner is None:
            return
        still_running = self.runner.choose(index)
        if still_running:
            self._display_current()
        else:
            self.app.end_dialogue()

    def handle_click(self) -> None:
        if self.runner is None or self._choice_ready:
            return
        if self._shown_chars < len(self._full_text):
            self._shown_chars = float(len(self._full_text))
            self.body_text["text"] = self._full_text
            self._on_typing_done()
            return
        still_running = self.runner.advance()
        if still_running:
            self._display_current()
        else:
            self.app.end_dialogue()
