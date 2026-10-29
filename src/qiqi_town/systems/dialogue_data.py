"""对话数据加载与示例内容。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qiqi_town.paths import data_dir


def load_dialogue_nodes() -> dict[str, Any]:
    root = data_dir() / "dialogue"
    nodes: dict[str, Any] = {}
    if not root.exists():
        return nodes
    for path in sorted(root.glob("*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(raw, dict):
            nodes.update(raw)
    return nodes
