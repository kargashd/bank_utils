import json
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Optional

import pandas as pd

logger = logging.getLogger(__name__)


def save_report_to_file(filename: Optional[str] = None) -> Callable:
    """Декоратор для сохранения результата функции-отчёта в файл"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)

            output_filename = filename if filename else "report.json"

            if isinstance(result, pd.DataFrame):
                data = result.to_dict(orient="records")
                json_data = json.dumps(data, ensure_ascii=False, indent=2, default=str)
            elif isinstance(result, (dict, list)):
                json_data = json.dumps(result, ensure_ascii=False, indent=2, default=str)
            else:
                json_data = str(result)

            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(json_data)

            logger.info(f"Отчёт сохранён в файл: {output_filename}")

            return result

        return wrapper

    return decorator


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


@save_report_to_file()
def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> pd.DataFrame:
    """Возвращаем траты по категории за последние 3 месяца"""

    logger.info(f"Расчёт трат по категории: {category}, дата отсчёта: {date}")

    if date is None:
        end_date = datetime.now()
        logger.info(f"Дата отсчёта не передана, используется текущая дата")
    else:
        try:
            end_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            logger.error(f"Неверный формат даты {date}")
            raise ValueError("Дата должна быть в формате YYYY-MM-DD")

    start_date = end_date - timedelta(days=90)
    logger.info(f"Период: {start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}")

    df = transactions.copy()
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["Дата операции"])

    result = df[
        (df["Дата операции"] >= start_date) & (df["Дата операции"] <= end_date) & (df["Категория"] == category)
    ]

    logger.info(f"Найдено {len(result)} транзакций по категории '{category}'")
    return result
