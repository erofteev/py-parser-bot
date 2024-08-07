from keep_repl_alive import keep_alive
import os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.markdown import hlink
import json
from parser import load_news
import asyncio
from deep_translator import MyMemoryTranslator, GoogleTranslator
from langdetect import detect, lang_detect_exception
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()

# [Config]
keep_alive()  # Пинг сервера

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

# [Bot set]
bot = Bot(token=BOT_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)


def translate_text(text, target_language):
  try:
    source_language = detect(text)
  except lang_detect_exception.LangDetectException:
    return text, False
  if source_language == target_language:
    return text, False
  try:
    translator = MyMemoryTranslator(source=source_language,
                                    target=target_language)
    return translator.translate(text), True
  except Exception:
    translator = GoogleTranslator(source=source_language,
                                  target=target_language)
    return translator.translate(text), True


async def send_news():
  while True:
    load_news()

    with open("data.json", "r", encoding='utf-8') as file:
      data_list = json.load(file)

    try:
      with open("sent.json", "r", encoding='utf-8') as file:
        sent_list = json.load(file)
    except FileNotFoundError:
      sent_list = []

    for article_id, article_data in reversed(data_list.items()):
      if article_id not in sent_list:
        category = article_data["category"]
        title, translated = translate_text(article_data["title"], 'ru')
        summary, _ = translate_text(article_data["summary"], 'ru')
        link = article_data["link"]
        image = article_data["image"]

        if not summary:
          continue

        if translated:
          news = f"#{category}\n\n<b>{title}</b>\n\n{summary}\n\n<i>Возможен некорректный перевод текста, сверяйте с источником.</i>\n\n💎 {hlink('GE News','https://t.me/gldnnews')} | {hlink('Источник',link)}"
        else:
          news = f"#{category}\n\n<b>{title}</b>\n\n{summary}\n\n💎 {hlink('GE News','https://t.me/gldnnews')} | {hlink('Источник',link)}"

        if len(news) > 1024:
          continue

        await bot.send_photo(CHANNEL_ID,
                             photo=image,
                             caption=news,
                             disable_notification=True)
        if len(sent_list) >= 10000:
          sent_list.pop(0)
        sent_list.append(article_id)
        with open("sent.json", "w", encoding='utf-8') as file:
          json.dump(sent_list, file)
        await asyncio.sleep(10)

    os.remove("data.json")
    await asyncio.sleep(1200)


if __name__ == '__main__':
  executor.start_polling(dp, on_startup=lambda _: send_news())
