import json

import pandas as pd

from src.reports import spending_by_category
from src.services import profitable_cashback_categories
from src.utils import load_operations, load_user_settings
from src.views import main_page


def main():
    """Запуск демонстрации всех функций."""

    print("=" * 60)
    print("ЗАГРУЗКА ДАННЫХ")
    print("=" * 60)
    df = load_operations()
    settings = load_user_settings()
    print(f"Загружено транзакций: {len(df)}")
    print(f"Настройки: {settings}")
    print()

    print("=" * 60)
    print("1. ГЛАВНАЯ СТРАНИЦА (views.main_page)")
    print("=" * 60)
    result_views = main_page("2021-12-31 23:59:59")
    data_views = json.loads(result_views)
    print(f"Приветствие: {data_views['greeting']}")
    print(f"Карт обработано: {len(data_views['cards'])}")
    print(f"Топ транзакций: {len(data_views['top_transactions'])}")
    print(f"Курсы валют: {data_views['currency_rates']}")
    print(f"Цены акций: {data_views['stock_prices']}")
    print()

    print("=" * 60)
    print("2. ВЫГОДНЫЕ КАТЕГОРИИ КЕШБЭКА (services.profitable_cashback_categories)")
    print("=" * 60)

    transactions_list = df.to_dict(orient="records")
    for t in transactions_list:
        if "Дата операции" in t and isinstance(t["Дата операции"], pd.Timestamp):
            t["Дата операции"] = t["Дата операции"].strftime("%Y-%m-%d %H:%M:%S")

    result_services = profitable_cashback_categories(2021, 12, transactions_list)
    data_services = json.loads(result_services)
    print("Категории с кешбэком за декабрь 2021:")
    if data_services:
        for category, cashback in data_services.items():
            print(f"  {category}: {cashback} руб.")
    else:
        print("  Данные не найдены")
    print()

    print("=" * 60)
    print("3. ТРАТЫ ПО КАТЕГОРИИ (reports.spending_by_category)")
    print("=" * 60)
    category = "Супермаркеты"
    result_reports = spending_by_category(df, category, "2021-12-31")
    print(f"Категория: {category}")
    print(f"Период: последние 3 месяца от 2021-12-31")
    print(f"Найдено транзакций: {len(result_reports)}")
    if len(result_reports) > 0:
        print("\nПервые 5 транзакций:")
        print(result_reports[["Дата операции", "Сумма платежа", "Категория"]].head())
    print()

    print("=" * 60)
    print("ВСЕ МОДУЛИ УСПЕШНО ЗАВЕРШИЛИ РАБОТУ")
    print("=" * 60)


if __name__ == "__main__":
    main()
