#!/usr/bin/env python3
"""
GitHub 项目搜索脚本

通过 GitHub API 搜索仓库，支持按关键词、语言、star 数等条件筛选。
无需 Token，使用公开 API（60次/小时限制）。
"""

import argparse
import io
import json
import sys
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime
from typing import Optional

# 修复 Windows 控制台 UTF-8 输出问题
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def search_repositories(
    query: str,
    language: Optional[str] = None,
    min_stars: int = 0,
    topic: Optional[str] = None,
    sort: str = "stars",
    order: str = "desc",
    limit: int = 20
) -> dict:
    """
    搜索 GitHub 仓库。

    参数:
        query: 搜索关键词
        language: 编程语言筛选（可选）
        min_stars: 最低 star 数（默认 0）
        topic: 按 topic 筛选（可选）
        sort: 排序方式，可选 stars/forks/updated（默认 stars）
        order: 排序顺序，可选 desc/asc（默认 desc）
        limit: 返回结果数量（默认 20，最大 100）

    返回:
        dict: 包含搜索结果的字典，格式为 {"total_count": int, "items": list}
    """
    # 构建查询字符串
    q_parts = [query]

    if language:
        q_parts.append(f"language:{language}")

    if min_stars > 0:
        q_parts.append(f"stars:>={min_stars}")

    if topic:
        q_parts.append(f"topic:{topic}")

    q = " ".join(q_parts)

    # 构建 API URL
    # 使用 quote_via=urllib.parse.quote 避免空格被编码为 + 而非 %20
    # GitHub API 需要 + 作为 AND 连接符，所以手动处理
    params = {
        "sort": sort,
        "order": order,
        "per_page": min(limit, 100)
    }

    # 手动构建 q 参数，保留 + 作为连接符
    q_encoded = urllib.parse.quote(q, safe=":><=")
    q_encoded = q_encoded.replace("%20", "+")
    url = f"https://api.github.com/search/repositories?q={q_encoded}&{urllib.parse.urlencode(params)}"

    # 发送请求
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "GitHub-Project-Finder/1.0"
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))

            # 获取限流信息
            rate_limit = response.headers.get("X-RateLimit-Remaining", "unknown")
            rate_reset = response.headers.get("X-RateLimit-Reset", "unknown")

            return {
                "success": True,
                "total_count": data.get("total_count", 0),
                "items": format_results(data.get("items", [])),
                "rate_limit_remaining": rate_limit,
                "rate_limit_reset": rate_reset
            }

    except urllib.error.HTTPError as e:
        if e.code == 403:
            return {
                "success": False,
                "error": "API 限流，请稍后重试",
                "error_code": 403
            }
        elif e.code == 422:
            return {
                "success": False,
                "error": "查询语法错误",
                "error_code": 422
            }
        else:
            return {
                "success": False,
                "error": f"HTTP 错误: {e.code}",
                "error_code": e.code
            }
    except urllib.error.URLError as e:
        return {
            "success": False,
            "error": f"网络错误: {str(e.reason)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"未知错误: {str(e)}"
        }


def get_repository_details(owner: str, repo: str) -> dict:
    """
    获取单个仓库的详细信息。

    参数:
        owner: 仓库所有者
        repo: 仓库名称

    返回:
        dict: 仓库详细信息
    """
    url = f"https://api.github.com/repos/{owner}/{repo}"

    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "GitHub-Project-Finder/1.0"
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
            return {
                "success": True,
                "data": format_repo_detail(data)
            }
    except urllib.error.HTTPError as e:
        return {
            "success": False,
            "error": f"HTTP 错误: {e.code}",
            "error_code": e.code
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"错误: {str(e)}"
        }


def format_results(items: list) -> list:
    """
    格式化搜索结果列表。

    参数:
        items: GitHub API 返回的原始仓库列表

    返回:
        list: 格式化后的仓库信息列表
    """
    formatted = []
    for item in items:
        formatted.append({
            "name": item.get("name", ""),
            "full_name": item.get("full_name", ""),
            "owner": item.get("owner", {}).get("login", ""),
            "description": item.get("description", "") or "无描述",
            "url": item.get("html_url", ""),
            "stars": item.get("stargazers_count", 0),
            "forks": item.get("forks_count", 0),
            "open_issues": item.get("open_issues_count", 0),
            "language": item.get("language", "未知"),
            "license": item.get("license", {}).get("spdx_id", "未知") if item.get("license") else "未知",
            "created_at": item.get("created_at", ""),
            "updated_at": item.get("updated_at", ""),
            "pushed_at": item.get("pushed_at", ""),
            "topics": item.get("topics", []),
            "homepage": item.get("homepage", "")
        })
    return formatted


