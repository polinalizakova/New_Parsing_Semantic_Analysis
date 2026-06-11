#!/usr/bin/env Rscript

# Групповой проект: семантический анализ новостей

cat("\n")
cat("ЗАПУСК R-АНАЛИЗА\n")
cat("\n")

# 1. ПРОВЕРКА И УСТАНОВКА ПАКЕТОВ

cat("[1/8] Проверка и установка пакетов...\n")

check_package <- function(pkg) {
  if(!require(pkg, character.only = TRUE)) {
    cat("[УСТАНОВКА] Пакет", pkg, "\n")
    install.packages(pkg, repos = "https://cloud.r-project.org", quiet = TRUE)
    library(pkg, character.only = TRUE)
  } else {
    cat("[OK] Пакет", pkg, "\n")
  }
}

packages <- c("udpipe", "ggplot2", "dplyr", "wordcloud", "RColorBrewer")
for(pkg in packages) {
  check_package(pkg)
}

cat("[OK] Все пакеты загружены\n\n")

# 2. СОЗДАНИЕ ПАПОК

cat("[2/8] Создание папок...\n")

dir.create("output/plots", showWarnings = FALSE, recursive = TRUE)
dir.create("output/tables", showWarnings = FALSE, recursive = TRUE)
cat("[OK] Папки созданы\n\n")

# 3. ЗАГРУЗКА ДАННЫХ

cat("[3/8] Загрузка данных...\n")

if(!file.exists("data/raw_news.csv")) {
  cat("[ОШИБКА] Файл data/raw_news.csv не найден\n")
  quit(status = 1)
}

data <- read.csv("data/raw_news.csv", fileEncoding = "UTF-8", stringsAsFactors = FALSE)
cat("[OK] Загружено", nrow(data), "новостей\n")

data$date <- as.Date(data$date)
data <- data[!is.na(data$date), ]
cat("[OK] Диапазон дат: от", min(data$date), "до", max(data$date), "\n\n")

# 4. ЗАГРУЗКА МОДЕЛИ UDPIPE

cat("[4/8] Загрузка модели udpipe...\n")

model_file <- "russian-gsd-ud-2.5-191206.udpipe"
if(!file.exists(model_file)) {
  cat("Скачиваю модель...\n")
  udpipe::udpipe_download_model(language = "russian", model_dir = ".")
}

if(!file.exists(model_file)) {
  cat("[ОШИБКА] Модель не найдена\n")
  quit(status = 1)
}

ud_model <- udpipe::udpipe_load_model(model_file)
cat("[OK] Модель загружена\n\n")

# 5. ЛЕММАТИЗАЦИЯ

cat("[5/8] Лемматизация текстов...\n")

all_text <- paste(data$title, data$text, sep = " ")
annotated <- udpipe::udpipe_annotate(ud_model, x = all_text, doc_id = 1:nrow(data))
df <- as.data.frame(annotated)
cat("[OK] Обработано", nrow(df), "токенов\n\n")

# 6. ФИЛЬТРАЦИЯ

cat("[6/8] Фильтрация...\n")

filtered <- df[df$upos %in% c("NOUN", "VERB", "ADJ"), ]
cat("  После фильтрации по POS:", nrow(filtered), "токенов\n")

filtered <- filtered[nchar(filtered$lemma) >= 3, ]
cat("  После удаления коротких слов:", nrow(filtered), "токенов\n")

stop_words <- c("и", "в", "на", "с", "к", "у", "о", "по", "за", "из", "от", "до",
                "это", "как", "так", "вот", "весь", "а", "но", "да", "или", "же",
                "все", "меня", "тебя", "нас", "вас", "мой", "твой", "его", "ее",
                "наш", "ваш", "также", "чтобы", "потому", "быть", "для", "при")
filtered <- filtered[!filtered$lemma %in% stop_words, ]
cat("  После удаления стоп-слов:", nrow(filtered), "токенов\n\n")

# 7. ЧАСТОТНЫЙ АНАЛИЗ

cat("[7/8] Частотный анализ...\n")

freq <- table(filtered$lemma)
freq <- sort(freq, decreasing = TRUE)
top30 <- head(freq, 30)

freq_df <- data.frame(слово = names(top30), частота = as.vector(top30))
write.csv(freq_df, "output/tables/word_freq.csv", row.names = FALSE, fileEncoding = "UTF-8")
cat("[OK] Сохранено: output/tables/word_freq.csv\n\n")

