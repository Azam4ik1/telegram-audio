import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from categories import detect_by_keywords
from parser import fmt, parse_line


def test_parse_line_amount_before_note():
    assert parse_line("50 такси") == (50.0, "такси")


def test_parse_line_amount_after_note():
    assert parse_line("плов 35") == (35.0, "плов")


def test_parse_line_thousand_suffix():
    assert parse_line("1.5к аренда") == (1500.0, "аренда")
    assert parse_line("1к зарплата") == (1000.0, "зарплата")


def test_parse_line_comma_decimal():
    assert parse_line("кофе 12,5") == (12.5, "кофе")


def test_parse_line_note_starting_with_k_letter_is_not_a_suffix():
    assert parse_line("50 кофе") == (50.0, "кофе")


def test_parse_line_no_number_returns_none():
    assert parse_line("такси без суммы") is None


def test_parse_line_no_note_returns_none():
    assert parse_line("50") is None


def test_detect_by_keywords_food():
    assert detect_by_keywords("плов") == "🍔 Еда"


def test_detect_by_keywords_transport():
    assert detect_by_keywords("такси") == "🚕 Транспорт"


def test_detect_by_keywords_unknown_returns_none():
    assert detect_by_keywords("неизвестное слово") is None


def test_fmt_integer():
    assert fmt(1500.0) == "1 500"


def test_fmt_decimal_trims_trailing_zero():
    assert fmt(12.5) == "12.5"


def test_fmt_large_number():
    assert fmt(1000000) == "1 000 000"
