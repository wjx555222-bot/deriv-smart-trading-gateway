from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from ..models import Platform, ProductRecord
from .base import SearchProvider, SearchQuery


class SampleSearchProvider(SearchProvider):
    platform: Platform = "sample"

    def __init__(self, sample_path: Path | None = None) -> None:
        self.sample_path = sample_path or (
            Path(__file__).resolve().parent.parent / "sample_data" / "sample_products.json"
        )

    async def search(self, query: SearchQuery) -> Iterable[ProductRecord]:
        fetched_at = datetime.now(timezone.utc)
        items = json.loads(self.sample_path.read_text(encoding="utf-8"))
        keyword = query.keyword.strip().lower()
        matched = [
            item
            for item in items
            if keyword in str(item.get("name") or "").lower()
            or keyword in str(item.get("shop_name") or "").lower()
        ]
        if not matched:
            matched = items

        records: list[ProductRecord] = []
        for item in matched[: max(query.limit, 1)]:
            platform = item.get("platform") or "sample"
            if platform not in ("jd", "taobao", "pdd"):
                platform = "sample"
            records.append(
                ProductRecord.model_validate(
                    {
                        "platform": platform,
                        "keyword": query.keyword,
                        "name": item.get("name") or "unknown",
                        "price": item.get("price"),
                        "sales": item.get("sales"),
                        "shop_name": item.get("shop_name"),
                        "shop_rating": item.get("shop_rating"),
                        "url": item.get("url"),
                        "product_id": item.get("product_id"),
                        "fetched_at": fetched_at,
                        "raw": item,
                    }
                )
            )
        return records

