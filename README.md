# B站视频文稿提取工具 (bili-tools)

给一个 B 站视频链接，自动提取文字稿：**优先下载官方字幕，没有字幕则下载音频并用 faster-whisper 语音转写**（中文，默认输出简体中文）。

## 环境要求

- Windows + Python 3.10+（无需单独安装 ffmpeg，由 pip 包内置提供）

## 安装

双击运行 `setup.bat`，或手动执行：

```bat
python -m venv venv
venv\Scripts\pip install -U pip yt-dlp imageio-ffmpeg static-ffmpeg faster-whisper
```

> 首次语音转写会自动下载模型（默认 `small`，国内默认走 hf-mirror 镜像，约 500MB）。
> 追求更快可用 `--model tiny` / `base`；追求更准可用 `--model medium`。

## 使用

```bat
venv\Scripts\python bili_transcript.py "https://www.bilibili.com/video/BVxxxxxx"
```

输出保存在 `output\` 目录下，文件名为视频标题。

## 参数

| 参数 | 说明 |
|---|---|
| `--model` | 转写模型：tiny / base / small（默认）/ medium / large-v3，越大越准越慢 |

## 工作原理

1. `yt-dlp` 获取视频信息
2. 尝试下载官方字幕（含 CC 自动字幕），成功则整理为纯文本
3. 无字幕时下载最佳音轨，用 faster-whisper（CPU int8）转写，带 VAD 过滤静音
4. 输出带时间戳的文稿 txt，可直接交给 AI（如 Kimi）做提炼总结

## 备注

- 需要配合 Watt Toolkit 等加速器访问 GitHub / HuggingFace 时，脚本已默认使用 `https://hf-mirror.com` 镜像下载模型
- PyAV 请使用 13.x（`av==13.1.0`），14 及以上版本与 faster-whisper 存在兼容问题
