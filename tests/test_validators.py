"""Unit tests for all validator functions."""
import pytest
from src.utils.validators import validate_ticker, validate_quantity, validate_price, validate_score


class TestValidateTicker:
    def test_valid_ticker(self):
        assert validate_ticker("reliance") == "RELIANCE"

    def test_valid_ticker_with_hyphen(self):
        assert validate_ticker("m-m") == "M-M"

    def test_empty_ticker_raises(self):
        with pytest.raises(ValueError):
            validate_ticker("")

    def test_none_ticker_raises(self):
        with pytest.raises(ValueError):
            validate_ticker(None)

    def test_whitespace_stripped(self):
        assert validate_ticker("  INFY  ") == "INFY"


class TestValidateQuantity:
    def test_valid_quantity(self):
        assert validate_quantity(10) == 10

    def test_string_quantity_converted(self):
        assert validate_quantity("5") == 5

    def test_zero_raises(self):
        with pytest.raises(ValueError):
            validate_quantity(0)

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            validate_quantity(-1)

    def test_non_numeric_raises(self):
        with pytest.raises(ValueError):
            validate_quantity("abc")


class TestValidatePrice:
    def test_valid_price(self):
        assert validate_price(1500.50) == pytest.approx(1500.50)

    def test_string_price_converted(self):
        assert validate_price("2000") == pytest.approx(2000.0)

    def test_zero_price_raises(self):
        with pytest.raises(ValueError):
            validate_price(0)

    def test_negative_price_raises(self):
        with pytest.raises(ValueError):
            validate_price(-100)


class TestValidateScore:
    def test_valid_score_10(self):
        assert validate_score(10) == 10.0

    def test_valid_score_0(self):
        assert validate_score(0) == 0.0

    def test_score_above_10_raises(self):
        with pytest.raises(ValueError):
            validate_score(10.1)

    def test_score_below_0_raises(self):
        with pytest.raises(ValueError):
            validate_score(-0.1)

    def test_string_score_converted(self):
        assert validate_score("7.5") == pytest.approx(7.5)
