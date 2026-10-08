# world.execute(me); — Windows EXE

需要 64 位 Windows 10/11。无需安装 Python、FFmpeg，无需另外准备歌曲。

直接双击 `world-execute-mv.exe`，按空格开始播放。

程序作为普通控制台 EXE 运行，由 Windows 的默认终端设置接管双击启动。在将 Windows Terminal 设置为默认终端的系统上，会直接在 Windows Terminal 中打开；程序不调用或指定任何终端路径。推荐窗口至少 128 列 × 44 行。

在已有 Windows Terminal 中，可以直接运行 EXE。参数与 Python 版相同，例如：

```powershell
.\world-execute-mv.exe --start 158.7 --autoplay
```

空格：开始/暂停；左右：后退/前进 5 秒；R：重播；1–5：章节跳转；H：帮助；Q：退出。

音乐、动画、字幕、频谱、Python 运行时都在 EXE 内。启动时 PyInstaller 将资源解包到用户临时目录，正常退出后自动清理；运行无需联网。内嵌音频是 PCM WAV，不会再次有损压缩。

原曲与歌词：Mili《world.execute(me);》。本项目是个人创作与备份，未对原曲、歌词或其他第三方素材授予额外使用许可。
