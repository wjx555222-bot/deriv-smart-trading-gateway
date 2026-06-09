from __future__ import annotations

import asyncio
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from ecom_price.models import Platform
from ecom_price.pipeline import collect_and_compare, load_price_trend
from ecom_price.report import rows_to_frame


st.set_page_config(page_title="电商价格采集对比", layout="wide")

st.title("电商商品价格自动化采集与对比")
st.caption("离线示例数据可直接运行；启用 JD 在线抓取需要网络环境且可能受反爬影响。")

default_keyword = "蓝牙耳机"
keyword = st.text_input("关键词", value=default_keyword, help="例如：蓝牙耳机 / 充电宝 / 机械键盘")

platform_options: list[Platform] = ["jd", "taobao", "pdd"]
platforms = st.multiselect("平台", options=platform_options, default=platform_options)

limit = st.slider("每个平台抓取条数", min_value=5, max_value=50, value=20, step=5)
disable_jd = st.checkbox("禁用 JD 在线抓取（使用离线示例数据替代）", value=False)

output_dir = Path.cwd() / "output" / "ecom_price"


def run_compare() -> tuple[pd.DataFrame, Path]:
    rows, db_path = asyncio.run(
        collect_and_compare(
            keyword=keyword,
            platforms=platforms or ["jd"],
            limit_per_platform=int(limit),
            output_dir=output_dir,
            jd_enabled=not disable_jd,
        )
    )
    return rows_to_frame(rows), db_path


col_a, col_b = st.columns([1, 2], gap="large")

with col_a:
    st.subheader("运行采集")
    run_clicked = st.button("开始采集与对比", type="primary")
    st.write(f"输出目录：{output_dir}")

    sample_path = Path(__file__).resolve().parent.parent / "ecom_price" / "sample_data" / "sample_products.json"
    with st.expander("初始化示例数据（sample_products.json）", expanded=False):
        st.code(sample_path.read_text(encoding="utf-8"), language="json")

with col_b:
    if run_clicked:
        with st.spinner("采集中..."):
            frame, db_path = run_compare()
        st.session_state["ecom_price_frame"] = frame
        st.session_state["ecom_price_db"] = str(db_path)

frame: pd.DataFrame | None = st.session_state.get("ecom_price_frame")
db_path_value = st.session_state.get("ecom_price_db")
db_path = Path(db_path_value) if db_path_value else (output_dir / "price_history.sqlite3")

if frame is None:
    rows, db_path = asyncio.run(
        collect_and_compare(
            keyword=default_keyword,
            platforms=["sample"],
            limit_per_platform=20,
            output_dir=output_dir,
            jd_enabled=False,
        )
    )
    frame = rows_to_frame(rows)
    st.session_state["ecom_price_frame"] = frame
    st.session_state["ecom_price_db"] = str(db_path)

st.subheader("对比结果")
if frame.empty:
    st.info("没有抓取到数据。可以尝试切换关键词、减少平台或勾选禁用 JD 在线抓取。")
else:
    display = frame.sort_values("price", na_position="last")
    st.dataframe(
        display[
            [
                "recommended",
                "platform",
                "name",
                "price",
                "sales",
                "shop_name",
                "shop_rating",
                "value_score",
                "url",
            ]
        ],
        use_container_width=True,
        height=460,
    )

    if display["price"].notna().any():
        price_frame = display.dropna(subset=["price"]).head(20)
        fig_price = px.bar(
            price_frame,
            x="price",
            y="name",
            color="platform",
            orientation="h",
            title="价格从低到高（Top 20）",
            hover_data=["sales", "shop_rating", "url", "value_score", "recommended"],
        )
        fig_price.update_layout(height=650, margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig_price, use_container_width=True)

        fig_box = px.box(
            display.dropna(subset=["price"]),
            x="platform",
            y="price",
            points="all",
            title="平台价格分布",
            hover_data=["name", "url"],
        )
        fig_box.update_layout(height=420, margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig_box, use_container_width=True)

    st.subheader("价格趋势")
    selectable = display.dropna(subset=["url"]).head(50)
    selected = st.selectbox(
        "选择一个商品查看历史价格",
        options=list(range(len(selectable))),
        format_func=lambda i: f"[{selectable.iloc[i]['platform']}] {selectable.iloc[i]['name']}",
    )
    selected_row = selectable.iloc[int(selected)]
    trend = load_price_trend(db_path, keyword=str(selected_row["keyword"]), url=str(selected_row["url"]))
    if trend.empty:
        st.info("该商品暂时没有历史趋势数据；多运行几次采集后会自动累计。")
    else:
        fig_trend = px.line(trend, x="fetched_at", y="price", markers=True, title="历史价格趋势")
        fig_trend.update_layout(height=360, margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig_trend, use_container_width=True)

