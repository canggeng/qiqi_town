"""测试专用 fixture。

Windows 沙箱下 tempfile/pytest tmpdir 创建的目录可能带受限 ACL，
因此统一使用项目内 .test-tmp 并由 Path.mkdir 创建。
"""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import pytest


@pytest.fixture()
def work_dir() -> Path:
    root = Path(".test-tmp") / f"case_{uuid.uuid4().hex[:10]}"
    root.mkdir(parents=True, exist_ok=False)
    try:
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)
