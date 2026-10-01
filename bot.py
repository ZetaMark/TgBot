import os
import time
import requests

TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

# Общий эндпоинт ленты листингов CSFloat (сортировка по новизне или низкой цене)
API_URL = "https://csfloat.com/api/v1/listings"

# Множество для хранения ID уже отправленных предметов, чтобы не спамить
seen_items = set()

def send_telegram_alert(text):
    if not TG_TOKEN or not TG_CHAT_ID:
        print("Ошибка: Токены Telegram не настроены в переменных окружения!")
        return
        
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")

def check_market_deals():
    # Параметры: ищем недорогие предметы (до $5)
    params = {
        "max_price": 500,  # цена в центах ($5.00)
        "sort_by": "lowest_price",
        "limit": 30,
    }
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(API_URL, params=params, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Ошибка ответа от API: статус {response.status_code}")
            return

        listings = response.json()

        for item in listings:
            item_id = item.get("id")
            
            # Если этот лот мы уже кидали в телегу, просто пропускаем его
            if item_id in seen_items:
                continue

            item_info = item.get("item", {})
            market_name = item_info.get("market_hash_name", "Unknown")
            float_val = item_info.get("float_value", 1.0)
            price_usd = item.get("price", 0) / 100.0

            # Фильтр: скины в качестве Factory New (float < 0.07) до $0.50
            if float_val < 0.07 and price_usd < 0.50:
                alert_msg = (
                    f"⚡ *Потенциальная находка!* ⚡\n"
                    f"Скин: `{market_name}`\n"
                    f"Float: `{float_val:.5f}` (Factory New)\n"
                    f"Цена: **${price_usd}**\n"
                    f"Ссылка: https://csfloat.com/item/{item_id}"
                )
                send_telegram_alert(alert_msg)
                
                # Добавляем ID в список отправленных, чтобы не прислать повторно через 2 минуты
                seen_items.add(item_id)
                
                # Ограничиваем размер множества, чтобы не засорять оперативку (храним последние 1000 ID)
                if len(seen_items) > 1000:
                    seen_items.pop()

    except Exception as e:
        print(f"Ошибка запроса к CSFloat: {e}")

if __name__ == "__main__":
    print("Монитор рынка запущен...")
    while True:
        check_market_deals()
        time.sleep(120)  # проверка каждые 2 минуты