# 8. ВИЗУАЛИЗАЦИЯ

cat("[8/8] Визуализация...\n")

# Облако слов
png("output/plots/wordcloud.png", width = 800, height = 600, res = 100)
wordcloud::wordcloud(words = freq_df$слово, freq = freq_df$частота,
          min.freq = 1, max.words = 100, random.order = FALSE,
          rot.per = 0.35, colors = RColorBrewer::brewer.pal(8, "Dark2"))
title("Облако слов")
dev.off()
cat("[OK] Сохранено: output/plots/wordcloud.png\n")

# Столбчатая диаграмма
top15 <- freq_df[1:15, ]
p_bar <- ggplot(top15, aes(x = reorder(слово, частота), y = частота)) +
  geom_bar(stat = "identity", fill = "steelblue") +
  coord_flip() +
  labs(title = "Топ-15 частотных слов", x = "", y = "Частота") +
  theme_minimal()
ggsave("output/plots/top15_words.png", p_bar, width = 10, height = 6)
cat("[OK] Сохранено: output/plots/top15_words.png\n")

# 9. ДИНАМИКА ПО ДНЯМ

cat("\nСоздание динамики по дням...\n")

top5_words <- freq_df$слово[1:min(5, nrow(freq_df))]
daily_data <- data.frame()

for(word in top5_words) {
  word_doc_ids <- filtered$doc_id[filtered$lemma == word]
  if(length(word_doc_ids) > 0) {
    for(i in 1:nrow(data)) {
      count_i <- sum(word_doc_ids == i)
      if(count_i > 0) {
        daily_data <- rbind(daily_data, data.frame(
          date = data$date[i],
          word = word,
          count = count_i
        ))
      }
    }
  }
}

if(nrow(daily_data) > 0) {
  daily_agg <- aggregate(count ~ date + word, data = daily_data, sum)
  
  p_dyn <- ggplot(daily_agg, aes(x = date, y = count, color = word, group = word)) +
    geom_line(size = 1) +
    geom_point(size = 2) +
    labs(title = "Динамика упоминаний ключевых слов по дням",
         x = "Дата", y = "Количество упоминаний", color = "Слово") +
    theme_minimal() +
    theme(legend.position = "bottom")
  
  ggsave("output/plots/dynamics.png", p_dyn, width = 12, height = 6)
  cat("[OK] Сохранено: output/plots/dynamics.png\n")
  
  write.csv(daily_agg, "output/tables/dynamics.csv", row.names = FALSE, fileEncoding = "UTF-8")
  cat("[OK] Сохранено: output/tables/dynamics.csv\n")
  
  cat("\nДинамика по дням:\n")
  for(word in top5_words) {
    word_data <- daily_agg[daily_agg$word == word, ]
    if(nrow(word_data) > 0) {
      cat("\n", word, ":\n")
      for(i in 1:nrow(word_data)) {
        cat("  ", word_data$date[i], ":", word_data$count[i], "\n")
      }
    }
  }
} else {
  cat("[ПРЕДУПРЕЖДЕНИЕ] Не удалось построить динамику\n")
}

# 10. ОТЧЁТ


report <- paste(
  "ОТЧЁТ О СЕМАНТИЧЕСКОМ АНАЛИЗЕ НОВОСТЕЙ\n\n",
  "Дата анализа:", Sys.time(), "\n\n",
  "--- ИСХОДНЫЕ ДАННЫЕ ---\n",
  "  Всего новостей:", nrow(data), "\n",
  "  Источники:", paste(unique(data$source), collapse = ", "), "\n",
  "  Период:", min(data$date), "—", max(data$date), "\n",
  "  Всего дней:", as.numeric(max(data$date) - min(data$date)) + 1, "\n\n",
  "--- РЕЗУЛЬТАТЫ ---\n",
  "  Уникальных слов (лемм):", length(unique(filtered$lemma)), "\n",
  "  Всего токенов:", nrow(filtered), "\n\n",
  "  Топ-5 слов:\n"
)

for(i in 1:min(5, nrow(freq_df))) {
  report <- paste(report, "    ", i, ".", freq_df$слово[i], "-", freq_df$частота[i], "\n")
}

writeLines(report, "output/report.txt")
cat("\n[OK] Сохранено: output/report.txt\n\n")

cat("ГОТОВО! Результаты в папке output/\n")