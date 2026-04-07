import json
import pytest
from unittest.mock import patch, MagicMock
from src.services import *


def test_normal(sample_transaction_list):
    """Тест, проверяющий нормальную работу функции"""
    result = profitable_cashback_categories(2021, 12, sample_transaction_list)
    data = json.loads(result)

    assert data["Супермаркеты"] == 8.29
    assert data["Переводы"] == 11.98
    assert len(data) == 5


@patch("src.services.logger")
def test_empty_transactions(mock_logger):
    """Тест, проверяющий работу функции при пустом списке транзакций"""
    result = profitable_cashback_categories(2021, 12, [])
    data = json.loads(result)

    assert data == {}
    mock_logger.warning.assert_called_with("Список транзакций пуст")


@patch("src.services.logger")
def test_invalid_month(mock_logger):
    """Тест проверяющий работу функции при неверном месяце"""
    with pytest.raises(ValueError) as exc_info:
        profitable_cashback_categories(2021, 13, [])

        assert "Месяцы должны быть в диапозоне от 1 до 12" in str(exc_info.value)
        mock_logger.error.assert_called_with("Неверный месяц 13")


@patch("src.services.logger")
def test_missing_category(mock_logger):
    """Тест проверяющий работу функции при отсутствии категории"""
    transactions = [
        {
            "Дата операции": "2021-12-21 10:00:00",
            "Статус": "ОК",
            "Кэшбэк": 10.00
        },
    ]

    result = profitable_cashback_categories(2021, 12, transactions)
    data = json.loads(result)

    assert data["Без категории"] == 10.00
    mock_logger.debug.assert_called()
