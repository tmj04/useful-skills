---
name: video-downloader
description: 视频下载工具，使用 yt-dlp 从 YouTube、Bilibili、抖音等 1000+ 网站下载视频。自动合并视频和音频，输出完整 MP4 文件。当用户请求下载视频、保存视频、或者提供视频链接时使用此 skill。
license: Apache 2.0
---

# Video Downloader

使用 yt-dlp 从各种视频网站下载视频、音频和字幕。**自动处理视频合并，无需额外配置。**

## 特性

- **自动合并** - 视频和音频自动合并为完整 MP4 文件
- **自动安装依赖** - 首次使用自动安装 yt-dlp 和 ffmpeg
- **多平台支持** - YouTube、Bilibili、抖音、快手、Vimeo 等 1000+ 网站

## 支持的网站

YouTube、Bilibili、抖音、快手、Vimeo、Twitter、Instagram 以及 yt-dlp 支持的 1000+ 网站。

## 快速开始

下载视频到当前目录：

```bash
python scripts/download_video.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

## 工作流程

1. **检查环境** - 自动检测并安装 yt-dlp 和 imageio-ffmpeg（含 ffmpeg）
2. **获取信息** - 显示视频标题、时长等信息
3. **下载并合并** - 自动下载视频和音频，合并输出 MP4 文件
4. **清理临时文件** - 自动删除分片文件

## 使用方式

### 下载视频（默认）

```bash
python scripts/download_video.py "<视频链接>"
```

输出：完整的 MP4 文件（视频+音频已合并）

### 仅下载音频（MP3）

```bash
python scripts/download_video.py "<视频链接>" --audio
```

### 下载带字幕的视频

```bash
python scripts/download_video.py "<视频链接>" --subtitle
```

### 指定输出目录

```bash
python scripts/download_video.py "<视频链接>" --dir "D:\Videos"
```

### 指定视频质量

```bash
python scripts/download_video.py "<视频链接>" --quality "720p"
```

质量选项：
- `bestvideo+bestaudio` - 最佳视频+音频（默认）
- `best` - 最佳预合并格式
- `720p` / `480p` / `360p` - 特定分辨率

## 常见问题

**Q: 视频下载后是分开的文件怎么办？**
A: 新版本脚本已自动处理合并，输出完整的 MP4 文件。如果仍有问题，请更新脚本。

**Q: 下载失败怎么办？**
A: 某些网站可能需要更新 yt-dlp，运行：`pip install -U yt-dlp`

**Q: Bilibili 下载失败？**
A: 部分 Bilibili 视频需要大会员权限。可尝试使用 cookies：
```bash
yt-dlp --cookies-from-browser chrome "<视频链接>"
```

**Q: 如何下载播放列表？**
A: 当前脚本仅下载单个视频。如需播放列表，可直接使用 yt-dlp：
```bash
yt-dlp -o "%(playlist_index)s-%(title)s.%(ext)s" "<播放列表链接>"
```

## 输出示例

```
正在安装缺失的依赖: imageio-ffmpeg
依赖安装完成！
使用 yt-dlp 版本: 2025.12.8
使用 ffmpeg: D:\someenv\anaconda3\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe

视频信息:
  标题: 示例视频
  上传者: 某UP主
  时长: 3:45

开始下载: https://www.bilibili.com/video/BV...
输出目录: E:\Videos
[download] 100% of 15.00MiB
[ffmpeg] Merging formats into "示例视频.mp4"

下载完成！视频已自动合并。

文件保存在: E:\Videos\示例视频.mp4
```
