"""
Групповой проект: Парсинг + семантический анализ новостей
"""

import os
import sys
import subprocess
import pandas as pd

RSCRIPT_PATH = "E:/R-4.5.3/bin/x64/Rscript.exe"

def clear_screen():
    os.system('cls' if sys.platform == 'win32' else 'clear')

def open_manual():
    manual_path = os.path.join("notes", "user_manual.pdf")
    if not os.path.exists(manual_path):
        print(f"[Ошибка] Файл инструкции не найден: {manual_path}")
        input("Нажмите Enter...")
        return
    os.startfile(manual_path)

def parse_news():
    print("\n" + "="*50)
    print("ЗАПУСК ПАРСИНГА НОВОСТЕЙ")
    print("="*50)
    
    try:
        from scripts.parser import collect_news
        
        print("\nВыберите режим сбора:")
        print("1. Собрать ВСЕ новости (без фильтра по дням)")
        print("2. Собрать новости с фильтром по дням")
        print("3. Добавить к существующим (накопление)")
        choice = input("Ваш выбор (1-3): ").strip()
        
        if choice == "1":
            print("\nСбор ВСЕХ новостей...")
            df = collect_news(append_mode=False)
            
        elif choice == "2":
            print("\nВыберите количество дней:")
            print("1. 3 дня")
            print("2. 7 дней")
            print("3. 14 дней")
            days_choice = input("Ваш выбор (1-3): ").strip()
            days_map = {"1": 3, "2": 7, "3": 14}
            days = days_map.get(days_choice, 7)
            print(f"\nСбор новостей за последние {days} дней...")
            df = collect_news(append_mode=False)
            # Фильтруем по дням после сбора
            cutoff = pd.Timestamp.now() - pd.Timedelta(days=days)
            df = df[df['date'] >= cutoff]
            
        elif choice == "3":
            print("\nДобавление новых новостей к существующим...")
            df = collect_news(append_mode=True)
            
        else:
            print("\n[Ошибка] Неверный выбор")
            input("Нажмите Enter...")
            return
        
        print(f"\n[Успех] Итого собрано: {len(df)} новостей")
        print("Сохранено в: data/raw_news.csv")
        
        if len(df) > 0:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df_valid = df.dropna(subset=['date'])
            
            if len(df_valid) > 0:
                print(f"\nДиапазон дат:")
                print(f"  от {df_valid['date'].min().date()} до {df_valid['date'].max().date()}")
                
                print(f"\nНовостей по дням:")
                day_counts = df_valid['date'].dt.date.value_counts().sort_index()
                for day, count in day_counts.items():
                    print(f"  {day}: {count} новостей")
        
    except Exception as e:
        print(f"\n[Ошибка] {e}")
        import traceback
        traceback.print_exc()
    
    input("\nНажмите Enter...")

def run_r_analysis():
    print("\n" + "="*50)
    print("ЗАПУСК АНАЛИЗА (R)")
    print("="*50)
    
    if not os.path.exists("data/raw_news.csv"):
        print("\n[Ошибка] Сначала выполните парсинг новостей (пункт 1)")
        input("Нажмите Enter...")
        return
    
    if not os.path.exists(RSCRIPT_PATH):
        print(f"\n[Ошибка] Rscript не найден по пути: {RSCRIPT_PATH}")
        input("Нажмите Enter...")
        return
    
    try:
        print("\nЗапуск R-скрипта...")
        result = subprocess.run(
            [RSCRIPT_PATH, "r_scripts/analyze.R"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=os.getcwd()
        )
        
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print("\n[Успех] Анализ завершён!")
            print("Результаты в папке output/")
        else:
            print(f"\n[Ошибка] R-скрипт завершился с кодом {result.returncode}")
            
    except Exception as e:
        print(f"\n[Ошибка] {e}")
    
    input("Нажмите Enter...")

def show_menu():
    clear_screen()
    print("="*50)
    print("    АНАЛИЗ НОВОСТНЫХ ТЕКСТОВ")
    print("    Парсинг + семантический анализ")
    print("="*50)
    print("")
    print("  1. Парсинг новостей (Python)")
    print("  2. Запустить анализ (R)")
    print("  3. Открыть инструкцию")
    print("  0. Выход")
    print("")
    print("="*50)

def main():
    while True:
        show_menu()
        choice = input("Ваш выбор: ").strip()
        
        if choice == "1":
            parse_news()
        elif choice == "2":
            run_r_analysis()
        elif choice == "3":
            open_manual()
        elif choice == "0":
            print("\nДо свидания!")
            sys.exit(0)
        else:
            print("\n[Ошибка] Неверный ввод. Выберите 0-3")
            input("Нажмите Enter...")

if __name__ == "__main__":
    main()