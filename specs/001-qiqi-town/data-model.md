# 数据模型

## 1. `GameState`

| 字段 | 类型 | 说明 |
|---|---|---|
| `schema_version` | int | 存档结构版本，当前 1 |
| `day` | int | 1–5 |
| `time_minutes` | int | 480–1200（08:00–20:00） |
| `location` | str | `town` / `home` / `kindergarten` / `library` |
| `spawn_id` | str | 场景内出生点 |
| `player` | PlayerState | 地面坐标和朝向 |
| `flags` | dict[str, bool/str/int] | 剧情旗标 |
| `quests` | dict[str, QuestState] | 每日主线状态 |
| `minigames` | dict[str, MinigameState] | 小游戏完成情况 |
| `inventory` | list[str] | 任务物品 |
| `stickers` | list[str] | 已获得贴纸 |
| `friendship` | dict[str, int] | 友谊值 |
| `journal_entries` | list[str] | 已解锁日记 |
| `seen_dialogues` | list[str] | 已见对话（用于重复台词） |
| `playtime_seconds` | float | 游玩时长 |
| `story_complete` | bool | 是否已通关 |

### PlayerState
```json
{"x": 0.0, "y": 0.0, "facing": 0.0}
```
- `x/y` 为 Panda3D 地面坐标；`z` 在场景加载时由地形高度计算。
- `facing` 为度或弧度？**统一为弧度**，0 指向 +Y。
- 加载时坐标必须有限、在场景范围内、落在可走区域；否则回退到出生点。

### QuestState
```json
{"step": 1, "status": "active"}
```
- `status`: `locked` / `active` / `complete`。

### MinigameState
```json
{"completed": true, "best": 3, "plays": 1}
```

## 2. `SaveMeta`

```json
{
  "slot": 3,
  "is_auto": false,
  "saved_at": "2026-10-29T15:40:00+08:00",
  "playtime_seconds": 1234,
  "day": 2,
  "time_minutes": 600,
  "location_label": "青禾图书馆",
  "quest_title": "旧书里的地图"
}
```

## 3. 存档文件

```json
{
  "schema_version": 1,
  "meta": {},
  "state": {}
}
```

- 手动：`slot_01.json` … `slot_20.json`。
- 自动：`autosave.json`。
- 备份：同目录 `*.bak`。
- 临时：`*.tmp`，成功后替换。

## 4. 对话节点

```json
{
  "id": "day1_lin_01",
  "speaker": "林老师",
  "text": "淇淇，欢迎来到幼儿园。",
  "next": "day1_lin_02",
  "condition": {"all": [{"flag": "day1_started", "value": true}]},
  "choices": [
    {
      "text": "把红气球给小满拿一会儿",
      "next": "day1_lin_03a",
      "effects": [
        {"type": "add_friendship", "npc": "xiaoman", "amount": 1},
        {"type": "set_flag", "key": "shared_balloon", "value": true}
      ]
    }
  ]
}
```

- `next` 与 `choices` 二选一；没有 `next` 表示结束。
- `condition` 可省略。
- 支持的环境变量：`day`、`time_minutes`、`location`、`flags`、`friendship`、`stickers`。

## 5. 效果类型

| `type` | 参数 | 说明 |
|---|---|---|
| `set_flag` | `key`, `value` | 写旗标 |
| `add_friendship` | `npc`, `amount` | 友谊值，0–5 |
| `give_sticker` | `id` | 发贴纸，去重 |
| `add_journal` | `id` | 解锁日记 |
| `advance_quest` | `quest`, `step` | 推进任务 |
| `start_minigame` | `id` | 启动小游戏 |
| `play_sfx` | `id` | 音效 |
| `open_screen` | `screen` | 打开 UI |
| `set_balloon` | `visible` | 控制气球显示 |

## 6. 事件定义

```json
{
  "id": "park_ducks_cross",
  "once": true,
  "trigger": {"location": "park", "day": 2, "time": "morning"},
  "condition": {"flag": "met_su", "value": true},
  "dialogue": "park_ducks_01"
}
```

## 7. NPC 定义

```json
{
  "id": "xiaoman",
  "name": "小满",
  "palette": {"dress": "#F28C82", "hair": "#3E3A39"},
  "schedule": [
    {"days": [1, 2, 3, 4], "hours": [8, 12], "location": "kindergarten"},
    {"days": [1, 2, 4], "hours": [12, 17], "location": "playground"}
  ],
  "dialogue": {"default": "xiaoman_idle", "quest": "xiaoman_day4"}
}
```

## 8. 小游戏配置

```json
{
  "id": "day1_shapes",
  "type": "match",
  "day": 1,
  "location": "kindergarten",
  "title": "形状小管家",
  "params": {"rounds": 3, "shapes": ["circle", "square", "triangle"]},
  "sticker": "sticker_shapes"
}
```

## 9. 设置

```json
{
  "master_volume": 0.8,
  "music_volume": 0.6,
  "sfx_volume": 0.8,
  "text_speed": 35,
  "camera_sensitivity": 1.0,
  "window_width": 1600,
  "window_height": 900,
  "fullscreen": false,
  "tutorial_hints": true
}
```
