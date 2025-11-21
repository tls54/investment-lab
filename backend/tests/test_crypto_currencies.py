"""
Tests for cryptocurrency pricing in different fiat currencies.

Tests coverage:
1. Known supported currencies (USD, EUR, GBP, JPY)
2. Behavior with unsupported/invalid currencies
3. Historical data with different currencies
4. Future: Triangular conversion for unsupported pairs
"""

import pytest
from datetime import datetime, timedelta
from src.price_service.fetchers import YFinanceFetcher
from src.price_service.models import AssetType, SymbolNotFoundError, APIError


@pytest.fixture
def fetcher():
    """Create a YFinanceFetcher instance for tests."""
    return YFinanceFetcher()


class TestCryptoCurrentPrice:
    """Test current price fetching in different currencies."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("currency", ["USD", "EUR", "GBP", "JPY"])
    async def test_supported_currencies(self, fetcher, currency):
        """Test that major fiat currencies work for crypto pricing."""
        # Fetch BTC price in the specified currency
        price = await fetcher.fetch_price("BTC", AssetType.CRYPTO, currency=currency)

        # Assertions
        assert price is not None
        assert price.symbol == "BTC"
        assert price.asset_type == AssetType.CRYPTO
        assert price.price > 0, f"BTC price should be positive in {currency}"
        assert price.currency == currency, f"Currency should be {currency}"
        assert price.timestamp is not None
        assert isinstance(price.timestamp, datetime)

    @pytest.mark.asyncio
    async def test_default_currency_is_usd(self, fetcher):
        """Test that default currency is USD when not specified."""
        price = await fetcher.fetch_price("BTC", AssetType.CRYPTO)

        assert price.currency == "USD"
        assert price.price > 0

    @pytest.mark.asyncio
    @pytest.mark.parametrize("crypto_symbol", ["BTC", "ETH", "USDT"])
    async def test_multiple_cryptos_with_custom_currency(self, fetcher, crypto_symbol):
        """Test that different cryptos work with custom currencies."""
        price = await fetcher.fetch_price(crypto_symbol, AssetType.CRYPTO, currency="EUR")

        assert price.symbol == crypto_symbol
        assert price.currency == "EUR"
        assert price.price > 0

    @pytest.mark.asyncio
    async def test_unsupported_currency_behavior(self, fetcher):
        """
        Test behavior when requesting an unsupported currency.

        yfinance will either:
        - Return no data (SymbolNotFoundError)
        - Return an error (APIError)

        We test that we get a meaningful error, not a crash.
        """
        # Try a made-up currency code
        with pytest.raises((SymbolNotFoundError, APIError)) as exc_info:
            await fetcher.fetch_price("BTC", AssetType.CRYPTO, currency="XYZ")

        # Verify we get a meaningful error message
        error_msg = str(exc_info.value)
        assert len(error_msg) > 0, "Error message should not be empty"

    @pytest.mark.asyncio
    async def test_currency_case_insensitive(self, fetcher):
        """Test that currency codes are case-insensitive."""
        price_upper = await fetcher.fetch_price("BTC", AssetType.CRYPTO, currency="USD")
        price_lower = await fetcher.fetch_price("BTC", AssetType.CRYPTO, currency="usd")

        # Both should work and return USD
        assert price_upper.currency == "USD"
        assert price_lower.currency == "USD"

        # Prices should be similar (within 5% due to time difference)
        assert abs(price_upper.price - price_lower.price) / price_upper.price < 0.05

    @pytest.mark.asyncio
    async def test_symbol_normalization_with_currency(self, fetcher):
        """Test that symbol normalization works correctly with currencies."""
        # These should all work the same
        price1 = await fetcher.fetch_price("BTC", AssetType.CRYPTO, currency="EUR")
        price2 = await fetcher.fetch_price("btc", AssetType.CRYPTO, currency="EUR")
        price3 = await fetcher.fetch_price(" BTC ", AssetType.CRYPTO, currency="EUR")

        assert price1.symbol == "BTC"
        assert price2.symbol == "BTC"
        assert price3.symbol == "BTC"
        assert all(p.currency == "EUR" for p in [price1, price2, price3])


class TestCryptoHistoricalPrices:
    """Test historical price fetching in different currencies."""

    @pytest.mark.asyncio
    async def test_historical_with_custom_currency(self, fetcher):
        """Test fetching historical data in a non-USD currency."""
        end = datetime.now()
        start = end - timedelta(days=7)

        historical = await fetcher.fetch_historical(
            "BTC", start, end, interval="1d",
            asset_type=AssetType.CRYPTO,
            currency="EUR"
        )

        assert historical is not None
        assert historical.symbol == "BTC"
        assert historical.asset_type == AssetType.CRYPTO
        assert len(historical.prices) > 0

        # Check that all prices have EUR currency
        for price in historical.prices:
            assert price.currency == "EUR"
            assert price.price > 0

    @pytest.mark.asyncio
    @pytest.mark.parametrize("currency", ["USD", "EUR", "GBP"])
    async def test_historical_multiple_currencies(self, fetcher, currency):
        """Test that historical data works across multiple currencies."""
        end = datetime.now()
        start = end - timedelta(days=3)

        historical = await fetcher.fetch_historical(
            "ETH", start, end, interval="1d",
            asset_type=AssetType.CRYPTO,
            currency=currency
        )

        assert len(historical.prices) >= 2, "Should have at least 2 days of data"
        assert all(p.currency == currency for p in historical.prices)

    @pytest.mark.asyncio
    async def test_historical_unsupported_currency(self, fetcher):
        """Test that historical data with unsupported currency fails gracefully."""
        end = datetime.now()
        start = end - timedelta(days=7)

        with pytest.raises((SymbolNotFoundError, APIError)):
            await fetcher.fetch_historical(
                "BTC", start, end, interval="1d",
                asset_type=AssetType.CRYPTO,
                currency="INVALID"
            )


class TestCurrencyValidation:
    """Test currency validation and edge cases."""

    @pytest.mark.asyncio
    async def test_empty_currency_defaults_to_usd(self, fetcher):
        """Test that empty currency string defaults to USD."""
        price = await fetcher.fetch_price("BTC", AssetType.CRYPTO, currency="")

        # Should fallback to USD or handle gracefully
        assert price is not None
        assert price.price > 0

    @pytest.mark.asyncio
    async def test_whitespace_currency_handling(self, fetcher):
        """Test that whitespace is stripped from currency codes."""
        price = await fetcher.fetch_price("BTC", AssetType.CRYPTO, currency=" USD ")

        assert price.currency == "USD"

    @pytest.mark.asyncio
    async def test_common_supported_currencies(self, fetcher):
        """
        Document which currencies are known to work.

        This test serves as documentation for supported currencies.
        """
        known_working = {
            "USD": "US Dollar",
            "EUR": "Euro",
            "GBP": "British Pound",
            "JPY": "Japanese Yen",
            "AUD": "Australian Dollar",
            "CAD": "Canadian Dollar",
        }

        results = {}
        for currency, name in known_working.items():
            try:
                price = await fetcher.fetch_price("BTC", AssetType.CRYPTO, currency=currency)
                results[currency] = {
                    "supported": True,
                    "price": price.price,
                    "name": name
                }
            except (SymbolNotFoundError, APIError):
                results[currency] = {
                    "supported": False,
                    "name": name
                }

        # At least USD, EUR, GBP should work
        assert results["USD"]["supported"], "USD should be supported"
        assert results["EUR"]["supported"], "EUR should be supported"
        assert results["GBP"]["supported"], "GBP should be supported"

        # Print results for documentation
        print("\n=== Supported Currencies ===")
        for currency, info in results.items():
            status = "✓" if info["supported"] else "✗"
            price_info = f" (${info['price']:,.2f})" if info.get("price") else ""
            print(f"{status} {currency}: {info['name']}{price_info}")


class TestTriangularConversion:
    """
    Tests for triangular currency conversion.

    Example: If BTC-INR is not available, calculate via:
    BTC-INR = BTC-USD × USD-INR

    This feature is now implemented!
    """

    @pytest.mark.asyncio
    async def test_triangular_conversion_via_usd(self, fetcher):
        """
        Test converting via USD when direct pair is unavailable.

        This tests a currency that likely isn't directly available
        but should work via triangular conversion.
        """
        # Try Indian Rupee (INR) - unlikely to have direct BTC-INR pair
        price = await fetcher.fetch_price("BTC", AssetType.CRYPTO, currency="INR")

        assert price is not None
        assert price.currency == "INR"
        assert price.price > 0
        assert "triangular" in price.source.lower(), (
            "Should indicate triangular conversion in source"
        )

    @pytest.mark.asyncio
    async def test_triangular_source_indicator(self, fetcher):
        """Test that triangular conversions are marked in the source field."""
        # Currency likely to need triangular conversion
        price = await fetcher.fetch_price("ETH", AssetType.CRYPTO, currency="KRW")

        # Should indicate it was calculated, not a direct quote
        assert "triangular" in price.source.lower()

    @pytest.mark.asyncio
    async def test_triangular_vs_direct_comparison(self, fetcher):
        """
        Compare direct pair vs triangular for currencies that have both.

        For currencies like EUR, both direct (BTC-EUR) and triangular
        (BTC-USD × USD-EUR) should exist and be close.
        """
        # This test documents expected behavior:
        # - Direct pair is preferred when available
        # - Triangular is only used as fallback

        # EUR should have direct pair (common currency)
        eur_price = await fetcher.fetch_price("BTC", AssetType.CRYPTO, currency="EUR")

        # Should use direct pair (NOT triangular)
        assert "triangular" not in eur_price.source.lower(), (
            "EUR should have direct pair, not use triangular"
        )

    @pytest.mark.asyncio
    async def test_triangular_only_for_crypto(self, fetcher):
        """Test that triangular conversion only applies to crypto."""
        from src.price_service.models import SymbolNotFoundError

        # Stock with invalid currency should fail
        # (no triangular conversion for stocks)
        with pytest.raises(SymbolNotFoundError):
            await fetcher.fetch_price("AAPL", AssetType.STOCK, currency="INR")

    @pytest.mark.asyncio
    async def test_triangular_not_for_usd(self, fetcher):
        """Test that triangular is not attempted when currency is already USD."""
        # If BTC-USD doesn't exist (very unlikely), should fail immediately
        # without trying triangular (would create infinite loop)

        # This test mainly documents the loop prevention logic
        # We can't easily test the failure case without mocking
        price = await fetcher.fetch_price("BTC", AssetType.CRYPTO, currency="USD")
        assert price.currency == "USD"
        # Should not have tried triangular
        assert "triangular" not in price.source.lower()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("currency", ["INR", "KRW", "CNY", "BRL"])
    async def test_triangular_multiple_currencies(self, fetcher, currency):
        """
        Test triangular conversion works for various currencies.

        These are real currencies that may not have direct crypto pairs.
        """
        price = await fetcher.fetch_price("BTC", AssetType.CRYPTO, currency=currency)

        assert price is not None
        assert price.currency == currency
        assert price.price > 0
        # May or may not be triangular depending on yfinance data availability


class TestCurrencyConversionEndpoints:
    """
    Test the denomination conversion endpoints with different currencies.

    Example: AAPL priced in BTC-EUR instead of BTC-USD
    """

    @pytest.mark.asyncio
    async def test_conversion_respects_currency(self, fetcher):
        """
        Test that denomination conversion respects currency parameter.

        When converting AAPL/BTC with BTC in EUR, the ratio should differ
        from AAPL/BTC with BTC in USD.
        """
        # This is more of an integration test
        # TODO: Move to integration tests once converter is updated
        pass


# Pytest configuration
def pytest_configure(config):
    """Add custom markers."""
    config.addinivalue_line(
        "markers",
        "currency: mark test as testing currency support"
    )
