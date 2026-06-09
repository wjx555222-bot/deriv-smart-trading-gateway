from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from typing import Iterable

import httpx

from ..models import ProductRecord
from .base import ProviderError, SearchProvider, SearchQuery


def _parse_compact_int(value: str | None) -> int | None:
    if not value:
        return None
    raw = value.strip().replace(",", "")
    raw = raw.replace("+", "")
    if not raw:
        return None
    if "万" in raw:
        try:
            num = float(raw.replace("万", ""))
        except ValueError:
            return None
        return int(math.floor(num * 10_000))
    digits = re.sub(r"[^\d]", "", raw)
    if not digits:
        return None
    try:
        return int(digits)
    except ValueError:
        return None


class JDSearchProvider(SearchProvider):
    platform = "jd"

    def __init__(
        self,
        *,
        timeout_seconds: float = 10.0,
        user_agent: str | None = None,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )

    async def search(self, query: SearchQuery) -> Iterable[ProductRecord]:
        try:
            from bs4 import BeautifulSoup
        except Exception as exc:
            raise ProviderError("JD provider requires beautifulsoup4") from exc

        fetched_at = datetime.now(timezone.utc)
        page = max(query.page, 1)
        url = "https://search.jd.com/Search"
        params = {"keyword": query.keyword, "enc": "utf-8", "page": str(2 * page - 1)}
        headers = {"User-Agent": self.user_agent, "Accept-Language": "zh-CN,zh;q=0.9"}

        async with httpx.AsyncClient(timeout=self.timeout_seconds, headers=headers, follow_redirects=True) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            items = soup.select("li.gl-item[data-sku]")
            if not items:
                raise ProviderError("JD search page parse failed (no items found)")

            sku_ids: list[str] = []
            partial: dict[str, dict[str, object]] = {}
            for li in items:
                sku = str(li.get("data-sku") or "").strip()
                if not sku:
                    continue
                anchor = li.select_one("div.p-name a")
                name_node = li.select_one("div.p-name em")
                name = name_node.get_text(" ", strip=True) if name_node else None
                href = anchor.get("href") if anchor else None
                if href and href.startswith("//"):
                    href = f"https:{href}"
                elif href and href.startswith("/"):
                    href = f"https://item.jd.com{href}"

                shop_node = li.select_one("div.p-shop a")
                commit_node = li.select_one("div.p-commit strong a")
                partial[sku] = {
                    "name": name,
                    "url": href,
                    "shop_name": shop_node.get_text(" ", strip=True) if shop_node else None,
                    "sales": _parse_compact_int(commit_node.get_text(strip=True) if commit_node else None),
                }
                sku_ids.append(sku)
                if len(sku_ids) >= max(query.limit, 1):
                    break

            prices: dict[str, float] = {}
            if sku_ids:
                chunks = [sku_ids[i : i + 20] for i in range(0, len(sku_ids), 20)]
                for chunk in chunks:
                    price_url = "https://p.3.cn/prices/mgets"
                    sku_param = ",".join([f"J_{sku}" for sku in chunk])
                    price_response = await client.get(price_url, params={"skuIds": sku_param})
                    price_response.raise_for_status()
                    payload = price_response.json()
                    if isinstance(payload, list):
                        for row in payload:
                            sku = str(row.get("id") or "").replace("J_", "")
                            try:
                                prices[sku] = float(row.get("p"))
                            except Exception:
                                continue

            records: list[ProductRecord] = []
            for sku in sku_ids:
                item = partial.get(sku) or {}
                name = str(item.get("name") or "").strip()
                link = str(item.get("url") or "").strip()
                if not name or not link:
                    continue
                records.append(
                    ProductRecord.model_validate(
                        {
                            "platform": "jd",
                            "keyword": query.keyword,
                            "name": name,
                            "price": prices.get(sku),
                            "sales": item.get("sales"),
                            "shop_name": item.get("shop_name"),
                            "shop_rating": None,
                            "url": link,
                            "product_id": sku,
                            "fetched_at": fetched_at,
                            "raw": {"sku": sku},
                        }
                    )
                )
            return records
