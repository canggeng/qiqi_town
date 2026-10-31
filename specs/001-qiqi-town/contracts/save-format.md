# 契约：存档格式

## 目录

```
%APPDATA%\QiqiTown\
├─ saves\
│  ├─ slot_01.json
│  ├─ ...
│  ├─ slot_20.json
│  └─ autosave.json
├─ settings.json
└─ logs\
```

不可写时依次回退到 `%LOCALAPPDATA%\QiqiTown\`、用户目录、exe 目录；不得回退到当前工作目录。
首次启动会把旧版写在 cwd/exe 旁的 `QiqiTown\saves` 迁移到稳定目录。
设置页显示实际路径。

## 手动档规则

- 槽位编号 1–20。
- 最多 20 个文件；满后 UI 不允许选择空槽，仓库也拒绝。
- 覆盖已有槽位前写 `.bak`。
- 删除同时删除对应 `.bak`（或保留备份，由实现决定；首版保留 `.bak`）。

## 自动档规则

- 文件名 `autosave.json`，`meta.is_auto=true`。
- 不计入手动档数量。
- 触发点：新的一天开始、主线完成、进入自由模式、探索态安全退出。
- 对话/小游戏中不自动存档。

## 写入协议

1. 序列化为 UTF-8 JSON。
2. 写入同目录 `slot_XX.json.tmp`。
3. 重新读取并校验 `schema_version`、必填字段、类型。
4. 若目标存在，复制为 `slot_XX.json.bak`。
5. `os.replace(tmp, target)`。
6. 任一步失败：删除 tmp，保留原文件，向上返回可读错误。

## 读取协议

1. 读 JSON；解析失败 → `SaveError.CORRUPT`。
2. 校验 `schema_version`；高于当前版本 → `SaveError.VERSION`。
3. `GameState.from_dict`；字段缺失用默认值/回退。
4. 坐标非法 → 使用场景默认出生点，不视为损坏。
5. 损坏文件不得自动删除或覆盖。

## 元数据

`meta` 必须包含：`slot`、`is_auto`、`saved_at`、`playtime_seconds`、`day`、`time_minutes`、`location_label`、`quest_title`。
列表读取只依赖顶层 `meta`，不构造 `GameState`。
