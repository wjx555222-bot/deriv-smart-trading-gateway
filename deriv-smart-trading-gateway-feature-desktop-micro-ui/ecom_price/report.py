from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.io as pio

from .models import ComparisonRow
from .pipeline import load_price_trend


def rows_to_frame(rows: list[ComparisonRow]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(
            columns=[
                "platform",
                "keyword",
                "name",
                "price",
                "sales",
                "shop_name",
                "shop_rating",
                "url",
                "value_score",
                "recommended",
                "fetched_at",
            ]
        )
    prepared: list[dict[str, object]] = []
    for row in rows:
        item = row.model_dump()
        item["url"] = str(row.url)
        prepared.append(item)
    frame = pd.DataFrame(prepared)
    frame["fetched_at"] = pd.to_datetime(frame["fetched_at"], utc=True, errors="coerce")
    return frame


def build_report_html(rows: list[ComparisonRow], *, db_path: Path) -> str:
    frame = rows_to_frame(rows)
    keyword = str(frame["keyword"].iloc[0]) if not frame.empty else ""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    plots: list[str] = []
    include_js = True

    if not frame.empty and frame["price"].notna().any():
        price_frame = frame.dropna(subset=["price"]).copy()
        price_frame = price_frame.sort_values("price", ascending=True).head(20)
        fig_price = px.bar(
            price_frame,
            x="price",
            y="name",
            color="platform",
            orientation="h",
            title="价格从低到高（Top 20）",
            hover_data=["sales", "shop_rating", "url", "value_score", "recommended"],
        )
        fig_price.update_layout(height=700, margin=dict(l=10, r=10, t=50, b=10))
        plots.append(
            pio.to_html(
                fig_price,
                include_plotlyjs="inline" if include_js else False,
                full_html=False,
            )
        )
        include_js = False

        fig_box = px.box(
            frame.dropna(subset=["price"]),
            x="platform",
            y="price",
            points="all",
            title="平台价格分布",
            hover_data=["name", "url"],
        )
        fig_box.update_layout(height=420, margin=dict(l=10, r=10, t=50, b=10))
        plots.append(pio.to_html(fig_box, include_plotlyjs=False, full_html=False))

        rec = frame[frame["recommended"] == True].head(3)
        for _, row in rec.iterrows():
            trend = load_price_trend(db_path, keyword=str(row["keyword"]), url=str(row["url"]))
            if trend.empty:
                continue
            fig_trend = px.line(
                trend,
                x="fetched_at",
                y="price",
                markers=True,
                title=f"价格趋势：{row['name']}",
            )
            fig_trend.update_layout(height=360, margin=dict(l=10, r=10, t=50, b=10))
            plots.append(pio.to_html(fig_trend, include_plotlyjs=False, full_html=False))

    table_html = frame.sort_values("price", na_position="last").to_html(
        index=False, escape=True, justify="left"
    )

    return f"""
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>电商价格对比报告 - {keyword}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, "PingFang SC", "Microsoft YaHei", sans-serif; margin: 24px; }}
    h1 {{ margin: 0 0 8px 0; font-size: 22px; }}
    .meta {{ color: #666; margin-bottom: 18px; }}
    .badge {{ display: inline-block; padding: 2px 10px; border-radius: 999px; background: #0ea5e9; color: #fff; font-size: 12px; }}
    .grid {{ display: grid; grid-template-columns: 1fr; gap: 16px; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
    th, td {{ border: 1px solid #e5e7eb; padding: 6px 8px; vertical-align: top; }}
    th {{ background: #f9fafb; text-align: left; }}
    .note {{ color: #6b7280; font-size: 12px; margin-top: 10px; }}
  </style>
</head>
<body>
  <h1>电商商品价格采集与对比报告 <span class="badge">{keyword}</span></h1>
  <div class="meta">生成时间：{now}</div>
  <div class="grid">
    {''.join(plots)}
    <div>
      <h2 style="font-size:16px;margin:0 0 8px 0;">横向对比明细</h2>
      {table_html}
      <div class="note">说明：推荐标注基于价格、销量、店铺评分的归一化加权得分（value_score）。真实抓取字段受平台风控与反爬策略影响，缺失字段会自动降级。</div>
    </div>
  </div>
</body>
</html>
""".strip()


def write_report(
    *,
    rows: list[ComparisonRow],
    output_dir: Path,
    db_path: Path,
    basename: str = "report",
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / f"{basename}.html"
    report_path.write_text(build_report_html(rows, db_path=db_path), encoding="utf-8")
    return report_path
