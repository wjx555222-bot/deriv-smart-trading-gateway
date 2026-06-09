from __future__ import annotations

import asyncio
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

import pandas as pd

from .models import ComparisonRow, Platform, ProductRecord
from .providers import JDSearchProvider, SampleSearchProvider
from .providers.base import SearchQuery


@dataclass(frozen=True, slots=True)
class CollectOptions:
    keyword: str
    platforms: Sequence[Platform]
    limit_per_platform: int = 20
    page: int = 1
    sample_path: Path | None = None
    jd_enabled: bool = True


def _default_output_dir() -> Path:
    return Path.cwd() / "output" / "ecom_price"


def _history_db_path(output_dir: Path) -> Path:
    return output_dir / "price_history.sqlite3"


def ensure_history_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            create table if not exists price_history (
              keyword text not null,
              platform text not null,
              product_id text,
              url text not null,
              name text not null,
              price real,
              sales integer,
              shop_name text,
              shop_rating real,
              fetched_at text not null
            )
            """
        )
        conn.execute(
            "create index if not exists idx_price_history_lookup on price_history(keyword, platform, product_id, url)"
        )
        conn.commit()


def append_history(db_path: Path, records: Iterable[ProductRecord]) -> None:
    ensure_history_db(db_path)
    rows = [
        (
            r.keyword,
            r.platform,
            r.product_id,
            str(r.url),
            r.name,
            r.price,
            r.sales,
            r.shop_name,
            r.shop_rating,
            r.fetched_at.isoformat(),
        )
        for r in records
    ]
    if not rows:
        return
    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            """
            insert into price_history (
              keyword, platform, product_id, url, name, price, sales, shop_name, shop_rating, fetched_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()


def load_price_trend(db_path: Path, *, keyword: str, url: str) -> pd.DataFrame:
    if not db_path.exists():
        return pd.DataFrame(columns=["fetched_at", "price"])
    with sqlite3.connect(db_path) as conn:
        frame = pd.read_sql_query(
            """
            select fetched_at, price
            from price_history
            where keyword = ? and url = ?
            order by fetched_at asc
            """,
            conn,
            params=(keyword, url),
        )
    if frame.empty:
        return frame
    frame["fetched_at"] = pd.to_datetime(frame["fetched_at"], utc=True, errors="coerce")
    frame["price"] = pd.to_numeric(frame["price"], errors="coerce")
    frame = frame.dropna(subset=["fetched_at", "price"])
    return frame


def normalize_and_score(records: Sequence[ProductRecord]) -> list[ComparisonRow]:
    if not records:
        return []

    prepared: list[dict[str, object]] = []
    for record in records:
        item = record.model_dump()
        item["url"] = str(record.url)
        prepared.append(item)
    frame = pd.DataFrame(prepared)
    frame["price"] = pd.to_numeric(frame["price"], errors="coerce")
    frame["sales"] = pd.to_numeric(frame["sales"], errors="coerce")
    frame["shop_rating"] = pd.to_numeric(frame["shop_rating"], errors="coerce")
    frame["url"] = frame["url"].astype(str)
    frame = frame.drop_duplicates(subset=["url"], keep="first")
    frame = frame.sort_values(by=["price", "sales"], ascending=[True, False], na_position="last")

    price = frame["price"]
    sales = frame["sales"].fillna(0)
    rating = frame["shop_rating"].fillna(0)

    def min_max(series: pd.Series) -> pd.Series:
        lo = float(series.min()) if series.size else 0.0
        hi = float(series.max()) if series.size else 0.0
        if hi - lo <= 1e-9:
            return pd.Series([0.5] * len(series), index=series.index, dtype="float64")
        return (series - lo) / (hi - lo)

    sales_norm = min_max(sales)
    rating_norm = min_max(rating)
    price_norm = min_max(price.fillna(price.max() if price.notna().any() else 0))
    price_good = 1.0 - price_norm

    frame["value_score"] = (0.45 * price_good + 0.35 * sales_norm + 0.20 * rating_norm).round(4)
    frame["value_score"] = frame["value_score"].where(frame["price"].notna(), None)

    recommended_urls = set(frame.sort_values("value_score", ascending=False).head(3)["url"].tolist())
    rows: list[ComparisonRow] = []
    for item in frame.to_dict(orient="records"):
        rows.append(
            ComparisonRow.model_validate(
                {
                    "platform": item.get("platform"),
                    "keyword": item.get("keyword"),
                    "name": item.get("name"),
                    "price": item.get("price") if pd.notna(item.get("price")) else None,
                    "sales": int(item["sales"]) if pd.notna(item.get("sales")) else None,
                    "shop_name": item.get("shop_name"),
                    "shop_rating": float(item["shop_rating"]) if pd.notna(item.get("shop_rating")) else None,
                    "url": item.get("url"),
                    "product_id": item.get("product_id"),
                    "fetched_at": item.get("fetched_at"),
                    "value_score": float(item["value_score"]) if item.get("value_score") is not None else None,
                    "recommended": item.get("url") in recommended_urls,
                }
            )
        )
    return rows


async def _collect_one(provider: object, query: SearchQuery) -> list[ProductRecord]:
    try:
        records = await provider.search(query)
        return list(records)
    except Exception:
        return []


async def collect_products(options: CollectOptions) -> list[ProductRecord]:
    keyword = options.keyword.strip()
    if not keyword:
        return []

    query = SearchQuery(keyword=keyword, limit=options.limit_per_platform, page=options.page)
    tasks: list[asyncio.Task[list[ProductRecord]]] = []

    for platform in options.platforms:
        if platform == "sample":
            provider = SampleSearchProvider(options.sample_path)
        elif platform == "jd":
            if not options.jd_enabled:
                continue
            provider = JDSearchProvider()
        else:
            provider = SampleSearchProvider(options.sample_path)
        tasks.append(asyncio.create_task(_collect_one(provider, query)))

    if not tasks:
        return []

    results = await asyncio.gather(*tasks)
    flattened: list[ProductRecord] = []
    for batch in results:
        flattened.extend(batch)
    return flattened


async def collect_and_compare(
    *,
    keyword: str,
    platforms: Sequence[Platform] = ("jd", "taobao", "pdd"),
    limit_per_platform: int = 20,
    output_dir: Path | None = None,
    sample_path: Path | None = None,
    jd_enabled: bool = True,
) -> tuple[list[ComparisonRow], Path]:
    output_dir = output_dir or _default_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    db_path = _history_db_path(output_dir)

    fetched_at = datetime.now(timezone.utc)
    records = await collect_products(
        CollectOptions(
            keyword=keyword,
            platforms=platforms,
            limit_per_platform=limit_per_platform,
            page=1,
            sample_path=sample_path,
            jd_enabled=jd_enabled,
        )
    )
    for record in records:
        record.fetched_at = fetched_at

    append_history(db_path, records)
    return normalize_and_score(records), db_path
