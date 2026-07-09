import pytest
from app.utils.date import (
    current_period,
    format_period,
    parse_period,
    period_range,
)
from datetime import datetime, timezone


def test_current_period_format():
    period = current_period()
    assert len(period) == 7
    assert period[4] == "-"
    year, month = period.split("-")
    assert year.isdigit()
    assert month.isdigit()
    assert 1 <= int(month) <= 12


def test_format_period():
    dt = datetime(2025, 6, 15, tzinfo=timezone.utc)
    assert format_period(dt) == "2025-06"


def test_parse_period_valid():
    year, month = parse_period("2025-06")
    assert year == 2025
    assert month == 6


def test_parse_period_invalid_raises():
    with pytest.raises(ValueError):
        parse_period("2025/06")

    with pytest.raises(ValueError):
        parse_period("June 2025")


def test_period_range_single():
    result = period_range("2025-06", "2025-06")
    assert result == ["2025-06"]


def test_period_range_within_year():
    result = period_range("2025-01", "2025-03")
    assert result == ["2025-01", "2025-02", "2025-03"]


def test_period_range_across_year():
    result = period_range("2024-11", "2025-02")
    assert result == ["2024-11", "2024-12", "2025-01", "2025-02"]


def test_period_range_reversed_returns_empty():
    result = period_range("2025-06", "2025-03")
    assert result == []