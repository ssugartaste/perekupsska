import re
import os
import asyncio
import aiohttp

from aiogram import Bot, Dispatcher, types, Router
from aiogram.types import InputMediaPhoto
from aiogram.filters import Command

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from db import Database


load_dotenv('main.env')

BOT_TOKEN = os.getenv('BOT_TOKEN')
dp = Dispatcher()

router = Router()
dp.include_router(router)

db = Database()  # initialize database

bot = Bot(token=BOT_TOKEN)


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    db.add_user(message.from_user.id)
    await message.reply(
        "Hello! I'm a bot for tracking ads.\n"
        "Add a search URL from ss.lv using the command:\n"
        "/addurl <URL>\n"
        "For example:\n"
        "/addurl https://www.ss.lv/ru/transport/cars/mercedes/e270/"
    )


@router.message(Command("addurl"))
async def cmd_addurl(message: types.Message, command: Command):
    db.add_user(message.from_user.id)
    args = command.args
    if not args:
        await message.reply("Please specify a URL after the command.\nExample:\n/addurl https://www.ss.lv/ru/transport/cars/audi/a6/")
        return

    url = args.strip()
    if not url.startswith("https://www.ss.lv"):
        await message.reply("URL must start with https://www.ss.lv")
        return

    added = db.add_url_for_user(message.from_user.id, url)
    if added:
        await message.reply(f"URL added: {url}")
    else:
        await message.reply("This URL is already in your list.")


async def fetch_ads_by_url(session: aiohttp.ClientSession, url: str):
    """
    Fetch and parse ads list from a given URL.
    Returns list of ad elements (BeautifulSoup objects).
    """
    async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as resp:
        text = await resp.text()
    soup = BeautifulSoup(text, "html.parser")
    ads = soup.select("a[href^='/msg/ru/']")
    return ads


async def fetch_ad_details(session: aiohttp.ClientSession, full_url: str):
    """
    Fetch ad page and parse details like model, price, km, images.
    Returns a dict with needed info.
    """
    async with session.get(full_url, headers={"User-Agent": "Mozilla/5.0"}) as resp:
        ad_html = await resp.text()
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
    km = get_field(["Пробег", "Nobraukums"])

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

    print(img_url)

    return {
        "model": model,
        "price": price,
        "km": km,
        "img_url": img_url
    }


def build_caption(ad_info: dict, full_url: str) -> str:
    return (
        f"New car:\n"
        f"Model: {ad_info['model']}\n"
        f"Price: {ad_info['price']}\n"
        f"Km: {ad_info['km']}\n"
        f"{full_url}"
    )


async def send_ad_to_users(ad_id: str, img_url: str, ad_info: dict, full_url: str, users: list):
    caption = build_caption(ad_info, full_url)

    for user_id in users:
        try:
            if img_url:
                await bot.send_photo(chat_id=user_id, photo=img_url, caption=caption)
            else:
                await bot.send_message(chat_id=user_id, text=caption)
            db.mark_ad_as_seen(user_id, ad_id)
        except Exception as e:
            print(f"Telegram error for user {user_id}: {e}")


async def process_url(session: aiohttp.ClientSession, url: str):
    """
    Process one unique URL: fetch ads, parse details, send to relevant users.
    """
    try:
        ads = await fetch_ads_by_url(session, url)
    except Exception as e:
        print(f"Error fetching ads from URL {url}: {e}")
        return

    for ad in ads:
        href = ad["href"]
        ad_id = href.strip("/").split("/")[-1]

        users_for_url = db.get_active_users_by_url(url)
        users_to_send = [uid for uid in users_for_url if not db.is_ad_seen(uid, ad_id)]
        if not users_to_send:
            continue

        full_url = f"https://www.ss.lv{href}"

        try:
            ad_info = await fetch_ad_details(session, full_url)
        except Exception as e:
            print(f"Error fetching ad details {full_url}: {e}")
            continue

        await send_ad_to_users(ad_id, ad_info["img_url"], ad_info, full_url, users_to_send)



async def periodic_check():
    while True:
        unique_urls = db.get_unique_urls_of_active_users()
        async with aiohttp.ClientSession() as session:
            tasks = [process_url(session, url) for url in unique_urls]
            await asyncio.gather(*tasks)
        await asyncio.sleep(10)


async def main():
    asyncio.create_task(periodic_check())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())