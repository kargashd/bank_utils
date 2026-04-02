import json
from unittest.mock import mock_open, patch
import pytest
import sys
import os
import pandas as pd
import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from utils import (
    load_user_settings,
    greeting,
    load_operations,
    get_cards_info,
    get_top_transactions,
    get_currency_rates,
    get_stock_prices
)


def test_load_user_settings_success(sample_settings):
    """Успешная загрузка настроек из валидного JSON-файла."""
    mock_file_content = json.dumps(sample_settings)
    m = mock_open(read_data=mock_file_content)

    with patch("builtins.open", m):
        result = load_user_settings("test_settings.json")

    assert result == sample_settings
    m.assert_called_once_with("test_settings.json", "r", encoding="utf-8")


def test_load_user_settings_file_not_found():
    """Ошибка при отсутствии файла настроек."""
    with patch("builtins.open", mock_open()) as m:
        m.side_effect = FileNotFoundError()

        with pytest.raises(FileNotFoundError):
            load_user_settings("nonexistent.json")


def test_load_user_settings_invalid_json():
    """Ошибка при невалидном JSON в файле настроек."""
    m = mock_open(read_data="invalid json {")

    with patch("builtins.open", m):
        with pytest.raises(json.JSONDecodeError):
            load_user_settings("invalid.json")


@pytest.mark.parametrize("time_str, expected", [
    ("2024-02-15 06:00:00", "Доброе утро"),
    ("2025-11-02 11:10:20", "Доброе утро"),
    ("2020-02-28 12:00:00", "Добрый день"),
    ("2021-07-05 15:35:18", "Добрый день"),
    ("2024-05-17 18:00:00", "Добрый вечер"),
    ("2024-10-13 22:59:59", "Добрый вечер"),
    ("2023-08-10 23:01:01", "Доброй ночи"),
    ("2020-09-25 05:59:59", "Доброй ночи"),
])
def test_greeting(time_str, expected):
    """Тест приветствия в зависимости от времени суток."""
    result = greeting(time_str)
    assert result == expected


def test_load_operations_success(sample_transactions_df):
    """Успешная загрузка транзакций из Excel-файла."""
    mock_df = sample_transactions_df

    with patch("utils.pd.read_excel") as mock_read_excel:
        mock_read_excel.return_value = mock_df
        result = load_operations("test_operations.xlsx")

    assert len(result) == 5
    assert result.equals(mock_df)
    mock_read_excel.assert_called_once_with("test_operations.xlsx")


def test_load_operations_file_not_found():
    """Ошибка при отсутствии Excel-файла."""
    with patch("utils.pd.read_excel") as mock_read_excel:
        mock_read_excel.side_effect = FileNotFoundError()

        with pytest.raises(FileNotFoundError):
            load_operations("nonexistent.xlsx")


def test_get_cards_info_multiple_cards(sample_transactions_df):
    """Проверка расчёта трат и кэшбэка по нескольким картам."""
    result = get_cards_info(sample_transactions_df, "2021-12-21 23:59:59")

    assert len(result) == 2

    card_5814 = next((c for c in result if c["last_digits"] == "14.0"), None)
    assert card_5814 is not None
    assert card_5814["total_spent"] == pytest.approx(2603.68, rel=0.01)
    assert card_5814["cashback"] == pytest.approx(26.04, rel=0.01)

    card_7512 = next((c for c in result if c["last_digits"] == "12.0"), None)
    assert card_7512 is not None
    assert card_7512["total_spent"] == pytest.approx(421.00, rel=0.01)
    assert card_7512["cashback"] == pytest.approx(4.21, rel=0.01)


def test_get_cards_info_filters_by_date(sample_transactions_df):
    """Проверка фильтрации транзакций по дате."""
    result = get_cards_info(sample_transactions_df, "2021-12-17 23:59:59")

    assert len(result) == 1
    assert result[0]["last_digits"] == "14.0"
    assert result[0]["total_spent"] == pytest.approx(576.45, rel=0.01)
    assert result[0]["cashback"] == pytest.approx(5.76, rel=0.01)


def test_get_cards_info_no_transactions(sample_transactions_df):
    """Проверка поведения при отсутствии транзакций за период."""
    result = get_cards_info(sample_transactions_df, "2021-12-01 23:59:59")

    assert result == []


def test_top_transactions_default_limit(sample_transactions_df):
    """Проверка топ-транзакций с лимитом по умолчанию."""
    result = get_top_transactions(sample_transactions_df, "2021-12-21 23:59:59")

    assert len(result) == 5
    assert result[0]["amount"] == 1198.23
    assert result[1]["amount"] == 829.00
    assert result[2]["amount"] == 453.00
    assert result[3]["amount"] == 421.00
    assert result[4]["amount"] == 123.45


def test_top_transactions_custom_limit(sample_transactions_df):
    """Проверка топ-транзакций с пользовательским лимитом."""
    result = get_top_transactions(sample_transactions_df, "2021-12-21 23:59:59", limit=3)

    assert len(result) == 3
    assert result[0]["amount"] == 1198.23
    assert result[1]["amount"] == 829.00
    assert result[2]["amount"] == 453.00


