import os
import re
import requests
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_gold_rates():
    url = "https://www.goodreturns.in/gold-rates/vijayawada.html"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        rates = {}
        for row in soup.find_all("tr"):
            cols = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
            if len(cols) >= 2 and cols[0] in ("1", "1 gram", "1 Gram"):
                price_match = re.search(r"₹\s?[\d,]+", cols[1])
                if price_match and "24K" not in rates:
                    rates["24K"] = price_match.group(0)
                elif price_match and "22K" not in rates:
                    rates["22K"] = price_match.group(0)

        if "24K" in rates and "22K" in rates:
            return (
                f"🪙 *Daily Gold Rate (Vijayawada - 1g)*\n"
                f"• *24K Gold:* {rates['24K']}\n"
                f"• *22K Gold:* {rates['22K']}\n\n"
                f"_Source: Goodreturns_"
            )
    except Exception as e:
        print(f"Primary fetch warning: {e}")

    return (
        "⚠️ Could not automatically parse Goodreturns today (site layout or bot protection changed).\n"
        f"Check directly here: {url}"
    )


def send_telegram_message(text):
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
    }
    response = requests.post(api_url, json=payload, timeout=10)
    response.raise_for_status()
    print("Notification sent successfully!")


if __name__ == "__main__":
    message = fetch_gold_rates()
    send_telegram_message(message)
