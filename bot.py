import os
import time
import requests

TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

# Общий эндпоинт ленты листингов CSFloat (сортировка по новизне или низкой цене)
API_URL = "https://csfloat.com/api/v1/listings"


def send_telegram_alert(text):
  url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
  payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
  try:
    requests.post(url, json=payload, timeout=10)
  except Exception as e:
    print(f"Ошибка отправки: {e}")


def check_market_deals():
  # Параметры: ищем недорогие предметы (до $5), отсортированные по свежести
  params = {
      "max_price": 500,  # цена в центах ($5.00)
      "sort_by": "lowest_price",
      "limit": 30,
  }
  headers = {"User-Agent": "Mozilla/5.0"}

  try:
    response = requests.get(API_URL, params=params, headers=headers, timeout=10)
    if response.status_code != 200:
      return

    listings = response.json()

    for item in listings:
      item_info = item.get("item", {})
      market_name = item_info.get("market_hash_name", "Unknown")
      float_val = item_info.get("float_value", 1.0)
      price_usd = item.get("price", 0) / 100.0
      item_id = item.get("id")

      # Пример универсального фильтра:
      # Ищем скины в качестве Factory New (float < 0.07), которые стоят сущие копейки (например, < $0.50),
      # но при этом потенциально могут быть редкими «филлерами» под контракты.
      if float_val < 0.07 and price_usd < 0.50:
        alert_msg = (
            f"⚡ *Потенциальная находка!* ⚡\n"
            f"Скин: `{market_name}`\n"
            f"Float: `{float_val:.5f}` (Factory New)\n"
            f"Цена: **${price_usd}**\n"
            f"Ссылка: https://csfloat.com/item/{item_id}"
        )
        send_telegram_alert(alert_msg)

  except Exception as e:
    print(f"Ошибка запроса: {e}")


if __name__ == "__main__":
  print("Монитор рынка запущен...")
  while True:
    check_market_deals()
    time.sleep(120)  # проверка каждые 2 минуты