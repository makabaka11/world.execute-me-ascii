# world.execute(me); —ascii (Windows fork)

![world.execute(me);](docs/images/mv-cover.png)

Mili《world.execute(me);》的中英双语终端字符动画。本 fork **仅提供 Windows 版本**，不发布上游的 macOS 版本。推荐在 Windows Terminal 中播放，窗口至少 64 列 × 24 行，128 列 × 44 行及以上效果更好。

## 下载与运行

从 [Releases](https://github.com/makabaka11/world.execute-me-ascii/releases) 下载以下任一文件。两者都内嵌音乐、字幕、动画和频谱，无需另外准备音频或安装 FFmpeg。

| 文件 | 运行要求 | 启动方式 |
| --- | --- | --- |
| `world-execute-mv.pyz` | Windows 10/11、Python 3.9+ | 在 Windows Terminal 中运行 `python world-execute-mv.pyz` |
| `world-execute-mv.exe` | 64 位 Windows 10/11 | 双击运行，使用系统默认终端；无需安装 Python。详见 [EXE 说明](docs/windows-exe.md) |

两种文件都可添加参数，例如 `--start 158.7 --autoplay` 从 2:38.7 开始播放。EXE 是普通控制台程序，不调用或指定终端路径；当 Windows Terminal 是系统默认终端时，双击便由它启动。按空格开始播放。内嵌资源在运行时解包到用户临时目录，正常退出后清理。

## 操作

| 按键 | 功能 |
| --- | --- |
| 空格 | 开始／暂停 |
| 左／右 | 后退／前进 5 秒 |
| R | 从头播放 |
| Q | 退出 |
| H | 显示全部帮助 |
| 1–5 | 跳转章节 |

## 从源码运行与构建

仓库包含 CI 构建所需的 `media/song.mp3`。源码运行与构建首次需要 FFmpeg 在 PATH 中；程序将 MP3 解码成 16 位 PCM WAV，按音频内容缓存到 `.build/pcm/`。更换歌曲会生成新缓存。画面以 Windows 音频设备已播放的采样数同步，暂停和跳转跟随音频时间。

在 Windows Terminal 中运行源码：

```powershell
python -X utf8 player.py
```

构建两个与 Release 相同的文件（构建机器需要 64 位 Windows、Python 3.9+、FFmpeg 和 PyInstaller）：

```powershell
python -m pip install -r tools/requirements-exe.txt
python tools/build_bundle.py
python tools/build_exe.py
```

产物位于 `dist/world-execute-mv.pyz` 与 `dist/world-execute-mv.exe`。推送 `v*` 标签会在 GitHub Actions 的 Windows runner 上构建、验证并将这两个文件上传到 Release；Release 说明读取仓库根目录的 `CHANGE_LOG.md`。

本地验证：

```powershell
python -X utf8 -m unittest discover -s tests -v
# 增加真实音频设备测试（使用静音 PCM，验证采样时钟、暂停、跳转、结束和重播）
$env:MV_TEST_AUDIO = '1'
python -X utf8 tests/test_windows.py
```

## 创作提示词

整理了这支 MV 从初始构想到逐段调整的 **25 轮提示词**，以及一份方便复用的合并版。

- **[在线阅读创作过程](docs/prompts/creation-prompts.md)**：按轮次查看需求、场景位置与修改方向，文内目录可直接跳转。
- **[直接查看合并提示词](docs/prompts/creation-prompts.md#combined-prompt)**：适合整体阅读和复制使用。
- **[纯文本版](docs/prompts/creation-prompts.txt)**：方便保存到本地或在文本编辑器中打开。

## 来源

本仓库是 [yym8224961/world.execute-me-ascii](https://github.com/yym8224961/world.execute-me-ascii) 的 Windows 专用 fork，保留了原创的动画、字幕和频谱数据，并使用 Windows 原生音频播放。两种 Release 产物由本 fork 的 Windows CI 生成。

原曲与歌词：Mili《world.execute(me);》。本项目是个人创作与备份，未对原曲、歌词或其他第三方素材授予额外使用许可。
