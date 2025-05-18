import asyncio
import json
import aiohttp
from bs4 import BeautifulSoup
from telegram import Bot

URLS = [
    "https://www.ss.lv/ru/transport/cars/bmw/530/",
    "https://www.ss.lv/ru/transport/cars/mercedes/e270/",
    "https://www.ss.lv/ru/transport/cars/mercedes/e320/",
    "https://www.ss.lv/ru/transport/cars/audi/a6/"
]

BOT_TOKEN = "7888713461:AAH-v8ZrtCGqYXvaMrZe7uZcXa9QkXf8caA"
CHAT_ID = "334362698"
SEEN_FILE = "seen_ids.json"


bot = Bot(token=BOT_TOKEN)

async def load_seen_ids():
    try:
        with open(SEEN_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

async def save_seen_ids(ids):
    with open(SEEN_FILE, "w") as f:
        json.dump(ids, f)

async def fetch_new_ads():
    seen_ids = await load_seen_ids()

    new_seen = set(seen_ids)
    
    async with aiohttp.ClientSession() as session:
        for url in URLS:
            try:
                async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as response:
                    text = await response.text()
                print(f"Проверка страницы: {url} (статус: {response.status})")
            except Exception as e:
                print("Ошибка при запросе:", url, e)
                continue
            
            soup = BeautifulSoup(text, "html.parser")
            ads = soup.select("a[href^='/msg/ru/']")
            print(f"На странице {url} найдено объявлений: {len(ads)}")
            
            for ad in ads:
                href = ad.get("href", "")
                if not href.startswith("/msg/ru/"):
                    continue
                full_url = "https://www.ss.lv" + href
                ad_id = href.strip("/").split("/")[-1]
                
                if ad_id not in seen_ids:
                    title = ad.text.strip()
                    message = f"Новая машина:\n{title}\n{full_url}"
                    try:
                        await bot.send_message(chat_id=CHAT_ID, text=message)
                        print("Отправлено сообщение:", message)
                    except Exception as e:
                        print("Ошибка при отправке сообщения:", e)
                    new_seen.add(ad_id)
    
    await save_seen_ids(list(new_seen))

async def main():
    while True:
        await fetch_new_ads()
        await asyncio.sleep(300)

if __name__ == "__main__":
    asyncio.run(main())
