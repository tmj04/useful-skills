#!/usr/bin/env python3
"""
分析输入素材脚本 - 扫描文件或文件夹，识别图片和文本内容。

用途:
    python scripts/analyze_input.py "/path/to/materials"

输出 JSON 格式：
{
  "input_path": "...",
  "output_path": ".../output",
  "images": [{"path": "...", "width": N, "height": N, "format": "..."}],
  "texts": [{"path": "...", "content": "...", "char_count": N}],
  "summary": "找到 X 张图片、Y 个文本文件"
}
"""

import argparse
import json
import sys
from pathlib import Path

try:
    from PIL import Image as PILImage
except ImportError:
    print("Error: Pillow 未安装，请先运行：pip install Pillow", file=sys.stderr)
    sys.exit(1)

try:
    from docx import Document
except ImportError:
    Document = None


SUPPORTED_IMAGES = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'}
SUPPORTED_TEXTS = {'.txt', '.md', '.docx'}


def get_image_info(file_path: Path) -> dict | None:
    """
    获取图片文件的元信息（尺寸、格式、大小）。

    参数:
        file_path: 图片文件路径

    返回:
        dict: 包含 path, width, height, format, size_kb 的字典，失败返回 None
    """
    try:
        with PILImage.open(file_path) as img:
            width, height = img.size
            file_size_kb = round(file_path.stat().st_size / 1024, 2)
            return {
                "path": str(file_path),
                "width": width,
                "height": height,
                "format": img.format or "Unknown",
                "size_kb": file_size_kb
            }
    except Exception as e:
        print(f"Warning: 无法读取图片 '{file_path}': {e}", file=sys.stderr)
        return None


def extract_text_content(file_path: Path) -> str | None:
    """
    从文本文件提取内容（支持 txt/md/docx）。

    参数:
        file_path: 文本文件路径

    返回:
        str: 文件内容，失败返回 None
    """
    suffix = file_path.suffix.lower()

    if suffix in {'.txt', '.md'}:
        try:
            return file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            try:
                return file_path.read_text(encoding='gbk')
            except Exception as e:
                print(f"Warning: 无法读取文本 '{file_path}': {e}", file=sys.stderr)
                return None

    elif suffix == '.docx':
        if Document is None:
            print(f"Warning: python-docx 未安装，无法读取 docx 文件 '{file_path}'", file=sys.stderr)
            return None
        try:
            doc = Document(file_path)
            return '\n'.join(paragraph.text for paragraph in doc.paragraphs)
        except Exception as e:
            print(f"Warning: 无法读取 docx '{file_path}': {e}", file=sys.stderr)
            return None

    return None


def scan_path(input_path: str) -> dict:
    """
    扫描指定路径，分类整理所有图片和文本素材。

    参数:
        input_path: 文件或文件夹路径

    返回:
        dict: 包含 input_path, output_path, images, texts, summary 的结果
    """
    input_p = Path(input_path)

    if not input_p.exists():
        raise FileNotFoundError(f"路径不存在：{input_path}")

    # 确定输出目录
    if input_p.is_file():
        output_dir = input_p.parent / "output"
    else:
        output_dir = input_p / "output"

    output_dir.mkdir(parents=True, exist_ok=True)

    images = []
    texts = []

    # 扫描文件
    if input_p.is_file():
        files = [input_p]
    else:
        files = list(input_p.rglob('*'))

    for file_path in files:
        if not file_path.is_file():
            continue

        suffix = file_path.suffix.lower()

        if suffix in SUPPORTED_IMAGES:
            info = get_image_info(file_path)
            if info:
                images.append(info)

        elif suffix in SUPPORTED_TEXTS:
            content = extract_text_content(file_path)
            if content:
                texts.append({
                    "path": str(file_path),
                    "content": content,
                    "char_count": len(content)
                })

    summary = f"共找到 {len(images)} 张图片、{len(texts)} 个文本文件"

    return {
        "input_path": str(input_p),
        "output_path": str(output_dir),
        "images": images,
        "texts": texts,
        "summary": summary
    }


def main():
    parser = argparse.ArgumentParser(
        description="扫描文件或文件夹，识别图片和文本素材"
    )
    parser.add_argument(
        "input_path",
        help="要扫描的文件或文件夹路径"
    )

    args = parser.parse_args()

    try:
        result = scan_path(args.input_path)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
