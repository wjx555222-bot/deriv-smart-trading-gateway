from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, StringConstraints
from typing_extensions import Annotated

NonEmptyString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Platform = Literal["jd", "taobao", "pdd", "sample"]


class ProductRecord(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    platform: Platform
    keyword: NonEmptyString
    name: NonEmptyString
    price: float | None = Field(default=None, ge=0)
    sales: int | None = Field(default=None, ge=0)
    shop_name: str | None = None
    shop_rating: float | None = Field(default=None, ge=0, le=5)
    url: HttpUrl
    product_id: str | None = None
    fetched_at: datetime
    raw: dict[str, Any] | None = None


class ComparisonRow(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    platform: Platform
    keyword: NonEmptyString
    name: NonEmptyString
    price: float | None
    sales: int | None
    shop_name: str | None
    shop_rating: float | None
    url: HttpUrl
    product_id: str | None
    fetched_at: datetime
    value_score: float | None
    recommended: bool

