from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from ecom_price.models import Platform
from ecom_price.pipeline import collect_and_compare
from ecom_price.report import rows_to_frame, write_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="ecom-price",
        description="电商商品价格自动化采集与对比（离线示例 + 可选 JD 抓取）",
    )
    parser.add_argument("keyword", help="搜索关键词，例如：蓝牙耳机/充电宝")
    parser.add_argument(
        "--platforms",
        nargs="+",
        default=["jd", "taobao", "pdd"],
        help="平台列表：jd taobao pdd sample",
    )
    parser.add_argument("--limit", type=int, default=20, help="每个平台最多抓取条数")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path.cwd() / "output" / "ecom_price",
        help="输出目录（默认：./output/ecom_price）",
    )
    parser.add_argument(
        "--disable-jd",
        action="store_true",
        help="禁用 JD 在线抓取（强制使用离线示例数据）",
    )
    return parser.parse_args()


def normalize_platforms(values: list[str]) -> list[Platform]:
    allowed: set[str] = {"jd", "taobao", "pdd", "sample"}
    platforms: list[Platform] = []
    for item in values:
        key = item.strip().lower()
        if key in allowed:
            platforms.append(key)
    return platforms or ["sample"]


async def run() -> int:
    args = parse_args()
    platforms = normalize_platforms(args.platforms)
    rows, db_path = await collect_and_compare(
        keyword=args.keyword,
        platforms=platforms,
        limit_per_platform=max(int(args.limit), 1),
        output_dir=args.output_dir,
        jd_enabled=not args.disable_jd,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    frame = rows_to_frame(rows)

    csv_path = args.output_dir / "clean.csv"
    frame.to_csv(csv_path, index=False, encoding="utf-8-sig")

    json_path = args.output_dir / "clean.json"
    json_path.write_text(
        json.dumps([r.model_dump(mode="json") for r in rows], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    report_path = write_report(rows=rows, output_dir=args.output_dir, db_path=db_path, basename="report")

    best = [r for r in rows if r.recommended][:3]
    if best:
        print("性价比推荐：")
        for idx, item in enumerate(best, start=1):
            print(f"{idx}. [{item.platform}] {item.name} 价格={item.price} 评分={item.value_score} {item.url}")

    print(f"已输出：{csv_path}")
    print(f"已输出：{json_path}")
    print(f"已输出：{report_path}")
    return 0


def main() -> None:
    raise SystemExit(asyncio.run(run()))


if __name__ == "__main__":
    main()
