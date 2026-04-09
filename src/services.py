import json
import logging
from collections import defaultdict
from datetime import datetime
from typing import Any

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

logger = logging.getLogger(__name__)

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def profitable_cashback_categories(year: int, month: int, transactions: list[dict[str, Any]]) -> str:
    """Функция рассчитывает сумму кешбэка по каждой категории за указанный месяц"""

    logger.info(f"Расчёт кэшбэка за {month:02d}.{year}")

    if not 1 <= month <= 12:
        logger.error(f"Неверный месяц {month}")
        raise ValueError("Месяцы должны быть в диапозоне от 1 до 12")

    if not transactions:
        logger.warning("Список транзакций пуст")
        return json.dumps({}, ensure_ascii=False, indent=2)

    logger.info(f"Начало расчёта кэшбэка за {month:02d}.{year}")
    logger.debug(f"Количество транзакций: {len(transactions)}")

    cashback: dict[str, float] = defaultdict(float)

    processed = 0
    skipped_no_date = 0
    skipped_wrong_date = 0
    skipped_wrong_status = 0
    skipped_wrong_cashback = 0

    for transaction in transactions:

        try:
            dt = datetime.strptime(transaction.get("Дата операции", ""), DATE_FORMAT)

        except (ValueError, KeyError):
            logger.warning(
                f"Пропущена транзакция с некорреткной датой: {transaction.get('Дата операции', 'отсутствует')}"
            )
            skipped_no_date += 1
            continue

        if dt.year != year or dt.month != month:
            continue

        if transaction.get("Статус") != "ОК":
            skipped_wrong_status += 1
            continue

        category = transaction.get("Категория", "Без категории")
        cashback_value = transaction.get("Кэшбэк", 0)

        if not isinstance(cashback_value, (int, float)):
            logger.warning(f"Пропущена транзакция с некорректным кэшбэком: {cashback_value}")
            skipped_wrong_cashback += 1
            continue

        cashback[category] += cashback_value
        processed += 1
        logger.debug(f"Категория '{category}': +{cashback_value} (всего {cashback[category]:.2f})")

    logger.info(f"Обработано транзакций: {processed}")
    logger.debug(f"Пропущено (нет даты): {skipped_no_date}")
    logger.debug(f"Пропущено (неверный статус): {skipped_wrong_status}")
    logger.debug(f"Пропущено (неверный кешбэк): {skipped_wrong_cashback}")

    sorted_cashback = dict(sorted(cashback.items(), key=lambda x: x[1], reverse=True))
    result = {k: round(v, 2) for k, v in sorted_cashback.items()}

    logger.info(f"Рассчитано категорий: {len(result)}")

    return json.dumps(result, ensure_ascii=False, indent=2)
