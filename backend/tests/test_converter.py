"""
Tests for the DenominationConverter.

This module tests the converter layer which provides:
1. Currency conversion for stocks/ETFs (e.g., AAPL in EUR)
2. Cross-currency asset comparisons (e.g., AAPL vs VUSA.L)
3. Historical currency conversions
4. Historical cross-currency comparisons

The converter layer is separate from the fetcher layer and handles
all cross-currency operations for ALL asset types.
"""

import pytest
from datetime import datetime, timedelta
from src.price_service.converter import DenominationConverter, is_currency_code
from src.price_service.fetchers import YFinanceFetcher
from src.price_service.models import AssetType, SymbolNotFoundError


@pytest.fixture
def converter():
    """Create a DenominationConverter instance for tests."""
    fetchers = {'yfinance': YFinanceFetcher()}
    return DenominationConverter(fetchers)


@pytest.fixture
def fetcher():
    """Create a YFinanceFetcher instance for comparison tests."""
    return YFinanceFetcher()


class TestCurrencyCodeDetection:
    """Test the is_currency_code utility function."""

    def test_recognizes_currency_codes(self):
        """Test that common currency codes are recognized."""
        assert is_currency_code("USD") is True
        assert is_currency_code("EUR") is True
        assert is_currency_code("GBP") is True
        assert is_currency_code("JPY") is True
        assert is_currency_code("usd") is True  # Case insensitive

    def test_rejects_asset_symbols(self):
        """Test that asset symbols are not recognized as currencies."""
        assert is_currency_code("AAPL") is False
        assert is_currency_code("BTC") is False
        assert is_currency_code("BTC-USD") is False
        assert is_currency_code("VUSA.L") is False


class TestStockCurrencyConversion:
    """
    Test currency conversion for stocks/ETFs.

    This is the key functionality that was causing issues:
    - Stocks can only be fetched in their native currency at fetcher level
    - But converter provides currency conversion for stocks via forex rates
    """

    @pytest.mark.asyncio
    async def test_us_stock_to_eur(self, converter):
        """Test converting US stock (USD) to EUR."""
        result = await converter.convert_to_currency("AAPL", "EUR", AssetType.STOCK)

        assert result["symbol"] == "AAPL"
        assert result["native_currency"] == "USD"
        assert result["target_currency"] == "EUR"
        assert result["converted_price"] > 0
        assert result["forex_rate"] > 0
        assert result["conversion_method"] == "forex"
        assert "1 USD =" in result["interpretation"]

    @pytest.mark.asyncio
    async def test_uk_stock_to_usd(self, converter):
        """Test converting UK stock (GBP) to USD."""
        result = await converter.convert_to_currency("VUSA.L", "USD", AssetType.ETF)

        assert result["symbol"] == "VUSA.L"
        assert result["native_currency"] == "GBP"
        assert result["target_currency"] == "USD"
        assert result["converted_price"] > 0
        assert result["forex_rate"] > 0
        assert result["conversion_method"] == "forex"
        assert "1 GBP =" in result["interpretation"]

    @pytest.mark.asyncio
    async def test_same_currency_no_conversion(self, converter):
        """Test that no conversion happens when already in target currency."""
        result = await converter.convert_to_currency("AAPL", "USD", AssetType.STOCK)

        assert result["native_currency"] == "USD"
        assert result["target_currency"] == "USD"
        assert result["native_price"] == result["converted_price"]
        assert result["forex_rate"] == 1.0
        assert result["conversion_method"] == "direct"
        assert "already priced in USD" in result["interpretation"]

    @pytest.mark.asyncio
    async def test_uk_stock_same_currency(self, converter):
        """Test UK stock in its native GBP."""
        result = await converter.convert_to_currency("VUSA.L", "GBP", AssetType.ETF)

        assert result["native_currency"] == "GBP"
        assert result["target_currency"] == "GBP"
        assert result["conversion_method"] == "direct"

    @pytest.mark.asyncio
    async def test_invalid_target_currency(self, converter):
        """Test that invalid currency raises appropriate error."""
        with pytest.raises(Exception):  # Should raise APIError for invalid forex pair
            await converter.convert_to_currency("AAPL", "XYZ")


class TestFetcherVsConverterBehavior:
    """
    Test the key difference between fetcher and converter layers.

    This documents the architectural decision:
    - Fetcher: Native currency only for stocks, validates explicit requests
    - Converter: Currency conversion for all asset types
    """

    @pytest.mark.asyncio
    async def test_fetcher_rejects_stock_currency_request(self, fetcher):
        """
        Test that fetcher-level rejects stock with non-native currency.

        This is the validation we added to prevent confusion.
        """
        with pytest.raises(SymbolNotFoundError) as exc_info:
            await fetcher.fetch_price("AAPL", AssetType.STOCK, currency="EUR")

        error_msg = str(exc_info.value)
        assert "not available at fetcher level" in error_msg
        assert "convert_to_currency" in error_msg

    @pytest.mark.asyncio
    async def test_converter_allows_stock_currency_conversion(self, converter):
        """
        Test that converter-level allows stock currency conversion.

        This is the correct way to get AAPL in EUR.
        """
        result = await converter.convert_to_currency("AAPL", "EUR")

        assert result["target_currency"] == "EUR"
        assert result["conversion_method"] == "forex"

    @pytest.mark.asyncio
    async def test_fetcher_allows_stock_default_currency(self, fetcher):
        """Test that fetcher allows stock with no currency (returns native)."""
        price = await fetcher.fetch_price("AAPL", AssetType.STOCK)

        assert price.currency == "USD"
        assert price.price > 0


