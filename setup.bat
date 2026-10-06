@echo off
chcp 65001 >nul
echo ============================================
echo  B站文稿提取工具 - 自动安装
echo ============================================
python -m venv venv
venv\Scripts\python -m pip install -U pip
venv\Scripts\pip install yt-dlp imageio-ffmpeg static-ffmpeg "av==13.1.0" faster-whisper
echo.
echo 安装完成！使用方法：
echo   venv\Scripts\python bili_transcript.py "视频链接"
pause
