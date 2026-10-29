"""命令行入口。"""

from __future__ import annotations

import argparse
import multiprocessing
import os
import sys
import traceback
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="qiqi-town", description="淇淇的小镇")
    parser.add_argument("--smoke-test", action="store_true", help="渲染若干帧、截图并退出")
    parser.add_argument("--debug", action="store_true", help="显示调试信息/帧率")
    parser.add_argument("--debug-day", type=int, default=1, help="开发期直接进入指定天")
    parser.add_argument("--windowed", action="store_true", help="强制窗口模式")
    return parser


def _startup_log_file():
    base = Path(
        os.environ.get("QIQI_TOWN_DATA_DIR")
        or os.environ.get("APPDATA")
        or (Path.home() / "QiqiTown")
    )
    try:
        base.mkdir(parents=True, exist_ok=True)
        return open(base / "startup.log", "a", encoding="utf-8", buffering=1)
    except OSError:
        return None


def main(argv: list[str] | None = None) -> int:
    multiprocessing.freeze_support()
    args = build_parser().parse_args(argv)
    if args.smoke_test:
        os.environ.setdefault("QIQI_TOWN_DATA_DIR", str(Path.cwd() / ".smoke-data"))

    log = _startup_log_file()
    if log is not None:
        if sys.stdout is None:
            sys.stdout = log
        if sys.stderr is None:
            sys.stderr = log
        print(f"\n=== QiqiTown start {args} ===", flush=True)

    try:
        from qiqi_town.app import QiqiTownApp, configure_prc

        configure_prc(args)
        app = QiqiTownApp(args)
        if args.debug:
            app.setFrameRateMeter(True)
        if args.smoke_test:
            return app.run_smoke_test()
        app.run()
        return 0
    except BaseException:  # noqa: BLE001
        traceback.print_exc()
        if log is not None:
            traceback.print_exc(file=log)
            log.flush()
        return 1


if __name__ == "__main__":
    sys.exit(main())
