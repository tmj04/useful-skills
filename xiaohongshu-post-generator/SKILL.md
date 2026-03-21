---
name: xiaohongshu-post-generator
description: >-
  生成小红书图文帖子。给定包含图片和文字的文件或文件夹，自动分析内容，
  联网搜索热门帖子作为参考，生成爆款小红书标题、正文、话题标签，并生成封面图和内容轮播图。
  触发词：小红书、生成小红书帖子、小红书文案、小红书封面、xhs、红书种草、
  xiaohongshu、生成种草帖、小红书图文
license: Apache 2.0
---

# 小红书图文帖子生成

基于输入的素材（图片 + 文字），自动生成易爆的小红书图文帖子。包括：
- 🔍 联网搜索相关热门帖子，学习爆款套路
- ✨ 生成 5 个备选爆款标题
- 📝 生成小红书风格的正文文案
- 🎨 生成封面图 + 内容轮播图（3:4 竖版）
- 🏷️ 智能匹配话题标签

## 默认配置

**默认图片生成供应商**: `gemini`

用户可通过以下方式指定供应商：
- "用百炼生成" / "使用 dashscope"
- "provider=dashscope"
- "--provider dashscope"

## 环境要求

- Python 3.10+
- 依赖库：`pip install -r requirements.txt`
- API Key: `GEMINI_API_KEY` 或 `DASHSCOPE_API_KEY`

# 小红书图文帖子生成

基于输入的素材（图片 + 文字），自动生成易爆的小红书图文帖子。包括：
- 🔍 联网搜索相关热门帖子，学习爆款套路
- ✨ 生成 5 个备选爆款标题
- 📝 生成小红书风格的正文文案
- 🎨 生成封面图 + 内容轮播图（3:4 竖版）
- 🏷️ 智能匹配话题标签

## 默认配置

**默认图片生成供应商**: `gemini`

用户可通过以下方式指定供应商：
- "用百炼生成" / "使用 dashscope"
- "provider=dashscope"
- "--provider dashscope"

## 工作流程

### 阶段 1：素材扫描

运行脚本扫描输入的文件/文件夹：

```bash
python scripts/analyze_input.py "<输入路径>"
```

输出 JSON，包含：
- `images`: 图片列表（路径、尺寸、格式）
- `texts`: 文本文件列表（路径、内容）
- `output_path`: 自动创建的输出目录

### 阶段 2：热门帖子搜索

使用 WebSearch 搜索相关热门帖子，获取爆款参考：

```
搜索词模板：
- "小红书 <关键词> 爆款笔记"
- "小红书 <关键词> 种草"
- "site:xiaohongshu.com <关键词>"
```

分析搜索结果，提取：
- 爆款标题的共性套路
- 热门帖子的内容结构
- 高频话题标签
- 当前流行趋势

### 阶段 3：内容分析与文案生成

阅读素材并结合热门搜索结果：

1. **提炼核心卖点** - 从素材中挖掘亮点
2. **生成 5 个备选标题** - 参考热门搜索 + 风格指南中的爆款公式
3. **生成正文** - emoji 分段、口语化、种草风格
4. **生成 8-12 个话题标签** - 包含搜索中发现的高频标签
5. **规划图片序列** - 决定几张图、每张是什么内容
6. **准备图片生成 prompt** - 为 AI 生成做准备

### 阶段 4：图片生成

依次调用脚本生成每张图片：

**生成封面图**:
```bash
python scripts/generate_image.py \
  --provider gemini \
  --type cover \
  --prompt "小红书风格封面图描述" \
  --input-images <素材图路径> \
  --aspect-ratio 3:4 \
  --output output/01_cover.png
```

**生成内容卡片**:
```bash
python scripts/generate_image.py \
  --provider gemini \
  --type card \
  --prompt "内容卡片描述" \
  --aspect-ratio 3:4 \
  --output output/02_card.png
```

**美化素材图**:
```bash
python scripts/generate_image.py \
  --provider dashscope \
  --type enhance \
  --prompt "美化指令" \
  --input-images <素材图> \
  --aspect-ratio 3:4 \
  --output output/03_photo.png
```

### 阶段 5：文案保存

将完整文案保存到 `output/post_content.md`，格式可直接复制到小红书。

### 阶段 6：输出展示与迭代

- 展示所有生成的图片
- 展示完整文案
- 告知输出目录路径
- 支持迭代调整（重新生成某张图、修改文案等）

## 图片生成供应商说明

### Gemini (默认)

**环境变量**: `GEMINI_API_KEY`

**特点**:
- 支持输入图片 + 文本混合生成
- 同步返回，速度快
- 中文 prompt 支持良好

### 百炼/通义万相

**环境变量**: `DASHSCOPE_API_KEY`

**特点**:
- 文生图：wanx2.1-t2i-turbo
- 图片编辑：wanx2.5-image-edit
- 异步任务 + 轮询

## 封面风格选项

参考 `references/xhs-style-guide.md`，支持的风格：

| 风格 | 适用场景 |
|------|----------|
| 大字报 (big-text) | 干货分享、攻略 |
| 杂志风 (magazine) | 穿搭、美妆、生活方式 |
| 知识卡片 (knowledge) | 教程、科普 |
| 对比图 (comparison) | 测评、红黑榜 |
| 拼贴手账 (collage) | 旅行、日常 |
| 简约 INS 风 (minimal) | 家居、文艺 |

## 使用示例

**基本用法**:
```
用户："帮我用这个文件夹生成小红书帖子"
→ Claude 扫描素材 → 搜索热门 → 生成文案 → 生成图片 → 输出结果
```

**指定供应商**:
```
用户："用百炼生成小红书封面"
→ 使用 provider=dashscope 调用 generate_image.py
```

**自定义要求**:
```
用户："生成小红书帖子，用杂志风的封面"
→ 在 prompt 中使用 magazine 风格模板
```

## 输出目录结构

```
<输入文件夹>/
├── [原始素材...]
└── output/
    ├── 01_cover.png      # 封面图
    ├── 02_card.png       # 内容卡片 1
    ├── 03_card.png       # 内容卡片 2
    └── post_content.md   # 完整文案
```

## Resources

- `scripts/analyze_input.py` - 素材扫描脚本
- `scripts/generate_image.py` - 多供应商图片生成脚本
- `references/xhs-style-guide.md` - 小红书风格详细指南

## 注意事项

1. **API Key 配置**: 使用前确保配置了对应供应商的 API key 环境变量
2. **图片尺寸**: 所有输出固定为 3:4 比例 (1080x1440)，符合小红书最佳实践
3. **网络搜索**: 阶段 2 会自动使用 WebSearch，无需额外配置
4. **迭代优化**: 如果效果不满意，可以要求重生成某张图或调整文案
