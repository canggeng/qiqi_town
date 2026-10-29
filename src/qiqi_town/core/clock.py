"""游戏内时钟：08:00–20:00，1 现实秒 = 1 游戏分钟。"""

from __future__ import annotations

from qiqi_town.config import DAY_END_MINUTE, DAY_START_MINUTE, GAME_MINUTES_PER_SECOND


class GameClock:
    def __init__(
        self,
        day: int = 1,
        minutes: float = DAY_START_MINUTE,
        *,
        paused: bool = False,
    ) -> None:
        self.day = max(1, min(5, int(day)))
        self.minutes = max(float(DAY_START_MINUTE), min(float(DAY_END_MINUTE), float(minutes)))
        self.paused = paused

    def tick(self, dt: float) -> None:
        if self.paused or dt <= 0:
            return
        if self.minutes >= DAY_END_MINUTE:
            self.minutes = float(DAY_END_MINUTE)
            return
        self.minutes = min(
            float(DAY_END_MINUTE),
            self.minutes + float(dt) * GAME_MINUTES_PER_SECOND,
        )

    @property
    def minute_int(self) -> int:
        return int(self.minutes)

    @property
    def phase(self) -> str:
        if self.minutes < 12 * 60:
            return "morning"
        if self.minutes < 17 * 60:
            return "afternoon"
        return "dusk"

    @property
    def phase_label(self) -> str:
        return {"morning": "上午", "afternoon": "下午", "dusk": "黄昏"}[self.phase]

    @property
    def at_end(self) -> bool:
        return self.minutes >= DAY_END_MINUTE

    @property
    def display_time(self) -> str:
        total = self.minute_int
        return f"{total // 60:02d}:{total % 60:02d}"

    def set_minutes(self, minutes: float) -> None:
        self.minutes = max(float(DAY_START_MINUTE), min(float(DAY_END_MINUTE), float(minutes)))

    def advance_day(self) -> bool:
        """进入下一天；第 5 天不能再睡。返回是否成功。"""
        if self.day >= 5:
            return False
        self.day += 1
        self.minutes = float(DAY_START_MINUTE)
        return True

    def sync_from_state(self, day: int, time_minutes: int) -> None:
        self.day = max(1, min(5, int(day)))
        self.set_minutes(time_minutes)

    def to_state_values(self) -> tuple[int, int]:
        return self.day, self.minute_int
