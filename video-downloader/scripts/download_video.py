#!/usr/bin/env python3
"""
视频下载脚本 - 使用 yt-dlp 下载视频

自动下载完整合并的视频文件，无需额外配置 ffmpeg。

支持的视频网站包括但不限于：
- YouTube
- Bilibili
- 抖音
- 快手
- Vimeo
- 以及 yt-dlp 支持的 1000+ 网站
"""
import sys
import subprocess
import json
import os
from pathlib import Path


def get_ffmpeg_path():
    """获取 ffmpeg 路径，优先使用 moviepy 自带的版本"""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return None


def ensure_dependencies():
    """确保所有依赖已安装"""
    missing = []

    # 检查 yt-dlp
    try:
        subprocess.run(
            ["yt-dlp", "--version"],
            capture_output=True,
            check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        missing.append("yt-dlp")

    # 检查 moviepy（用于 ffmpeg）
    try:
        import imageio_ffmpeg
    except ImportError:
        missing.append("imageio-ffmpeg")

    if missing:
        print(f"正在安装缺失的依赖: {', '.join(missing)}")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-U"] + missing,
                check=True
            )
            print("依赖安装完成！")
            return True
        except subprocess.CalledProcessError as e:
            print(f"依赖安装失败: {e}")
            return False

    return True


def get_video_info(url):
    """获取视频信息"""
    try:
        result = subprocess.run(
            ["yt-dlp", "--dump-json", "--no-playlist", url],
            capture_output=True,
            text=True,
            check=True
        )
        info = json.loads(result.stdout)
        return {
            "title": info.get("title", "未知标题"),
            "duration": info.get("duration"),
            "uploader": info.get("uploader"),
            "view_count": info.get("view_count"),
        }
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return None


def download_video(url, output_dir=".", quality="bestvideo+bestaudio", subtitle=False):
    """
    下载视频（自动合并）

    Args:
        url: 视频 URL
        output_dir: 输出目录
        quality: 视频质量
        subtitle: 是否下载字幕

    Returns:
        下载的文件路径，失败返回 None
    """
    output_path = Path(output_dir).resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    # 获取 ffmpeg 路径
    ffmpeg_path = get_ffmpeg_path()

    # 构建命令
    cmd = [
        "yt-dlp",
        "-f", quality,
        "-o", str(output_path / "%(title)s.%(ext)s"),
        "--merge-output-format", "mp4",  # 确保输出 mp4 格式
        "--no-keep-video",  # 下载后删除临时分片文件
    ]

    # 配置 ffmpeg 路径
    if ffmpeg_path:
        cmd.extend(["--ffmpeg-location", ffmpeg_path])
        print(f"使用 ffmpeg: {ffmpeg_path}")

    if subtitle:
        cmd.extend(["--write-subs", "--sub-lang", "zh-Hans,zh-Hant,en", "--sub-format", "srt"])

    cmd.append(url)

    print(f"开始下载: {url}")
    print(f"输出目录: {output_path}")

    try:
        subprocess.run(cmd, check=True)
        print("\n下载完成！视频已自动合并。")

        # 查找生成的 mp4 文件
        mp4_files = list(output_path.glob("*.mp4"))
        if mp4_files:
            # 返回最新的文件
            latest_file = max(mp4_files, key=lambda p: p.stat().st_mtime)
            return str(latest_file)
        return str(output_path)
    except subprocess.CalledProcessError as e:
        print(f"下载失败: {e}")
        return None


def download_audio_only(url, output_dir="."):
    """仅下载音频（MP3 格式）"""
    output_path = Path(output_dir).resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    # 获取 ffmpeg 路径
    ffmpeg_path = get_ffmpeg_path()

    cmd = [
        "yt-dlp",
        "-x",  # 提取音频
        "--audio-format", "mp3",
        "-o", str(output_path / "%(title)s.%(ext)s"),
        "--audio-quality", "0",  # 最佳质量
    ]

    # 配置 ffmpeg 路径
    if ffmpeg_path:
        cmd.extend(["--ffmpeg-location", ffmpeg_path])

    cmd.append(url)

    print(f"开始下载音频: {url}")

    try:
        subprocess.run(cmd, check=True)
        print("\n音频下载完成！")

        # 查找生成的 mp3 文件
        mp3_files = list(output_path.glob("*.mp3"))
        if mp3_files:
            latest_file = max(mp3_files, key=lambda p: p.stat().st_mtime)
            return str(latest_file)
        return str(output_path)
    except subprocess.CalledProcessError as e:
        print(f"下载失败: {e}")
        return None


def main():
    if len(sys.argv) < 2:
        print("用法: python download_video.py <URL> [选项]")
        print("\n选项:")
        print("  --audio          仅下载音频 (MP3)")
        print("  --subtitle       下载字幕")
        print("  --dir DIR        输出目录 (默认: 当前目录)")
        print("  --quality QUAL   视频质量 (默认: bestvideo+bestaudio)")
        print("\n质量选项:")
        print("  bestvideo+bestaudio  最佳视频+音频 (默认)")
        print("  best                 最佳预合并格式")
        print("  720p                 720p 分辨率")
        print("  480p                 480p 分辨率")
        sys.exit(1)

    url = sys.argv[1]
    output_dir = "."
    quality = "bestvideo+bestaudio"
    audio_only = False
    subtitle = False

    # 解析参数
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--audio":
            audio_only = True
        elif sys.argv[i] == "--subtitle":
            subtitle = True
        elif sys.argv[i] == "--dir" and i + 1 < len(sys.argv):
            output_dir = sys.argv[i + 1]
            i += 1
        elif sys.argv[i] == "--quality" and i + 1 < len(sys.argv):
            quality = sys.argv[i + 1]
            i += 1
        i += 1

    # 检查并安装依赖
    if not ensure_dependencies():
        print("依赖安装失败，请手动安装:")
        print("  pip install -U yt-dlp imageio-ffmpeg")
        sys.exit(1)

    # 获取 yt-dlp 版本
    try:
        result = subprocess.run(
            ["yt-dlp", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"使用 yt-dlp 版本: {result.stdout.strip()}")
    except:
        pass

    # 获取视频信息
    info = get_video_info(url)
    if info:
        print(f"\n视频信息:")
        print(f"  标题: {info['title']}")
        print(f"  上传者: {info['uploader']}")
        if info['duration']:
            mins, secs = divmod(int(info['duration']), 60)
            print(f"  时长: {mins}:{secs:02d}")
        print()

    # 下载
    if audio_only:
        result_path = download_audio_only(url, output_dir)
    else:
        result_path = download_video(url, output_dir, quality, subtitle)

    if result_path:
        print(f"\n文件保存在: {result_path}")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
