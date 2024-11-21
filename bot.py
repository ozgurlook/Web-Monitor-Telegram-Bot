import logging
import asyncio
import aiohttp
from lxml import html
from aiogram import Bot, Dispatcher, types
from aiogram.types import BotCommand
from aiogram.filters import Command
from aiogram import Router
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import F

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,  # INFO seviyesinde log kaydedilir
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

API_TOKEN = 'your-telegram-bot-api-token'
URL = 'https://your-url-here.com'
CHAT_ID = 'your-chat-id'

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
stop_signal = asyncio.Event()
target_text = "Yüksek oran" 

async def fetch(session, url):
    try:
        async with session.get(url) as response:
            logger.info(f"Fetching URL: {url}")  # Log: URL'ye erişiliyor
            return await response.text()
    except Exception as e:
        logger.error(f"Error while fetching URL: {e}")  # Log: Hata

async def check_website():
    async with aiohttp.ClientSession() as session:
        while not stop_signal.is_set():
            try:
                logger.info("Checking website for target text...")  # Log: Web sitesi kontrol ediliyor
                page_content = await fetch(session, URL)
                tree = html.fromstring(page_content)
                if target_text in tree.text_content():
                    await bot.send_message(chat_id=CHAT_ID, text=f'Text "{target_text}" found on the website!')
                    logger.info(f"Target text '{target_text}' found on website!")  # Log: Metin bulundu
                    break
            except Exception as e:
                logger.error(f"An error occurred during website check: {e}")  # Log: Kontrol sırasında hata
            await asyncio.sleep(10)  # 10 saniye bekle
            logger.info("Retrying website check...")  # Log: Tekrar deneniyor

@router.message(Command(commands=["start"]))
async def start(message: types.Message):
    logger.info("Received /start command from user.")  # Log: /start komutu alındı
    stop_signal.clear()
    asyncio.create_task(check_website())
    await message.answer("Bot is monitoring the website.")

@router.message(Command(commands=["stop"]))
async def stop(message: types.Message):
    logger.info("Received /stop command from user.")  # Log: /stop komutu alındı
    stop_signal.set()
    await message.answer("Stopped monitoring the website.")

@router.message(Command(commands=["change"]))
async def change_target(message: types.Message):
    logger.info("Received /change command from user.")  # Log: /change komutu alındı
    global target_text
    new_target = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
    if new_target:
        target_text = new_target
        logger.info(f"Target text changed to: {target_text}")  # Log: Hedef metin değiştirildi
        await message.answer(f"Target text changed to: {target_text}")
    else:
        await message.answer("Please provide the new target text after the command, e.g., /change new text")

async def on_startup():
    logger.info("Setting bot commands...")  # Log: Komutlar ayarlanıyor
    await bot.set_my_commands([BotCommand(command="start", description="Start monitoring"),
                               BotCommand(command="stop", description="Stop monitoring"),
                               BotCommand(command="change", description="Change target text")])

async def main():
    logger.info("Bot is starting...")  # Log: Bot başlatılıyor
    dp.include_router(router)
    await on_startup()
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")  # Log: Bot kullanıcı tarafından durduruldu
