from qiqi_town.core.conditions import EffectContext
from qiqi_town.core.state import GameState
from qiqi_town.systems.dialogue import DialogueRunner

RAW = {
    "start": {
        "speaker": "林老师",
        "text": "你好",
        "effects": [{"type": "set_flag", "key": "met", "value": True}],
        "next": "choose",
    },
    "choose": {
        "speaker": "林老师",
        "text": "选一个",
        "choices": [
            {
                "text": "分享",
                "next": "end",
                "effects": [
                    {"type": "add_friendship", "npc": "lin", "amount": 1},
                    {"type": "give_sticker", "id": "sticker_share"},
                ],
            },
            {"text": "不分享", "next": "end"},
        ],
    },
    "end": {"speaker": "林老师", "text": "好"},
}


def test_dialogue_flow_and_effects() -> None:
    state = GameState.new_game()
    runner = DialogueRunner.from_data(RAW, state)
    assert runner.start("start")
    assert runner.current is not None
    assert runner.current.id == "start"
    assert state.flags["met"] is True
    assert runner.advance()
    assert runner.current is not None
    assert runner.current.id == "choose"
    assert runner.waiting_for_choice
    assert not runner.advance()
    assert runner.choose(0)
    assert state.friendship["lin"] == 1
    assert state.stickers == ["sticker_share"]
    assert runner.current is not None
    assert runner.current.id == "end"
    assert not runner.advance()
    assert runner.finished


def test_dialogue_condition_and_unknown_node() -> None:
    state = GameState.new_game()
    raw = {
        "only_day2": {
            "speaker": "?",
            "text": "hidden",
            "condition": {"day": 2},
        },
        "end": {"speaker": "?", "text": "end"},
    }
    runner = DialogueRunner.from_data(raw, state)
    assert not runner.start("only_day2")  # 条件不满足且无 fallback：直接结束
    assert runner.finished
    assert not runner.start("missing")


def test_effect_context_hook() -> None:
    state = GameState.new_game()
    seen: list[str] = []
    raw = {
        "start": {
            "speaker": "?",
            "text": "hi",
            "effects": [{"type": "play_sfx", "id": "chime"}],
        }
    }
    runner = DialogueRunner.from_data(
        raw, state, effect_context=EffectContext(hooks={"play_sfx": lambda e: seen.append(e["id"])})
    )
    assert runner.start("start")
    assert seen == ["chime"]
