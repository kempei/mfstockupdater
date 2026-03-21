"""
株価・為替データプロバイダーモジュール

AlphaVantage と Financial Modeling Prep (FMP) をサポートし、
環境変数 STOCK_PROVIDER で切り替え可能。
"""

from abc import ABC, abstractmethod
from logzero import logger
import requests
import os


class StockProvider(ABC):
    """株価・為替データプロバイダーの基底クラス"""

    @abstractmethod
    def stock_price(self, tick: str) -> float:
        """指定ティッカーの株価を取得する"""
        pass

    @abstractmethod
    def usdrate(self) -> float:
        """USD/JPY為替レートを取得する"""
        pass


class AlphaVantageProvider(StockProvider):
    """AlphaVantage APIを使用した株価・為替データプロバイダー"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.stock_price_cache: dict[str, float] = dict()

    def stock_price(self, tick: str) -> float:
        if tick not in self.stock_price_cache:
            for retry in range(3):
                r = requests.get(
                    f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={tick}&apikey={self.api_key}"
                )
                if r.status_code != 200:
                    raise ConnectionRefusedError()
                data = r.json()
                if "Global Quote" in data:
                    self.stock_price_cache[tick] = float(data["Global Quote"]["05. price"])
                    break
        return self.stock_price_cache[tick]

    def usdrate(self) -> float:
        r = requests.get(
            f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=USD&to_currency=JPY&apikey={self.api_key}"
        )
        if r.status_code != 200:
            raise ConnectionRefusedError()
        data = r.json()
        return float(data["Realtime Currency Exchange Rate"]["5. Exchange Rate"])


class FMPProvider(StockProvider):
    """Financial Modeling Prep APIを使用した株価・為替データプロバイダー"""

    BASE_URL = "https://financialmodelingprep.com/stable"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.stock_price_cache: dict[str, float] = dict()

    def stock_price(self, tick: str) -> float:
        if tick not in self.stock_price_cache:
            for retry in range(3):
                r = requests.get(
                    f"{self.BASE_URL}/quote-short?symbol={tick}&apikey={self.api_key}"
                )
                if r.status_code != 200:
                    raise ConnectionRefusedError(
                        f"FMP APIリクエスト失敗: ステータスコード {r.status_code}"
                    )
                data = r.json()
                if isinstance(data, list) and len(data) > 0 and "price" in data[0]:
                    self.stock_price_cache[tick] = float(data[0]["price"])
                    break
                logger.warning(f"FMP APIから{tick}の株価を取得できませんでした。リトライ {retry + 1}/3")
        return self.stock_price_cache[tick]

    def usdrate(self) -> float:
        r = requests.get(
            f"{self.BASE_URL}/quote?symbol=USDJPY&apikey={self.api_key}"
        )
        if r.status_code != 200:
            raise ConnectionRefusedError(
                f"FMP為替APIリクエスト失敗: ステータスコード {r.status_code}"
            )
        data = r.json()
        if isinstance(data, list) and len(data) > 0 and "price" in data[0]:
            return float(data[0]["price"])
        raise ValueError("FMP APIからUSD/JPY為替レートを取得できませんでした")


def create_provider() -> StockProvider:
    """
    環境変数 STOCK_PROVIDER に基づいてプロバイダーを生成する。
    - "fmp": Financial Modeling Prep (FMP_API_KEY 環境変数が必要)
    - "alphavantage" (デフォルト): AlphaVantage (ALPHAVANTAGE_API_KEY 環境変数が必要)
    """
    provider_name = os.environ.get("STOCK_PROVIDER", "alphavantage").lower()

    if provider_name == "fmp":
        if "FMP_API_KEY" not in os.environ:
            raise ValueError("環境変数 FMP_API_KEY が設定されていません。")
        logger.info("株価プロバイダー: Financial Modeling Prep (FMP)")
        return FMPProvider(os.environ["FMP_API_KEY"])
    else:
        if "ALPHAVANTAGE_API_KEY" not in os.environ:
            raise ValueError("環境変数 ALPHAVANTAGE_API_KEY が設定されていません。")
        logger.info("株価プロバイダー: AlphaVantage")
        return AlphaVantageProvider(os.environ["ALPHAVANTAGE_API_KEY"])
