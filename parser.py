import requests
from bs4 import BeautifulSoup as bs4
import json
from fake_useragent import UserAgent
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
import re
import nltk
import os
from dotenv import load_dotenv
import ast

nltk.download('punkt')

# Загрузка переменных окружения из файла .env
load_dotenv()

def load_news():
    ua = UserAgent()
    headers = {
        'user-agent': ua.random
    }
    data_list = {}
    urls = ast.literal_eval(os.getenv('URLS'))
    excluded_words = ast.literal_eval(os.getenv('EXCLUDED_WORDS'))
    summarizer_ru = LsaSummarizer()
    summarizer_en = LsaSummarizer()

    for url in urls:
        response = requests.get(url=url, headers=headers)

        # Проверка подключения
        print('Проверка подключения:', response.status_code)

        bs = bs4(response.text, "lxml")
        news_items = bs.find_all("div", class_="news-item")

        for news_item in news_items:
            try:
                article_id = news_item.get('data-article-id')
                if article_id and article_id not in data_list:
                    title_tag = news_item.find("a", class_="title")
                    if title_tag:
                        title = re.sub(r'\s+', ' ', title_tag.text.strip())
                        link = news_item.get('data-link')
                        link = re.sub(r'[?&]utm_source=CryptoNews&utm_medium=app', '', link)
                        image = news_item.get('data-image')
                        news_id = news_item.get('data-id')
                        category = news_id.split('/')[2] if url == urls[1] else news_id.split('/')[3]
                        category = category.replace('altcoins', 'Альткоины').replace('bitcoin', 'Биткоин').replace(
                            'finance', 'Рынок').replace('security', 'Безопасность').replace('video', 'Видео').replace(
                            'ethereum', 'Эфириум').replace('blockchain', 'Блокчейн').replace('mining', 'Майнинг').replace(
                            'legal', 'Регулирование').replace('analytics', 'Аналитика').replace('exchange', 'Обмен').replace(
                            'other', 'Прочее').replace('blokcheyn', 'Блокчейн').replace('market', 'Рынок')
                        news_url = f"https://cryptonews.net{news_id}"
                        news_response = requests.get(url=news_url, headers=headers)
                        news_bs = bs4(news_response.text, "lxml")
                        content_tag = news_bs.find("div", class_="cn-content")
                        description = '\n\n'.join([p.text for p in content_tag.find_all('p')]) if content_tag else ""
                        if url == urls[0]:
                            parser = PlaintextParser.from_string(description, Tokenizer("russian"))
                            summarizer = summarizer_ru
                        else:
                            parser = PlaintextParser.from_string(description, Tokenizer("english"))
                            summarizer = summarizer_en

                        if len(description) < 500:
                            sentence_count = 1
                        elif len(description) < 1500:
                            sentence_count = 2
                        else:
                            sentence_count = 3

                        summary_sentences = summarizer(parser.document, sentence_count)
                        summary = " ".join([str(sentence) for sentence in summary_sentences])

                        max_length = 1024

                        while len(summary) > max_length:
                            sentence_count -= 1
                            summary_sentences = summarizer(parser.document, sentence_count)
                            summary = " ".join([str(sentence) for sentence in summary_sentences])

                        if not any(word.lower() in title.lower() or word.lower() in description.lower() for word in excluded_words):
                            data_list[article_id] = {
                                "title": title,
                                "image": image,
                                "link": link,
                                "category": category,
                                "description": description,
                                "summary": summary
                            }
            except Exception as e:
                print(f"An error occurred: {e}")

    with open("data.json", "w", encoding='utf-8') as file:
        json.dump(data_list, file, indent=4, ensure_ascii=False)

def main():
    load_news()


if __name__ == '__main__':
    main()
