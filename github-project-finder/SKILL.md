---
name: github-project-finder
description: This skill should be used when the user asks to "搜索 GitHub 项目", "找开源项目", "推荐 GitHub 仓库", "查找技术方案参考", or mentions "github search", "开源推荐", "项目调研". 搜索高质量开源项目并生成 Markdown 推荐报告。
version: 0.2.0
---

# GitHub 优质项目搜索 Skill

搜索 GitHub 上的高质量开源项目，通过多源并行搜索策略发现优质项目，生成结构化的 Markdown 推荐报告。

## 重要规则

**必须遵守以下规则：**

1. **必须先确认需求**：在执行任何搜索之前，必须使用 AskUserQuestion 工具向用户确认需求
2. **必须使用英文关键词**：所有搜索查询必须使用英文关键词，GitHub 搜索对英文支持更好
3. **必须等待用户确认**：只有在用户确认需求后才能开始搜索

## 工作流程

### 阶段 1：需求澄清（必须执行）

**⚠️ 强制要求：必须使用 AskUserQuestion 工具收集以下信息，不能跳过！**

使用 AskUserQuestion 工具询问用户：

```
必须收集的信息：
1. 核心需求/主题 - 用户想实现什么功能
2. 编程语言 - 首选或可接受的语言
3. 项目类型 - 库/框架/工具/应用
```

**AskUserQuestion 示例：**

```json
{
  "questions": [
    {
      "header": "搜索目标",
      "question": "请确认您的搜索需求，我理解您想找：[总结用户需求]。这个理解正确吗？",
      "options": [
        {"label": "正确，开始搜索", "description": "按照上述理解进行搜索"},
        {"label": "需要补充", "description": "我想补充或修改需求"}
      ],
      "multiSelect": false
    },
    {
      "header": "编程语言",
      "question": "您希望使用什么编程语言？",
      "options": [
        {"label": "Python", "description": "Python 语言项目"},
        {"label": "JavaScript/TypeScript", "description": "JS/TS 语言项目"},
        {"label": "不限", "description": "任何语言都可以"}
      ],
      "multiSelect": false
    }
  ]
}
```

**可选信息（有默认值）：**

| 信息项 | 默认值 |
|--------|--------|
| 最低 star 数 | 100 |
| 活跃度要求 | 6个月内有更新 |
| 许可证偏好 | 不限 |
| 推荐数量 | 15-20 个 |

### 阶段 2：关键词转换（必须执行）

**⚠️ 强制要求：将用户的中文需求转换为英文搜索关键词！**

**转换规则：**
- 将中文技术术语翻译为对应的英文术语
- 使用常见的英文技术词汇
- 组合多个相关关键词

**转换示例：**

| 用户需求（中文） | 搜索关键词（英文） |
|------------------|-------------------|
| AI 助手宠物玩具 | AI companion pet robot, virtual pet AI |
| 长期记忆 | long-term memory, conversation memory |
| 情感计算 | emotion detection, sentiment analysis |
| 语音交互 | voice assistant, speech recognition |
| 硬件机器人 | ESP32 robot, M5Stack robot, hardware AI |

### 阶段 3：多源并行搜索

执行四种搜索源的并行搜索，最大化项目发现范围。

**⚠️ 所有搜索查询必须使用英文！**

**搜索源组合策略：**

| 用户意图 | 推荐搜索源组合 |
|----------|----------------|
| 找热门项目 | GitHub API (主) + Topics (辅) |
| 找最佳实践 | WebSearch (主) + Sourcegraph (辅) |
| 找特定实现 | Sourcegraph (主) + GitHub API (辅) |
| 领域探索 | Topics (主) + WebSearch (辅) |
| 综合发现（默认） | 全部搜索源并行 |

**第一层搜索（并行执行）：**

1. **GitHub API 搜索**
   使用 `scripts/search_github.py` 脚本：
   ```bash
   python scripts/search_github.py --query "english keywords" --language "{lang}" --min-stars {min} --limit 20
   ```
   或直接使用 curl：
   ```bash
   curl -s "https://api.github.com/search/repositories?q=english+keywords+language:{lang}+stars:>{min_stars}&sort=stars&per_page=20"
   ```

2. **WebSearch 搜索**（使用英文查询）
   执行以下搜索查询：
   - `awesome-{english-keyword} github` - 发现 awesome 列表
   - `best {english-keyword} libraries {year}` - 年度推荐
   - `site:dev.to OR site:medium.com {english-keyword} best libraries` - 技术博客推荐

3. **GitHub Topics 发现**
   访问相关 topics 页面或使用 API：
   ```bash
   curl -s "https://api.github.com/search/repositories?q=topic:{english-topic}&sort=stars&per_page=20"
   ```

**第二层搜索（基于第一层结果）：**

1. **GitHub API 详情获取**
   对每个发现的仓库获取完整元数据：
   ```bash
   curl -s "https://api.github.com/repos/{owner}/{repo}"
   ```

