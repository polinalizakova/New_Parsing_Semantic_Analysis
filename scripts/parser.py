"""
Модуль парсинга новостей из RSS-лент
"""

import feedparser
import pandas as pd
import time
import os
from datetime import datetime, timedelta
from scripts.cleaner import clean_text

def parse_date_generic(date_str):
    """Универсальный парсинг дат"""
    if not date_str:
        return None
    try:
        for fmt in ['%a, %d %b %Y %H:%M:%S %z', '%a, %d %b %Y %H:%M:%S', 
                    '%Y-%m-%d %H:%M:%S', '%d %b %Y %H:%M:%S']:
            try:
                dt = datetime.strptime(date_str.split('+')[0].strip(), fmt)
                return dt
            except:
                continue
        return pd.to_datetime(date_str, errors='coerce')
    except:
        return None

def parse_news_ria():
    url = "https://ria.ru/export/rss2/index.xml"
    try:
        feed = feedparser.parse(url)
        articles = []
        for entry in feed.entries:
            articles.append({
                'source': 'РИА Новости',
                'date_raw': entry.get('published', ''),
                'title': entry.get('title', ''),
                'text': entry.get('description', '')
            })
        return articles
    except Exception as e:
        print(f"  Ошибка РИА: {e}")
        return []

def parse_news_tass():
    url = "https://tass.ru/rss/v2.xml"
    try:
        feed = feedparser.parse(url)
        articles = []
        for entry in feed.entries:
            articles.append({
                'source': 'ТАСС',
                'date_raw': entry.get('published', ''),
                'title': entry.get('title', ''),
                'text': entry.get('summary', '')
            })
        return articles
    except Exception as e:
        print(f"  Ошибка ТАСС: {e}")
        return []

def parse_news_kommersant():
    url = "https://www.kommersant.ru/RSS/news.xml"
    try:
        feed = feedparser.parse(url)
        articles = []
        for entry in feed.entries:
            articles.append({
                'source': 'Коммерсантъ',
                'date_raw': entry.get('published', ''),
                'title': entry.get('title', ''),
                'text': entry.get('description', '')
            })
        return articles
    except Exception as e:
        print(f"  Ошибка Коммерсант: {e}")
        return []

def collect_news(append_mode=False):
    """Сбор новостей из трёх источников"""
    print("\n" + "="*60)
    print("НАЧАЛО СБОРА НОВОСТЕЙ")
    print("="*60)
    
    all_articles = []
    
    sources = [
        ("РИА Новости", parse_news_ria),
        ("ТАСС", parse_news_tass),
        ("Коммерсантъ", parse_news_kommersant),
    ]
    
    for i, (name, parser_func) in enumerate(sources, 1):
        print(f"\n[{i}/{len(sources)}] Парсинг {name}...")
        try:
            articles = parser_func()
            all_articles.extend(articles)
            print(f"      Получено: {len(articles)} новостей")
        except Exception as e:
            print(f"      Ошибка: {e}")
        time.sleep(0.3)
    
    if not all_articles:
        print("\n[Предупреждение] Не удалось собрать новости")
        return pd.DataFrame()
    
    df_new = pd.DataFrame(all_articles)
    
    # Парсим даты
    df_new['date'] = df_new['date_raw'].apply(parse_date_generic)
    
    # Удаляем строки с пустыми датами
    before_drop = len(df_new)
    df_new = df_new.dropna(subset=['date'])
    print(f"\nУдалено новостей без дат: {before_drop - len(df_new)}")
    
    # Склеиваем заголовок и текст
    df_new['full_text'] = (df_new['title'].fillna('') + " " + df_new['text'].fillna('')).str.strip()
    df_new['full_text'] = df_new['full_text'].apply(clean_text)
    
    # Удаляем дубликаты по заголовку
    df_new = df_new.drop_duplicates(subset=['title'])
    
    # Загрузка существующих данных (если append_mode)
    if append_mode and os.path.exists("data/raw_news.csv"):
        print("\nЗагрузка существующих данных...")
        df_existing = pd.read_csv("data/raw_news.csv", encoding="utf-8")
        df_existing['date'] = pd.to_datetime(df_existing['date'], errors='coerce')
        print(f"  Существующих новостей: {len(df_existing)}")
        
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        df_combined = df_combined.drop_duplicates(subset=['title'])
        df_combined = df_combined.sort_values('date', ascending=False)
        print(f"  Новых добавлено: {len(df_new)}")
        print(f"  Итого: {len(df_combined)}")
        df_result = df_combined
    else:
        df_result = df_new
    
    df_result = df_result.sort_values('date', ascending=False)
    
    print("\n" + "="*60)
    print("ИТОГО СОБРАНО НОВОСТЕЙ:")
    print(f"  Всего: {len(df_result)}")
    
    if len(df_result) > 0:
        print(f"\n  Диапазон дат:")
        print(f"    от {df_result['date'].min().date()} до {df_result['date'].max().date()}")
        
        print(f"\n  Новостей по дням:")
        day_counts = df_result['date'].dt.date.value_counts().sort_index()
        for day, count in day_counts.items():
            print(f"    {day}: {count} новостей")
    
    print("="*60)
    
    os.makedirs("data", exist_ok=True)
    df_result.to_csv("data/raw_news.csv", index=False, encoding="utf-8")
    
    return df_result

if __name__ == "__main__":
    df = collect_news(append_mode=False)
    print(f"\nСобрано {len(df)} новостей")
    print(df[['date', 'title']].head(10))