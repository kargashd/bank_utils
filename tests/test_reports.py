from datetime import datetime
from unittest.mock import mock_open, patch

import pandas as pd
import pytest

from src.reports import save_report_to_file, spending_by_category


def test_spending_by_category_empty_df():
    """Тест, проверяющий, что функция spending_by_category возвращает пустой словарь, если датафрейм пустой"""
    df = pd.DataFrame(columns=["Дата операции", "Категория", "Сумма платежа"])
    result = spending_by_category(df, "Супермаркеты", "2021-12-31")
    assert len(result) == 0
    assert isinstance(result, pd.DataFrame)


def test_spending_by_category_invalid_date():
    """Тест, проверяющий, что неверный формат даты вызывает ошибку"""
    df = pd.DataFrame(columns=["Дата операции", "Категория"])
    with pytest.raises(ValueError) as exc_info:
        spending_by_category(df, "Супермаркеты", "2021/12/31")
    assert "формате YYYY-MM-DD" in str(exc_info.value)


@patch("src.reports.datetime")
def test_spending_by_category_no_date(mock_datetime):
    """Тест проверяющий, что функция spending_by_category не вызывает ошибку, если дата не указана"""

    fixed_date = datetime(2024, 12, 31)
    mock_datetime.now.return_value = fixed_date

    data = {"Дата операции": ["01.12.2024 10:00:00"], "Категория": ["Супермаркеты"], "Сумма платежа": [500]}
    df = pd.DataFrame(data)

    result = spending_by_category(df, "Супермаркеты")

    assert len(result) == 1
    mock_datetime.now.assert_called_once()


@patch("builtins.open", new_callable=mock_open)
@patch("src.reports.logger")
def test_save_report_to_file_decorator(mock_logger, mock_file):
    """Тест проверяющий, что функция save_report_to_file сохраняет отчёт в файл"""

    @save_report_to_file("test_report.json")
    def test_func():
        return {"key": "value"}

    result = test_func()

    assert result == {"key": "value"}
    mock_file.assert_called_once_with("test_report.json", "w", encoding="utf-8")
    mock_logger.info.assert_called_with("Отчёт сохранён в файл: test_report.json")


@patch("builtins.open", new_callable=mock_open)
@patch("src.reports.logger")
def test_save_report_to_file_default_name(mock_logger, mock_file):
    """Тест проверяющий, что функция save_report_to_file сохраняет отчёт в файл с именем report.json"""

    @save_report_to_file()
    def test_func():
        return {"key": "value"}

    result = test_func()

    assert result == {"key": "value"}
    mock_file.assert_called_once_with("report.json", "w", encoding="utf-8")
