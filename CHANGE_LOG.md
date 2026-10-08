# v1.0 — Windows 专用版

本 fork 首次发布 Windows 版《world.execute(me);》终端字符动画。保留中英双语字幕、章节跳转、频谱与原曲同步播放，画面由 Windows 音频设备的采样时钟驱动。

- `world-execute-mv.pyz`：内嵌音乐、字幕和动画；需 Windows 10/11 与 Python 3.9 或更新版本，在终端运行 `python world-execute-mv.pyz`。
- `world-execute-mv.exe`：PyInstaller 打包的 64 位 Windows 独立程序，内置 Python 运行时与音乐，双击即可由系统默认终端打开，无需另装 Python 或 FFmpeg。

推荐 Windows Terminal，窗口至少 64 列 × 24 行，128 列 × 44 行及以上效果更好。按空格开始或暂停，左右键跳转 5 秒，`R` 重播，`1`–`5` 跳转章节，`H` 显示帮助，`Q` 退出。

此 fork 仅提供 Windows 构建，不提供上游的 macOS 版本。原曲与歌词：Mili《world.execute(me);》。本项目是个人创作与备份，未对原曲、歌词或其他第三方素材授予额外使用许可。