class TestCrossCurrencyAssetComparison:
    """
    Test comparing assets across different currencies.

    Example: AAPL (USD) vs VUSA.L (GBP)
    The converter normalizes both to a common currency for comparison.
    """

    @pytest.mark.asyncio
    async def test_us_vs_uk_stock(self, converter):
        """Test comparing US stock (USD) vs UK stock (GBP)."""
        result = await converter.convert(
            "AAPL", "VUSA.L",
            asset_type=AssetType.STOCK,
            denomination_type=AssetType.ETF
        )

        assert result["asset_symbol"] == "AAPL"
        assert result["denomination_symbol"] == "VUSA.L"
        assert result["asset_currency"] == "USD"
        assert result["denomination_currency"] == "GBP"
        assert result["common_currency"] == "USD"  # Normalized to USD
        assert result["conversion_method"] == "triangular"
        assert result["ratio"] > 0
        assert result["inverse_ratio"] > 0

    @pytest.mark.asyncio
    async def test_same_currency_direct_comparison(self, converter):
        """Test comparing assets in the same currency (no normalization needed)."""
        result = await converter.convert(
            "AAPL", "MSFT",
            asset_type=AssetType.STOCK,
            denomination_type=AssetType.STOCK
        )

        assert result["asset_currency"] == "USD"
        assert result["denomination_currency"] == "USD"
        assert result["common_currency"] == "USD"
        assert result["conversion_method"] == "direct"  # No triangulation needed

    @pytest.mark.asyncio
    async def test_crypto_with_different_currencies(self, converter):
        """Test crypto comparison with explicit different currencies."""
        result = await converter.convert(
            "BTC", "ETH",
            asset_type=AssetType.CRYPTO,
            denomination_type=AssetType.CRYPTO,
            asset_currency="EUR",
            denomination_currency="GBP"
        )

        assert result["conversion_method"] == "triangular"
        assert result["common_currency"] == "USD"


class TestHistoricalCurrencyConversion:
    """Test historical currency conversion for stocks."""

    @pytest.mark.asyncio
    async def test_historical_stock_currency_conversion(self, converter):
        """Test converting historical stock prices to different currency."""
        end = datetime.now()
        start = end - timedelta(days=7)

        result = await converter.convert_to_currency_historical(
            "AAPL", "EUR", start, end, "1d", AssetType.STOCK
        )

        assert result["symbol"] == "AAPL"
        assert result["native_currency"] == "USD"
        assert result["target_currency"] == "EUR"
        assert result["conversion_method"] == "forex_historical"  # Uses historical forex rates
        assert result["count"] >= 4  # At least 4 trading days in a week
        assert len(result["data"]) >= 4

        # Check data points - each should have its own historical forex rate
        for point in result["data"]:
            assert point["native_currency"] == "USD"
            assert point["target_currency"] == "EUR"
            assert point["converted_price"] > 0
            assert point["forex_rate"] > 0  # Each point has historical rate for that date

    @pytest.mark.asyncio
    async def test_historical_same_currency(self, converter):
        """Test historical with same currency (no conversion)."""
        end = datetime.now()
        start = end - timedelta(days=7)

        result = await converter.convert_to_currency_historical(
            "AAPL", "USD", start, end, "1d"
        )

        assert result["conversion_method"] == "direct"
        assert all(p["forex_rate"] == 1.0 for p in result["data"])


class TestHistoricalCrossCurrencyComparison:
    """Test historical cross-currency asset comparisons."""

    @pytest.mark.asyncio
    async def test_historical_cross_currency_ratio(self, converter):
        """Test historical ratio with cross-currency normalization."""
        end = datetime.now()
        start = end - timedelta(days=7)

        result = await converter.convert_historical(
            "AAPL", "VUSA.L",
            start, end, "1d",
            asset_type=AssetType.STOCK,
            denomination_type=AssetType.ETF
        )

        assert result["asset_symbol"] == "AAPL"
        assert result["denomination_symbol"] == "VUSA.L"
        assert result["conversion_method"] == "triangular"
        assert result["common_currency"] == "USD"
        assert result["count"] >= 4  # At least 4 trading days in a week

        # Check data points have normalized prices
        for point in result["data"]:
            assert point["asset_currency"] == "USD"
            assert point["denomination_currency"] == "GBP"
            assert point["common_currency"] == "USD"
            assert point["asset_price_normalized"] > 0
            assert point["denomination_price_normalized"] > 0
            assert point["ratio"] > 0

    @pytest.mark.asyncio
    async def test_historical_same_currency_direct(self, converter):
        """Test historical ratio with same currency (direct)."""
        end = datetime.now()
        start = end - timedelta(days=7)

        result = await converter.convert_historical(
            "AAPL", "MSFT",
            start, end, "1d",
            asset_type=AssetType.STOCK,
            denomination_type=AssetType.STOCK
        )

        assert result["conversion_method"] == "direct"
        assert result["common_currency"] == "USD"


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_invalid_symbol(self, converter):
        """Test that invalid symbols raise appropriate errors."""
        with pytest.raises(SymbolNotFoundError):
            await converter.convert_to_currency("INVALID123", "EUR")

    @pytest.mark.asyncio
    async def test_crypto_currency_conversion(self, converter):
        """Test that crypto can also use currency conversion."""
        result = await converter.convert_to_currency("BTC", "EUR", AssetType.CRYPTO)

        # For crypto, fetcher might support direct BTC-EUR
        # So conversion_method could be "direct" or "forex" depending on implementation
        assert result["target_currency"] == "EUR"
        assert result["converted_price"] > 0


# Pytest configuration
def pytest_configure(config):
    """Add custom markers."""
    config.addinivalue_line(
        "markers",
        "converter: mark test as testing converter functionality"
    )
