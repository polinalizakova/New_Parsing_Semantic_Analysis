"""
Модуль очистки текста от HTML-тегов, пунктуации и лишних пробелов
"""

import re

def clean_text(text):
    """
    Очищает текст от HTML-тегов, URL, пунктуации, приводит к нижнему регистру
    
    Параметры:
        text: строка для очистки
    
    Возвращает:
        очищенную строку
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Удаляем HTML-теги
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # Удаляем URL
    text = re.sub(r'http\S+|www\S+|https\S+', '', text)
    
    # Оставляем только буквы (русские и английские) и пробелы
    text = re.sub(r'[^a-zA-Zа-яА-Я\s]', ' ', text)
    
    # Приводим к нижнему регистру
    text = text.lower()
    
    # Убираем лишние пробелы
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def clean_dataframe(df, text_column='full_text'):
    """
    Очищает колонку с текстом в DataFrame
    
    Параметры:
        df: pandas DataFrame
        text_column: название колонки с текстом
    
    Возвращает:
        DataFrame с очищенной колонкой
    """
    if text_column in df.columns:
        df['cleaned_text'] = df[text_column].apply(clean_text)
    
    return df

