"""第一次进入游戏时的非阻塞鼠标教程。"""

from __future__ import annotations


class Tutorial:
    HINTS = (
        "左键点击地面，淇淇会自己走过去。",
        "按住右键拖动可以转动镜头，滚轮可以拉近拉远。",
        "点击人物、门或发光的物件，淇淇会走过去和它互动。",
        "右上角的“菜单”里可以保存进度、读取存档和写日记。",
    )

    def __init__(self, app) -> None:
        self.app = app
        self.index = 0

    def start(self) -> None:
        self.stop()
        if not self.app.settings.tutorial_hints:
            return
        self.index = 0
        self.app.taskMgr.doMethodLater(1.0, self._show_next, "tutorial_hint")

    def stop(self) -> None:
        self.app.taskMgr.remove("tutorial_hint")

    def _show_next(self, task):
        if self.app.mode not in {"playing"}:
            return task.done
        if self.index >= len(self.HINTS):
            return task.done
        self.app.ui.toast(self.HINTS[self.index], 3.6)
        self.index += 1
        if self.index < len(self.HINTS):
            self.app.taskMgr.doMethodLater(5.2, self._show_next, "tutorial_hint")
        return task.done