def test_top_transactions_date_format(sample_transactions_df):
    """Проверка формата даты в топ-транзакциях."""
    result = get_top_transactions(sample_transactions_df, "2021-12-21 23:59:59")

    for item in result:
        assert "." in item["date"]
        parts = item["date"].split(".")
        assert len(parts) == 3
        assert parts[0].isdigit()
        assert parts[1].isdigit()
        assert parts[2].isdigit()


def test_top_transactions_filters_by_date(sample_transactions_df):
    """Проверка фильтрации топ-транзакций по дате."""
    result = get_top_transactions(sample_transactions_df, "2021-12-17 23:59:59")

    assert len(result) == 2
    assert result[0]["amount"] == 453.00
    assert result[1]["amount"] == 123.45


def test_top_transactions_limit_greater_than_data(sample_transactions_df):
    """Проверка поведения когда лимит превышает количество данных."""
    result = get_top_transactions(sample_transactions_df, "2021-12-17 23:59:59", limit=10)

    assert len(result) == 2


@patch("utils.requests.get")
def test_get_currency_rates_success(mock_get, sample_currency_api_response):
    """Успешное получение курсов валют."""
    mock_response = mock_get.return_value
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = sample_currency_api_response

    result = get_currency_rates(["USD", "EUR"])

    assert len(result) == 2
    assert result[0]["currency"] == "USD"
    assert result[0]["rate"] == 73.21
    assert result[1]["currency"] == "EUR"
    assert result[1]["rate"] == 87.08


@patch("utils.requests.get")
def test_get_currency_rates_network_error(mock_get):
    """Обработка ошибки сети при получении курсов валют."""
    mock_get.side_effect = requests.RequestException()

    result = get_currency_rates(["USD"])

    assert result == []


@patch("utils.requests.get")
def test_get_currency_rates_partial_data(mock_get):
    """Обработка частичных данных при получении курсов валют."""
    mock_response = mock_get.return_value
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"Valute": {"USD": {"Value": 73.21}}}

    result = get_currency_rates(["USD", "EUR"])

    assert len(result) == 1
    assert result[0]["currency"] == "USD"
    assert result[0]["rate"] == 73.21


@patch("utils.requests.get")
def test_get_currency_rates_empty_currencies(mock_get):
    """Получение курсов валют с пустым списком."""
    mock_response = mock_get.return_value
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"Valute": {}}

    result = get_currency_rates([])

    assert result == []


@patch("utils.requests.get")
def test_get_currency_rates_http_error(mock_get):
    """Обработка HTTP ошибки при получении курсов валют."""
    mock_response = mock_get.return_value
    mock_response.raise_for_status.side_effect = requests.HTTPError()

    result = get_currency_rates(["USD"])

    assert result == []


@patch("utils.os.getenv")
@patch("utils.requests.get")
def test_get_stock_prices_success(mock_get, mock_getenv, sample_stock_api_response):
    """Успешное получение цены акции."""
    mock_getenv.return_value = "test_api_key"
    mock_response = mock_get.return_value
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = sample_stock_api_response

    result = get_stock_prices(["AAPL"])

    assert len(result) == 1
    assert result[0]["stock"] == "AAPL"
    assert result[0]["price"] == 150.12


@patch("utils.os.getenv")
@patch("utils.requests.get")
def test_get_stock_prices_multiple_stocks(mock_get, mock_getenv):
    """Получение цен нескольких акций."""
    mock_getenv.return_value = "test_api_key"

    def side_effect(url, **kwargs):
        mock = mock_get.return_value
        mock.raise_for_status.return_value = None
        if "AAPL" in url:
            mock.json.return_value = {"price": "150.12"}
        else:
            mock.json.return_value = {"price": "3173.18"}
        return mock

    mock_get.side_effect = side_effect

    result = get_stock_prices(["AAPL", "AMZN"])

    assert len(result) == 2
    assert result[0]["price"] == 150.12
    assert result[1]["price"] == 3173.18


@patch("utils.os.getenv")
@patch("utils.requests.get")
def test_get_stock_prices_network_error(mock_get, mock_getenv):
    """Обработка ошибки сети при получении цены акции."""
    mock_getenv.return_value = "test_api_key"
    mock_get.side_effect = requests.RequestException()

    result = get_stock_prices(["AAPL"])

    assert len(result) == 1
    assert result[0]["price"] == 0.0


@patch("utils.os.getenv")
@patch("utils.requests.get")
def test_get_stock_prices_invalid_response(mock_get, mock_getenv):
    """Обработка некорректного ответа API при получении цены акции."""
    mock_getenv.return_value = "test_api_key"
    mock_response = mock_get.return_value
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {}

    result = get_stock_prices(["AAPL"])

    assert len(result) == 1
    assert result[0]["price"] == 0.0


@patch("utils.os.getenv")
@patch("utils.requests.get")
def test_get_stock_prices_missing_api_key(mock_get, mock_getenv):
    """Обработка отсутствия API ключа при получении цены акции."""
    mock_getenv.return_value = None

    result = get_stock_prices(["AAPL"])

    assert len(result) == 1
    assert result[0]["stock"] == "AAPL"
    assert result[0]["price"] == 0.0
    mock_get.assert_not_called()


@patch("utils.os.getenv")
@patch("utils.requests.get")
def test_get_stock_prices_empty_stocks(mock_get, mock_getenv):
    """Получение цен акций с пустым списком."""
    mock_getenv.return_value = "test_api_key"

    result = get_stock_prices([])

    assert result == []
    mock_get.assert_not_called()
