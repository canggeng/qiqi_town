# 契约：对话与事件

## 对话节点字段

| 字段 | 必填 | 说明 |
|---|---|---|
| `id` | 是 | 同一文件内唯一 |
| `speaker` | 是 | 显示名 |
| `text` | 是 | 正文，可含 `\n` |
| `next` | 否 | 下一节点 id；与 `choices` 二选一 |
| `choices` | 否 | 选项数组 |
| `condition` | 否 | 进入节点前的条件 |
| `effects` | 否 | 进入节点时执行 |
| `portrait` | 否 | 表情名：happy/curious/shy/sad/surprised |

## 条件语法

```json
{"all": [{"flag": "met_gu", "value": true}, {"day": 2}]}
{"any": [{"time": "morning"}, {"time": "afternoon"}]}
{"friendship": {"npc": "xiaoman", "gte": 2}}
{"sticker": "sticker_shapes"}
{"location": "library"}
```

叶子条件键：`flag`、`day`、`time`、`location`、`friendship`、`sticker`、`quest_status`。

## 效果

见 `data-model.md` 第 5 节。效果按数组顺序执行；失败的效果记录日志但不中断对话。

## 事件

- 事件在 `location_enter`、`time_phase`、`quest_complete`、`interact` 时评估。
- `once=true` 的事件执行后写入 `flags["event:<id>"]=true`。
- 多个事件同时满足时按 `priority` 降序、`id` 字典序执行，一次最多触发一个，避免叠加弹窗。
- 事件可以只播放对话、只发效果、或两者都有。

## 文本规则

- 正文只允许纯文本 + 换行；不在文本里写 HTML。
- 选项 2–3 个；每个选项必须有 `text` 和 `next` 或 `effects`。
- 不含会导致主线锁死的选项。
- 中文换行由 UI 层按字符宽度处理，数据层不手动插入空格。
