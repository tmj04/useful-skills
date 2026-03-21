#!/usr/bin/env python3
"""
小红书封面/内容图片生成脚本 - 支持多家图片生成供应商。

用途:
    # 使用 Gemini 生成封面
    python scripts/generate_image.py \
        --provider gemini \
        --prompt "小红书风格封面图描述" \
        --input-images photo.jpg \
        --aspect-ratio 3:4 \
        --output output/01_cover.png

    # 使用百炼生成内容卡片
    python scripts/generate_image.py \
        --provider dashscope \
        --prompt "内容卡片描述" \
        --aspect-ratio 3:4 \
        --output output/02_card.png

支持的供应商:
    - gemini: Google Gemini 图像生成 (GEMINI_API_KEY)
    - dashscope: 百炼/通义万相 (DASHSCOPE_API_KEY)
"""

import argparse
import base64
import io
import os
import sys
import urllib.request
from abc import ABC, abstractmethod
from pathlib import Path

try:
    from PIL import Image as PILImage
except ImportError:
    print("Error: Pillow 未安装，请先运行：pip install Pillow", file=sys.stderr)
    sys.exit(1)


# 尺寸配置 (宽，高)
ASPECT_RATIOS = {
    "3:4": (1080, 1440),   # 小红书竖版最佳
    "1:1": (1080, 1080),   # 方形
}

# DashScope 支持的标准尺寸
DASHSCOPE_SIZES = {
    "3:4": "1024x768",
    "1:1": "1024x1024",
}


class ImageProvider(ABC):
    """图片生成供应商抽象基类"""

    @abstractmethod
    def generate(self, prompt: str, input_images: list[Path],
                 width: int, height: int) -> bytes:
        """
        生成图片。

        参数:
            prompt: 图片生成提示词
            input_images: 输入图片路径列表（可选，用于图片编辑）
            width: 输出宽度
            height: 输出高度

        返回:
            bytes: 生成的图片数据（PNG 格式）
        """
        pass


