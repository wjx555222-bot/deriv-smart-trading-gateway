from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable

from ..models import Platform, ProductRecord


class ProviderError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class SearchQuery:
    keyword: str
    limit: int = 20
    page: int = 1


class SearchProvider(ABC):
    platform: Platform

    @abstractmethod
    async def search(self, query: SearchQuery) -> Iterable[ProductRecord]:
        raise NotImplementedError