2. **Sourcegraph 代码验证**（可选）
   验证代码质量和实现方式：
   ```
   repo:^github\.com/{owner}/{repo}$ type:file
   ```

### 阶段 4：结果整合

**去重规则：**
- 按 `owner/repo` 去重
- 保留最完整的信息
- 记录所有来源（用于多源验证加分）

**多源验证：**
- 被 2 个源发现：+5 分
- 被 3 个以上源发现：+10 分
- 出现在 awesome 列表：+5 分

### 阶段 5：质量评估

使用综合评分算法对项目进行排序。详细评估标准参见 `references/quality-criteria.md`。

**评分公式：**
```
总分 = Stars(25%) + 活跃度(20%) + 多源验证(15%)
     + 文档质量(15%) + 维护状态(15%) + 社区(10%)
     + 加分项
```

**评分维度：**

| 维度 | 权重 | 优秀标准 | 评分方法 |
|------|------|----------|----------|
| Star 数 | 25% | >1000 | log10(stars) * 10，上限 25 |
| 活跃度 | 20% | 3个月内更新 | 根据最后更新时间评分 |
| 多源验证 | 15% | 被3个以上源发现 | 每个额外来源 +5 |
| 文档质量 | 15% | 完整 README | 检查 README 长度和结构 |
| 维护状态 | 15% | Issues 响应率 >50% | open_issues / (open + closed) |
| 社区活跃 | 10% | 贡献者 >10 人 | contributors 数量评分 |

**加分项：**
- 出现在 awesome 列表：+5
- 有明确 LICENSE：+5
- 有 CI/CD 配置：+3
- 有完整文档站点：+5

### 阶段 6：生成报告

**询问保存位置：**
```
报告已准备就绪，请问您希望将报告保存到哪里？
1. 当前工作目录（默认）
2. 指定路径
```

**输出文件命名：** `github-projects-{keyword}-{date}.md`

**Markdown 报告模板：**

```markdown
# GitHub 优质项目推荐报告

**搜索需求：** [需求描述]
**搜索时间：** [日期]
**筛选条件：** 语言: [语言] | 最低 Star: [数值]

## 推荐项目列表

| 项目名称 | 项目描述 | 推荐理由 | 项目链接 |
|----------|----------|----------|----------|
| [名称](URL) | [详细描述] | [匹配度+质量指标] | URL |

## 项目详情

### 1. [项目名称]
- ⭐ Star: X,XXX | 🍴 Fork: XXX | 📅 最后更新: YYYY-MM-DD
- **描述：** [2-3句详细描述]
- **核心特性：** [特性列表]
- **推荐理由：** [为什么适合用户需求]
- **链接：** [GitHub URL]

---

## 搜索方法说明

本报告通过以下搜索源综合发现：
- GitHub API 关键词搜索
- WebSearch 发现 awesome 列表和博客推荐
- GitHub Topics 分类浏览
- Sourcegraph 代码验证（如适用）

---

*报告生成时间：[时间戳]*
```

## 搜索语法参考

详细的多源搜索语法参见 `references/search-syntax.md`。

### GitHub API 常用查询（必须使用英文）

```bash
# 按关键词和语言搜索
q=web+framework+language:python+stars:>100

# 按 topic 搜索
q=topic:machine-learning+stars:>100

# 按更新时间筛选
q=chatbot+pushed:>2024-01-01

# 组合查询
q=voice+assistant+language:python+stars:>100+pushed:>2024-01-01
```

### WebSearch 搜索模式（必须使用英文）

```
# Awesome 列表发现
awesome-python github
awesome-chatbot github

# 年度推荐
best python web frameworks 2024
best AI companion libraries 2024

# 技术博客
site:dev.to voice assistant best libraries
site:medium.com AI pet robot recommendations
```

## 错误处理

**API 限流处理：**
- GitHub API 无 Token 限制：60 次/小时
- 遇到限流时，提示用户等待或使用 WebSearch 替代
- 显示剩余配额：检查响应头 `X-RateLimit-Remaining`

**搜索无结果处理：**
- 放宽搜索条件（降低 star 要求）
- 尝试相关英文关键词
- 使用 WebSearch 发现替代方案

## 注意事项

1. **必须先确认需求**：使用 AskUserQuestion 工具确认用户需求后再搜索
2. **必须使用英文关键词**：所有搜索查询使用英文，提高搜索效果
3. **优先无 Token 模式**：使用公开 API，注意 60 次/小时限制
4. **并行搜索**：尽可能并行执行多个搜索源以提高效率
5. **结果验证**：对高分项目进行二次验证，确保信息准确
6. **用户确认**：在生成报告前确认保存位置
7. **中文输出**：所有输出和交互使用中文（但搜索用英文）

## 参考资料

- `references/search-syntax.md` - 多源搜索语法详解
- `references/quality-criteria.md` - 项目质量评估标准
- `references/sourcegraph-guide.md` - Sourcegraph 使用指南
