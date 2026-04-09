import json
import logging
from datetime import datetime
from typing import Any

import pandas as pd

from src.utils import (
    get_cards_info,
    get_currency_rates,
    get_stock_prices,
    get_top_transactions,
    greeting,
    load_operations,
    load_user_settings,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

logger = logging.getLogger(__name__)


def main_page(datetime_str: str) -> str:
    """Функция получения информации форматы JSON для главной страницы"""

    logger.info(f"Запрос главной страницы с датой {datetime_str}")
    try:
        datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        logger.error(f"Неверный формат даты {datetime_str}")
        raise ValueError("Дата должна быть в формате YYYY-MM-DD HH:MM:SS")

    df = load_operations()

    settings = load_user_settings()

    user_greeting = greeting(datetime_str)
    cards = get_cards_info(df, datetime_str)
    top_transactions = get_top_transactions(df, datetime_str)
    currency_rates = get_currency_rates(settings["user_currencies"])
    stock_prices = get_stock_prices(settings["user_stocks"])

    result: dict[str, Any] = {
        "greeting": user_greeting,
        "cards": cards,
        "top_transactions": top_transactions,
        "currency_rates": currency_rates,
        "stock_prices": stock_prices,
    }

    logger.info("Главная страница сформирована успешно")

    return json.dumps(result, ensure_ascii=False, indent=2)
