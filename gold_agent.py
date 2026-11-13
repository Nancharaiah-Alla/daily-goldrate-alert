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
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.google.com/",
}


def try_goodreturns():
    url = "https://www.goodreturns.in/gold-rates/vijayawada.html"
    res = requests.get(url, headers=HEADERS, timeout=15)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    # Method 1: Parse Goodreturns side-by-side table (Gram | 24K | 22K | 18K)
    for row in soup.find_all("tr"):
        cols = [c.get_text(" ", strip=True) for c in row.find_all(["td", "th"])]
        if len(cols) >= 3 and cols[0].strip() in ("1", "1 gram", "1 Gram"):
            p24 = re.search(r"₹\s?[\d,]+", cols[1])
            p22 = re.search(r"₹\s?[\d,]+", cols[2])
            if p24 and p22:
                return p24.group(0), p22.group(0), "Goodreturns"

    # Method 2: Parse Goodreturns summary text
    text = soup.get_text(" ", strip=True)
    match = re.search(
        r"stands at\s*(₹\s?[\d,]+)\s*per gram for 24 karat.*?(₹\s?[\d,]+)",
        text,
        re.IGNORECASE,
    )
    if match:
        return match.group(1), match.group(2), "Goodreturns"

    return None


def try_bankbazaar():
    url = "https://www.bankbazaar.com/gold-rate-vijayawada.html"
    res = requests.get(url, headers=HEADERS, timeout=15)
    res.raise_for_status()
    text = BeautifulSoup(res.text, "html.parser").get_text(" ", strip=True)

    m22 = re.search(r"22\s*Carat\s*Gold\s*Rate.*?1\s*gram\s*(₹\s?[\d,]+)", text, re.IGNORECASE)
    m24 = re.search(r"24\s*Carat\s*Gold\s*Rate.*?1\s*gram\s*(₹\s?[\d,]+)", text, re.IGNORECASE)
    if m24 and m22:
        return m24.group(1), m22.group(1), "BankBazaar (Vijayawada)"

    return None


def fetch_gold_rates():
    for fetcher in (try_goodreturns, try_bankbazaar):
        try:
            result = fetcher()
            if result:
                rate_24k, rate_22k, source = result
                return (
                    f"🪙 *Daily Gold Rate (Vijayawada - 1g)*\n"
                    f"• *24K Gold:* {rate_24k}\n"
                    f"• *22K Gold:* {rate_22k}\n\n"
                    f"_Source: {source}_"
                )
        except Exception as e:
            print(f"{fetcher.__name__} failed: {e}")

    return (
        "⚠️ Both Goodreturns and backup sources blocked the cloud request today.\n"
        "Check directly here: https://www.goodreturns.in/gold-rates/vijayawada.html"
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
