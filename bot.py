import asyncio
import aiohttp
from lxml import html
from aiogram import Bot, Dispatcher, types
from aiogram.types import BotCommand
from aiogram.filters import Command
from aiogram import Router
from aiogram.fsm.storage.memory import MemoryStorage
import logging

# Logging ayarları
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Telegram API token (BotFather'dan alınmalı)
API_TOKEN = '7144252423:AAHLWYdYdid7_OIOd38v9E-1VBgTKEfpwjQ'  # Buraya kendi tokenınızı yazın

# URL ve diğer sabitler
URL = 'https://sports2.skappsports.com/tr/spor/basketbol/8/t%C3%BCm%C3%BC/0/lokasyon/canl%C4%B1'  # İzlemek istediğiniz URL'yi buraya yazın
CHAT_ID = '-1002042005489'  # Mesaj göndermek için kullanılacak chat ID
TARGET_TEXT = "Yüksek oran"  # İzlemek istediğiniz metin
STOP_SIGNAL = asyncio.Event()

# Bot ve Dispatcher
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()

# Web scraping için async fonksiyon
async def fetch(session, url):
    try:
        async with session.get(url) as response:
            logger.info(f"Fetching URL: {url}")
            return await response.text()
    except Exception as e:
        logger.error(f"Error fetching URL: {e}")
        return ""

# Web sitesi kontrolü
async def check_website():
    async with aiohttp.ClientSession() as session:
        while not STOP_SIGNAL.is_set():
            try:
                page_content = await fetch(session, URL)
                tree = html.fromstring(page_content)
                if TARGET_TEXT in tree.text_content():
                    await bot.send_message(chat_id=CHAT_ID, text=f'Text "{TARGET_TEXT}" found on the website!')
                    STOP_SIGNAL.set()
                    logger.info("Target text found. Monitoring stopped.")
            except Exception as e:
                logger.error(f"Error during website check: {e}")
            await asyncio.sleep(10)

# Komutlar
@router.message(Command(commands=["start"]))
async def start(message: types.Message):
    STOP_SIGNAL.clear()
    asyncio.create_task(check_website())
    await message.answer("Bot is monitoring the website.")
    logger.info(f"Monitoring started by user: {message.from_user.id}")

@router.message(Command(commands=["stop"]))
async def stop(message: types.Message):
    STOP_SIGNAL.set()
    await message.answer("Monitoring stopped.")
    logger.info(f"Monitoring stopped by user: {message.from_user.id}")

@router.message(Command(commands=["change"]))
async def change_target(message: types.Message):
    global TARGET_TEXT
    new_target = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
    if new_target:
        TARGET_TEXT = new_target
        await message.answer(f"Target text changed to: {TARGET_TEXT}")
        logger.info(f"Target text changed to: {TARGET_TEXT}")
    else:
        await message.answer("Please provide the new target text after the command, e.g., /change new text")

# Bot başlatma fonksiyonları
async def on_startup():
    await bot.set_my_commands([
        BotCommand(command="start", description="Start monitoring"),
        BotCommand(command="stop", description="Stop monitoring"),
        BotCommand(command="change", description="Change target text")
    ])
    logger.info("Bot commands set.")

async def main():
    dp.include_router(router)
    await on_startup()
    logger.info("Bot is starting...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    import nest_asyncio
    nest_asyncio.apply()  # Event loop uyumsuzluklarını önler
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped manually.")
