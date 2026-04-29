from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class MarketQuote:
    symbol: str
    price: float
    change_pct: float
    volume: int
    source: str = "mock"


class MockMarketDataAdapter:
    """默认模拟数据源，保证 MVP 不联网也能跑。

    后续可替换为真实行情 API、广告 API、飞书多维表格 API、企业微信 API。
    """

    def get_quotes(self, symbols: List[str]) -> List[MarketQuote]:
        quotes: List[MarketQuote] = []
        for symbol in symbols:
            seed = int(hashlib.sha256(symbol.encode("utf-8")).hexdigest()[:8], 16)
            rng = random.Random(seed)
            base = rng.uniform(10, 300)
            change = rng.uniform(-8, 8)
            volume = rng.randint(50_000, 10_000_000)
            quotes.append(
                MarketQuote(
                    symbol=symbol.upper(),
                    price=round(base * (1 + change / 100), 2),
                    change_pct=round(change, 2),
                    volume=volume,
                )
            )
        return quotes


class MarketDataAdapterFactory:
    @staticmethod
    def create(provider: str = "mock") -> MockMarketDataAdapter:
        # 这里可以扩展：provider == "akshare" / "tushare" / "yfinance" / "ads_api" 等
        return MockMarketDataAdapter()
