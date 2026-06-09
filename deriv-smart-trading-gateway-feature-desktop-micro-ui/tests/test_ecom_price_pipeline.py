from __future__ import annotations

import asyncio
from pathlib import Path

from ecom_price.pipeline import collect_and_compare


def test_collect_and_compare_sample(tmp_path: Path) -> None:
    rows, db_path = asyncio.run(
        collect_and_compare(
            keyword="蓝牙耳机",
            platforms=["sample"],
            limit_per_platform=20,
            output_dir=tmp_path,
            jd_enabled=False,
        )
    )
    assert rows
    assert db_path.exists()
    assert sum(1 for row in rows if row.recommended) <= 3