def format_repo_detail(data: dict) -> dict:
    """
    格式化单个仓库的详细信息。

    参数:
        data: GitHub API 返回的原始仓库数据

    返回:
        dict: 格式化后的仓库详细信息
    """
    return {
        "name": data.get("name", ""),
        "full_name": data.get("full_name", ""),
        "owner": data.get("owner", {}).get("login", ""),
        "description": data.get("description", "") or "无描述",
        "url": data.get("html_url", ""),
        "stars": data.get("stargazers_count", 0),
        "forks": data.get("forks_count", 0),
        "watchers": data.get("watchers_count", 0),
        "open_issues": data.get("open_issues_count", 0),
        "language": data.get("language", "未知"),
        "license": data.get("license", {}).get("spdx_id", "未知") if data.get("license") else "未知",
        "created_at": data.get("created_at", ""),
        "updated_at": data.get("updated_at", ""),
        "pushed_at": data.get("pushed_at", ""),
        "topics": data.get("topics", []),
        "homepage": data.get("homepage", ""),
        "default_branch": data.get("default_branch", "main"),
        "size": data.get("size", 0),
        "subscribers_count": data.get("subscribers_count", 0),
        "network_count": data.get("network_count", 0),
        "has_wiki": data.get("has_wiki", False),
        "has_pages": data.get("has_pages", False),
        "has_discussions": data.get("has_discussions", False)
    }


def main():
    """命令行入口函数。"""
    parser = argparse.ArgumentParser(
        description="GitHub 项目搜索工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --query "web framework" --language python --min-stars 1000
  %(prog)s --query "machine learning" --limit 10
  %(prog)s --topic "cli" --language rust --min-stars 500
  %(prog)s --detail owner/repo
        """
    )

    parser.add_argument(
        "--query", "-q",
        type=str,
        help="搜索关键词"
    )

    parser.add_argument(
        "--language", "-l",
        type=str,
        help="编程语言筛选"
    )

    parser.add_argument(
        "--min-stars", "-s",
        type=int,
        default=0,
        help="最低 star 数（默认: 0）"
    )

    parser.add_argument(
        "--topic", "-t",
        type=str,
        help="按 topic 筛选"
    )

    parser.add_argument(
        "--sort",
        type=str,
        choices=["stars", "forks", "updated"],
        default="stars",
        help="排序方式（默认: stars）"
    )

    parser.add_argument(
        "--order",
        type=str,
        choices=["desc", "asc"],
        default="desc",
        help="排序顺序（默认: desc）"
    )

    parser.add_argument(
        "--limit", "-n",
        type=int,
        default=20,
        help="返回结果数量（默认: 20，最大: 100）"
    )

    parser.add_argument(
        "--detail", "-d",
        type=str,
        help="获取指定仓库详情，格式: owner/repo"
    )

    parser.add_argument(
        "--output", "-o",
        type=str,
        choices=["json", "table"],
        default="json",
        help="输出格式（默认: json）"
    )

    args = parser.parse_args()

    # 获取仓库详情模式
    if args.detail:
        parts = args.detail.split("/")
        if len(parts) != 2:
            print(json.dumps({"success": False, "error": "仓库格式错误，应为 owner/repo"}))
            sys.exit(1)

        result = get_repository_details(parts[0], parts[1])
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result["success"] else 1)

    # 搜索模式
    if not args.query and not args.topic:
        parser.error("必须提供 --query 或 --topic 参数")

    query = args.query or ""

    result = search_repositories(
        query=query,
        language=args.language,
        min_stars=args.min_stars,
        topic=args.topic,
        sort=args.sort,
        order=args.order,
        limit=args.limit
    )

    if args.output == "table" and result["success"]:
        print_table(result["items"])
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    sys.exit(0 if result["success"] else 1)


def print_table(items: list) -> None:
    """
    以表格形式打印搜索结果。

    参数:
        items: 格式化后的仓库信息列表
    """
    if not items:
        print("未找到匹配的项目")
        return

    # 打印表头
    print(f"{'项目名称':<40} {'Star':<8} {'语言':<12} {'最后更新':<12}")
    print("-" * 80)

    for item in items:
        name = item["full_name"][:38] if len(item["full_name"]) > 38 else item["full_name"]
        stars = f"{item['stars']:,}"
        lang = (item["language"] or "未知")[:10]
        updated = item["pushed_at"][:10] if item["pushed_at"] else "未知"

        print(f"{name:<40} {stars:<8} {lang:<12} {updated:<12}")


if __name__ == "__main__":
    main()
