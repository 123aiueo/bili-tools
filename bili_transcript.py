# -*- coding: utf-8 -*-
"""B站视频文稿提取：优先抓官方字幕，没有字幕则下载音频用 faster-whisper 转写。

用法:
  python bili_transcript.py <视频URL> [--model small]

输出: 同目录下 <标题>.txt
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# 国内网络默认走 hf-mirror 下载模型；如已在海外网络可设 HF_ENDPOINT 覆盖
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

TOOLS = Path(__file__).parent
YT_DLP = str(TOOLS / "venv" / "Scripts" / "yt-dlp.exe")
PY = str(TOOLS / "venv" / "Scripts" / "python.exe")
OUT = TOOLS / "output"
OUT.mkdir(exist_ok=True)


def run(cmd):
    print("+", " ".join(str(c) for c in cmd[:3]), "...")
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print(r.stderr[-800:])
    return r.returncode == 0


def clean_name(title: str) -> str:
    title = re.sub(r'[\\/:*?"<>|]', "_", title).strip() or "bili_video"
    return title[:80]


def get_info(url: str):
    r = subprocess.run(
        [YT_DLP, "--dump-json", "--no-playlist", url],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print("获取视频信息失败:", r.stderr[-500:])
        sys.exit(1)
    return json.loads(r.stdout)


def try_subtitles(url: str, name: str):
    """尝试下载官方字幕（含自动字幕），转成纯文本。成功返回文本，失败返回 None。"""
    base = OUT / name
    ok = run([YT_DLP, "--skip-download", "--no-playlist",
              "--write-subs", "--write-auto-subs",
              "--sub-langs", "zh-Hans,zh-Hans-CN,zh-CN,zh,en",
              "--sub-format", "srt/vtt/json3/best",
              "-o", str(base), url])
    subs = sorted(glob.glob(str(base) + ".*.*"), key=os.path.getmtime, reverse=True)
    if not ok or not subs:
        return None
    sub_file = subs[0]
    print("找到字幕:", Path(sub_file).name)
    text = Path(sub_file).read_text(encoding="utf-8", errors="replace")
    # 去掉时间轴/标签
    lines = []
    for line in text.splitlines():
        line = re.sub(r"<[^>]+>", "", line).strip()
        if not line or line.isdigit() or "-->" in line or line.startswith(("WEBVTT", "Kind:", "Language:")):
            continue
        lines.append(line)
    return "\n".join(dict.fromkeys(lines))  # 去重且保序


def transcribe(url: str, name: str, model_size: str):
    audio = OUT / (name + ".m4a")
    if not audio.exists():
        if not run([YT_DLP, "--no-playlist", "-f", "ba", "-o", str(OUT / (name + ".m4a")), url]):
            print("音频下载失败")
            sys.exit(1)
    sys.path.insert(0, str(TOOLS / "venv" / "Lib" / "site-packages"))
    from faster_whisper import WhisperModel
    print(f"加载模型 {model_size}（首次会下载，约需几分钟）...")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    print("开始转写...")
    segments, info = model.transcribe(
        str(audio), language="zh", vad_filter=True,
        initial_prompt="以下是普通话的句子，请使用简体中文输出。",
        condition_on_previous_text=False)
    lines = [f"[{s.start:8.1f}s -> {s.end:8.1f}s] {s.text.strip()}" for s in segments]
    audio.unlink(missing_ok=True)
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--model", default="small", help="tiny/base/small/medium，越大越准越慢")
    args = ap.parse_args()

    info = get_info(args.url)
    name = clean_name(info.get("title", "bili_video"))
    print(f"视频: {name}  时长: {info.get('duration')}s")

    text = try_subtitles(args.url, name)
    if text is None:
        print("无官方字幕，改用语音转写...")
        text = transcribe(args.url, name, args.model)

    out_file = OUT / (name + ".txt")
    out_file.write_text(text, encoding="utf-8")
    print(f"\n文稿已保存: {out_file}  ({len(text)} 字符)")


if __name__ == "__main__":
    main()