class GeminiProvider(ImageProvider):
    """Google Gemini 图片生成供应商"""

    def __init__(self, api_key: str | None):
        """
        初始化 Gemini 供应商。

        参数:
            api_key: Gemini API key，None 则使用环境变量 GEMINI_API_KEY
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Gemini API key 未设置。\n"
                "请通过以下方式提供：\n"
                "  1. 设置环境变量 GEMINI_API_KEY\n"
                "  2. 或传递 --api-key 参数"
            )

        # 延迟导入避免无 key 时出错
        from google import genai
        self.client = genai.Client(api_key=self.api_key)

    def generate(self, prompt: str, input_images: list[Path],
                 width: int, height: int) -> bytes:
        """
        使用 Gemini 生成图片。

        参数:
            prompt: 图片生成提示词
            input_images: 输入图片路径列表
            width: 输出宽度
            height: 输出高度

        返回:
            bytes: PNG 格式的图片数据
        """
        from google.genai import types

        # 构建请求内容（图片 + 文本）
        contents = []

        for img_path in input_images:
            # 读取图片为 bytes
            img_bytes = img_path.read_bytes()
            contents.append(img_bytes)

        # 添加文本提示
        contents.append(prompt)

        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-preview-image-generation",
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"],
                )
            )

            # 从响应中提取图片
            for part in response.parts:
                if part.inline_data is not None:
                    image_data = part.inline_data.data
                    if isinstance(image_data, str):
                        image_data = base64.b64decode(image_data)

                    # 调整为目标尺寸
                    img = PILImage.open(io.BytesIO(image_data))
                    img = img.resize((width, height), PILImage.LANCZOS)

                    # 转为 bytes 返回
                    buffer = io.BytesIO()
                    img.save(buffer, "PNG")
                    return buffer.getvalue()

            raise RuntimeError("响应中未找到图片数据")

        except Exception as e:
            raise RuntimeError(f"Gemini 图片生成失败：{e}")


class DashScopeProvider(ImageProvider):
    """百炼/通义万相图片生成供应商"""

    def __init__(self, api_key: str | None):
        """
        初始化 DashScope 供应商。

        参数:
            api_key: DashScope API key，None 则使用环境变量 DASHSCOPE_API_KEY
        """
        self.api_key = api_key or os.environ.get("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "DashScope API key 未设置。\n"
                "请通过以下方式提供：\n"
                "  1. 设置环境变量 DASHSCOPE_API_KEY\n"
                "  2. 或传递 --api-key 参数"
            )

        # 延迟导入
        import dashscope
        dashscope.api_key = self.api_key

    def generate(self, prompt: str, input_images: list[Path],
                 width: int, height: int) -> bytes:
        """
        使用通义万相生成图片（文生图模式）。

        注意：当前版本仅支持文生图。如需图片编辑功能，请使用 Gemini 供应商。

        参数:
            prompt: 图片生成提示词
            input_images: 输入图片路径列表（此模式下会被忽略）
            width: 输出宽度
            height: 输出高度

        返回:
            bytes: PNG 格式的图片数据
        """
        import time
        from dashscope import ImageSynthesis

        size_str = DASHSCOPE_SIZES.get(f"{width}:{height}", "1024x1024")

        # 如果有输入图片，给出警告
        if input_images:
            print("Warning: DashScope 当前版本仅支持文生图，输入图片将被忽略。", file=sys.stderr)
            print("如需图片编辑功能，请使用 --provider gemini", file=sys.stderr)

        try:
            # 文生图模式：wanx2.1-t2i-turbo
            task = ImageSynthesis.async_call(
                model="wanx2.1-t2i-turbo",
                prompt=prompt,
                size=size_str,
            )

            # 轮询等待完成
            while True:
                status = ImageSynthesis.wait(task)
                if status.status == 'SUCCEEDED':
                    break
                elif status.status == 'FAILED':
                    raise RuntimeError(f"任务失败：{status.output}")
                time.sleep(2)

            # 下载结果
            result_url = status.output['results'][0]['url']
            return self._download_image(result_url, width, height)

        except Exception as e:
            raise RuntimeError(f"DashScope 图片生成失败：{e}")

    def _download_image(self, url: str, width: int, height: int) -> bytes:
        """下载图片并调整尺寸"""
        with urllib.request.urlopen(url) as response:
            image_bytes = response.read()

        # 调整为目标尺寸
        img = PILImage.open(io.BytesIO(image_bytes))
        img = img.resize((width, height), PILImage.LANCZOS)

        # 转为 bytes 返回
        buffer = io.BytesIO()
        img.save(buffer, "PNG")
        return buffer.getvalue()


def get_provider(name: str, api_key: str | None = None) -> ImageProvider:
    """
    获取图片生成供应商实例（工厂函数）。

    参数:
        name: 供应商名称（gemini 或 dashscope）
        api_key: 可选的 API key

    返回:
        ImageProvider: 对应的供应商实例
    """
    providers = {
        "gemini": GeminiProvider,
        "dashscope": DashScopeProvider,
    }

    if name not in providers:
        raise ValueError(f"不支持的供应商 '{name}'，支持的有：{', '.join(providers.keys())}")

    return providers[name](api_key)


def load_input_images(paths: list[str] | None) -> list[Path]:
    """
    加载并验证输入图片。

    参数:
        paths: 图片路径列表

    返回:
        list[Path]: 有效的图片路径列表
    """
    if not paths:
        return []

    valid_images = []
    for path_str in paths:
        p = Path(path_str)
        if not p.exists():
            print(f"Warning: 图片不存在：{path_str}", file=sys.stderr)
            continue

        try:
            # 验证是否为有效图片
            with PILImage.open(p) as img:
                img.verify()
            valid_images.append(p)
            print(f"✓ 加载图片：{path_str}")
        except Exception as e:
            print(f"Warning: 无效图片 '{path_str}': {e}", file=sys.stderr)
            continue

    if not valid_images:
        print("Info: 没有有效的输入图片，将使用纯文本生成", file=sys.stderr)

    return valid_images


def main():
    parser = argparse.ArgumentParser(
        description="使用 AI 生成小红书风格图片（封面/内容卡片等）"
    )
    parser.add_argument(
        "--provider", "-p",
        required=True,
        choices=["gemini", "dashscope"],
        help="图片生成供应商：gemini 或 dashscope"
    )
    parser.add_argument(
        "--type", "-t",
        choices=["cover", "card", "enhance"],
        default="cover",
        help="图片类型：cover(封面)/card(内容卡片)/enhance(素材美化)，默认 cover"
    )
    parser.add_argument(
        "--prompt",
        required=True,
        help="完整的图片生成提示词"
    )
    parser.add_argument(
        "--input-images", "-i",
        nargs="*",
        dest="input_images",
        help="输入素材图片路径（可选，多个图片用空格分隔）"
    )
    parser.add_argument(
        "--aspect-ratio",
        choices=["3:4", "1:1"],
        default="3:4",
        help="输出宽高比：3:4(竖版，默认) 或 1:1(方形)"
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="输出文件路径"
    )
    parser.add_argument(
        "--api-key", "-k",
        help="API key（覆盖环境变量）"
    )

    args = parser.parse_args()

    # 解析尺寸
    width, height = ASPECT_RATIOS[args.aspect_ratio]

    try:
        # 加载输入图片
        input_imgs = load_input_images(args.input_images)

        # 获取供应商
        provider = get_provider(args.provider, args.api_key)

        print(f"\n{'='*50}")
        print(f"开始生成图片...")
        print(f"  供应商：{args.provider}")
        print(f"  类型：{args.type}")
        print(f"  尺寸：{width}x{height}")
        print(f"  输入图片：{len(input_imgs)} 张")
        print(f"{'='*50}\n")

        # 生成图片
        image_bytes = provider.generate(args.prompt, input_imgs, width, height)

        # 保存到输出路径
        out_p = Path(args.output)
        out_p.parent.mkdir(parents=True, exist_ok=True)

        with open(out_p, 'wb') as f:
            f.write(image_bytes)

        print(f"\n{'='*50}")
        print(f"✓ 图片生成完成！")
        print(f"  保存位置：{out_p.resolve()}")
        print(f"{'='*50}")
        print(f"MEDIA: {out_p.resolve()}")

    except Exception as e:
        print(f"\n✗ 错误：{e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
