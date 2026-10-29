# 契约：CLI 与调试参数

```powershell
uv run qiqi-town
uv run qiqi-town --smoke-test
uv run qiqi-town --debug
uv run qiqi-town --debug-day 3
uv run qiqi-town --windowed
```

| 参数 | 说明 |
|---|---|
| 无参数 | 正常启动 |
| `--smoke-test` | 构建场景，渲染若干帧，保存截图 `build/smoke.png`，退出 0 |
| `--debug` | 显示日志与帧率 |
| `--debug-day N` | 开发期直接从第 N 天开始（正式发布不暴露入口） |
| `--windowed` | 强制窗口模式（开发时便于截图） |

## 退出码

- `0`：正常退出/冒烟通过。
- `1`：启动或资源加载失败。
- `2`：冒烟测试渲染/截图失败。
- `3`：存档仓库自检失败（仅 `--smoke-test`）。

## 日志

- 开发态输出到控制台。
- 打包态写入 `%APPDATA%\QiqiTown\logs\qiqi_town_YYYYMMDD.log`。
- 日志包含版本、资源根、存档根、异常栈，不包含 API/密钥类数据。
