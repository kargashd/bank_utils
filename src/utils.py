import json
import logging
import os
from datetime import datetime
from typing import Any

import pandas as pd
import requests
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

logger = logging.getLogger(__name__)

DATA_PATH = "../data/operations.xlsx"
SETTINGS_PATH = "../user_settings.json"
ENV_PATH = "../.env"

load_dotenv(ENV_PATH)


def load_operations(filepath: str = DATA_PATH) -> pd.DataFrame:
    """Загружает транзакции из Excel-файла."""
    df = pd.read_excel(filepath)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], errors="coerce")
    df = df.dropna(subset=["Дата операции"])

    logger.info(f"Загружено {len(df)} транзакции из {filepath}")
    return df


def load_user_settings(filepath: str = SETTINGS_PATH) -> dict[str, Any]:
    """Загружает пользовательские настройки из JSON-файла"""
    with open(filepath, "r", encoding="utf-8") as file:
        settings = json.load(file)
    logger.info(f"Загружены настройки: {settings}")
    return settings


def greeting(datetime_str: str) -> str:
    """Возвращает приветствие в зависимости о твремени суток"""
    dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
    hour = dt.hour

    if 6 <= hour < 12:
        result = "Доброе утро"
    elif 12 <= hour < 18:
        result = "Добрый день"
    elif 18 <= hour < 23:
        result = "Добрый вечер"
    else:
        result = "Доброй ночи"

    logger.info(f"Приветствие: {result}")
    return result


def get_cards_info(df: pd.DataFrame, date_str: str) -> list[dict[str, Any]]:
    """Возвращает список словарей с номером карты, суммой трат и кэшбэком за определённый период"""

    end_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    start_date = end_date.replace(day=1, hour=0, minute=0, second=0)

    df_filtered = df[(df["Дата операции"] >= start_date) & (df["Дата операции"] <= end_date) & (df["Статус"] == "OK")]

    cards = df_filtered.groupby("Номер карты").agg({"Сумма платежа": "sum", "Кэшбэк": "sum"}).reset_index()

    result = []
    for _, row in cards.iterrows():
        card_value = str(row["Номер карты"]) if not pd.isna(row["Номер карты"]) else ""
        card_number = card_value[-4:] if len(card_value) >= 4 else card_value

        result.append(
            {
                "last_digits": card_number,
                "total_spent": round(row["Сумма платежа"], 2),
                "cashback": round(row["Кэшбэк"], 2) if pd.notna(row["Кэшбэк"]) else 0.0,
            }
        )

    logger.info(f"Обработано карт:{len(result)}")
    return result


def get_top_transactions(df: pd.DataFrame, date_str: str, limit: int = 5) -> list[dict[str, Any]]:
    """Возвращает топ транзакций по сумме за период с начала месяца по указанную дату"""

    end_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    start_date = end_date.replace(day=1, hour=0, minute=0, second=0)

    df_filtered = df[(df["Дата операции"] >= start_date) & (df["Дата операции"] <= end_date) & (df["Статус"] == "OK")]

    df_top = df_filtered.nlargest(limit, "Сумма платежа")

    result = []

    for _, row in df_top.iterrows():
        date_val = row["Дата операции"]
        if isinstance(date_val, datetime):
            date_formated = date_val.strftime("%d.%m.%Y")
        else:
            date_formated = pd.to_datetime(date_val).strftime("%d.%m.%Y")

        result.append(
            {
                "date": date_formated,
                "amount": round(row["Сумма платежа"], 2),
                "category": row["Категория"],
                "description": row["Описание"],
            }
        )

    logger.info(f"Найдено топ-транзакций: {len(result)}")
    return result


def get_currency_rates(currencies: list[str]) -> list[dict[str, float]]:
    """Возвращает список словарей с валютой и курсом"""
    url = "https://www.cbr-xml-daily.ru/daily_json.js"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        result = []
        for currency in currencies:
            if currency in data["Valute"]:
                rate = data["Valute"][currency]["Value"]
                result.append(
                    {
                        "currency": currency,
                        "rate": round(rate, 2),
                    }
                )
            else:
                logger.warning(f"Валюта {currency} не найдена")

        logger.info(f"Получены курсы: {result}")
        return result

    except requests.RequestException as e:
        logger.error(f"Ошибка при получении курса валют {e}")
        return []


def get_stock_prices(stocks: list[str]) -> list[dict[str, float]]:
    """Возвращает список словарей с названиями акций и их ценами"""

    API_KEY = os.getenv("API_KEY_STOCK")
    BASE_URL = "https://api.twelvedata.com/price"
    result = []

    if not API_KEY:
        logger.warning("API_KEY_STOCK не найден в переменных окружения")
        for stock in stocks:
            result.append({"stock": stock, "price": 0.0})
        return result

    for stock in stocks:
        url = f"{BASE_URL}?symbol={stock}&apikey={API_KEY}"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            price = float(data.get("price", 0.0))
            result.append({"stock": stock, "price": round(price, 2)})

        except (requests.RequestException, KeyError, IndexError, ValueError, TypeError) as e:
            logger.error(f"Ошибка при получении цены акции {stock}: {e}")
            result.append({"stock": stock, "price": 0.0})

    logger.info(f"Получаем цены акций: {result}")
    return result
