import json
from unittest.mock import patch

import pandas as pd
import pytest

from src.views import main_page


@patch("src.views.get_top_transactions")
@patch("src.views.get_cards_info")
@patch("src.views.greeting")
@patch("src.views.get_stock_prices")
@patch("src.views.get_currency_rates")
@patch("src.views.load_operations")
@patch("src.views.load_user_settings")
def test_main_page_returns_json(
    mock_settings, mock_operations, mock_currency, mock_stocks, mock_greeting, mock_cards, mock_top
):
    "Тест проверяет, что функция возвращает JSON строку"
    mock_operations.return_value = pd.DataFrame()
    mock_settings.return_value = {"user_currencies": [], "user_stocks": []}
    mock_greeting.return_value = "Добрый день"
    mock_cards.return_value = []
    mock_top.return_value = []
    mock_currency.return_value = []
    mock_stocks.return_value = []

    result = main_page("2024-01-01 12:00:00")

    assert isinstance(result, str)
    data = json.loads(result)
    assert isinstance(data, dict)


@patch("src.views.get_top_transactions")
@patch("src.views.get_cards_info")
@patch("src.views.greeting")
@patch("src.views.get_stock_prices")
@patch("src.views.get_currency_rates")
@patch("src.views.load_operations")
@patch("src.views.load_user_settings")
def test_main_page_has_required_keys(
    mock_settings, mock_operations, mock_currency, mock_stocks, mock_greeting, mock_cards, mock_top
):
    "Тест проверяет, что в получившемся JSON есть необходимые ключи"

    mock_operations.return_value = pd.DataFrame()
    mock_settings.return_value = {"user_currencies": [], "user_stocks": []}
    mock_currency.return_value = []
    mock_stocks.return_value = []
    mock_greeting.return_value = "Добрый день"
    mock_cards.return_value = []
    mock_top.return_value = []

    result = main_page("2024-01-01 12:00:00")
    data = json.loads(result)

    assert "greeting" in data
    assert "cards" in data
    assert "top_transactions" in data
    assert "currency_rates" in data
    assert "stock_prices" in data


@patch("src.views.get_top_transactions")
@patch("src.views.get_cards_info")
@patch("src.views.greeting")
@patch("src.views.get_stock_prices")
@patch("src.views.get_currency_rates")
@patch("src.views.load_operations")
@patch("src.views.load_user_settings")
def test_greeting_call_correct_data(
    mock_settings, mock_operations, mock_currency, mock_stocks, mock_greeting, mock_cards, mock_top
):
    """Тест проверяющий, что функция greeting вызывает корректную дату"""
    mock_operations.return_value = pd.DataFrame()
    mock_settings.return_value = {"user_currencies": [], "user_stocks": []}
    mock_operations.return_value = []
    mock_currency.return_value = []
    mock_stocks.return_value = []
    mock_greeting.return_value = "Добрый день"
    mock_cards.return_value = []
    mock_top.return_value = []

    main_page("2024-01-01 12:00:00")

    mock_greeting.assert_called_once_with("2024-01-01 12:00:00")


def test_main_page_invalid_date_format():
    """Тест, проверяющий, что функция main_page принимает дату в формате YYYY-MM-DD HH:MM:SS"""
    with pytest.raises(ValueError) as exc_info:
        main_page("2024-01-01")

    assert "Дата должна быть в формате YYYY-MM-DD HH:MM:SS" in str(exc_info.value)


def test_main_page_empty_date():
    """Тест првоеряет, что пустая дата вызовет ошибку"""
    with pytest.raises(ValueError):
        main_page("")
