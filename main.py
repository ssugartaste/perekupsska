import asyncio
import json
import aiohttp
from bs4 import BeautifulSoup
from telegram import Bot, InputMediaPhoto
import re

URLS = [

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
            async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as resp:
                text = await resp.text()
            soup = BeautifulSoup(text, "html.parser")
            ads = soup.select("a[href^='/msg/ru/']")

            for ad in ads:
                href = ad["href"]
                ad_id = href.strip("/").split("/")[-1]
                full_url = f"https://www.ss.lv{href}"
                if ad_id in seen_ids:
                    continue

                
                thumb_url = None
                thumb_tag = ad.select_one("img.isfoto.foto_list")
                if thumb_tag and thumb_tag.get("src"):
                    src = thumb_tag["src"].strip()
                    if src.startswith("//"):
                        thumb_url = "https:" + src
                    elif src.startswith("/"):
                        thumb_url = "https://www.ss.lv" + src
                    else:
                        thumb_url = src

                
                async with session.get(full_url, headers={"User-Agent": "Mozilla/5.0"}) as ad_resp:
                    ad_html = await ad_resp.text()
                ad_soup = BeautifulSoup(ad_html, "html.parser")

                
                model = "—"
                model_tag = ad_soup.select_one("table.options_list td.ads_opt")
                if model_tag:
                    model = model_tag.get_text(strip=True)

               
                def get_field_for(label):
                    cell = ad_soup.find("td", string=lambda t: t and label in t)
                    if not cell:
                        return None
                    sib = cell.find_next_sibling("td")
                    return sib.get_text(strip=True) if sib else None

                def get_field(labels):
                    for lbl in labels:
                        val = get_field_for(lbl)
                        if val:
                            return val
                    return "—"

               
                raw_price = get_field(["Цена", "Cena"])
                price_match = re.search(r"[\d\s]+€", raw_price)
                price = price_match.group(0) if price_match else raw_price
                km = get_field(["Пробег", "Nobraukums", "Rida"])

                
                img_url = None
                fb = ad_soup.select_one("a.fancybox")
                if fb and fb.get("href"):
                    img_url = fb["href"].strip()
                else:
                    img_tag = ad_soup.select_one("#photo_tbl img")
                    if img_tag and img_tag.get("src"):
                        src = img_tag["src"].strip()
                        if src.startswith("//"):
                            img_url = "https:" + src
                        elif src.startswith("/"):
                            img_url = "https://www.ss.lv" + src
                        else:
                            img_url = src

                caption = (
                    f"Новая машина:\n"
                    f"Model: {model}\n"
                    f"Price: {price}\n"
                    f"Km: {km}\n"
                    f"{full_url}"
                )
                try:
                    media = []
                    
                    if thumb_url:
                        media.append(InputMediaPhoto(media=thumb_url))
                    
                    if img_url:
                        media.append(InputMediaPhoto(media=img_url, caption=caption))
                    
                    if media:
                        await bot.send_media_group(chat_id=CHAT_ID, media=media)
                    else:
                        await bot.send_message(chat_id=CHAT_ID, text=caption)
                except Exception as e:
                    print("Ошибка Telegram:", e)

                new_seen.add(ad_id)

    await save_seen_ids(list(new_seen))

async def main():
    while True:
        await fetch_new_ads()
        await asyncio.sleep(300)

if __name__ == "__main__":
    asyncio.run(main())
