#!/bin/bash

# Простой и надежный скрипт для получения содержимого веб-страницы
# Использует curl для загрузки и обработки ошибок

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Функция для проверки зависимостей
check_dependencies() {
    if ! command -v curl &> /dev/null; then
        log_error "curl не найден в системе"
        log_info "Установите curl: sudo apt-get install curl"
        exit 1
    fi
}

# Функция для валидации URL
validate_url() {
    local url="$1"
    
    # Простая проверка формата URL
    if [[ ! "$url" =~ ^https?:// ]]; then
        log_error "Неверный формат URL: $url"
        log_info "URL должен начинаться с http:// или https://"
        exit 1
    fi
}

# Функция для получения содержимого страницы
fetch_page() {
    local url="$1"
    local output_file="${2:-page_content.html}"
    local timeout="${3:-30}"
    
    log_info "Загружаю содержимое страницы: $url"
    log_info "Таймаут: ${timeout} секунд"
    
    # Создаем временный файл для curl
    local temp_file=$(mktemp)
    
    # Выполняем curl с обработкой ошибок
    if curl \
        --silent \
        --show-error \
        --max-time "$timeout" \
        --connect-timeout 10 \
        --retry 2 \
        --retry-delay 1 \
        --location \
        --compressed \
        --fail \
        --user-agent "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" \
        --output "$temp_file" \
        --write-out "HTTP_CODE:%{http_code}\nSIZE:%{size_download}\nTIME:%{time_total}\n" \
        "$url"; then
        
        # Получаем HTTP код и размер
        local http_code=$(grep "HTTP_CODE:" "$temp_file" | cut -d: -f2)
        local size=$(grep "SIZE:" "$temp_file" | cut -d: -f2)
        local time=$(grep "TIME:" "$temp_file" | cut -d: -f2)
        
        # Удаляем служебные строки curl
        sed -i '/^HTTP_CODE:/d; /^SIZE:/d; /^TIME:/d' "$temp_file"
        
        # Проверяем HTTP код
        if [[ "$http_code" -ge 200 && "$http_code" -lt 300 ]]; then
            log_success "Страница успешно загружена!"
            log_info "HTTP код: $http_code"
            log_info "Размер: $size байт"
            log_info "Время загрузки: ${time} секунд"
            
            # Копируем содержимое в выходной файл
            cp "$temp_file" "$output_file"
            log_success "Содержимое сохранено в: $output_file"
            
            # Показываем первые 500 символов
            echo
            log_info "Первые 500 символов содержимого:"
            echo "=================================================="
            head -c 500 "$output_file" | cat
            if [[ $(wc -c < "$output_file") -gt 500 ]]; then
                echo "..."
            fi
            echo "=================================================="
            
        else
            log_error "HTTP ошибка: $http_code"
            exit 1
        fi
        
    else
        log_error "Ошибка при загрузке страницы"
        exit 1
    fi
    
    # Удаляем временный файл
    rm -f "$temp_file"
}

# Функция для извлечения текста из HTML (простая версия)
extract_text() {
    local html_file="$1"
    local text_file="${2:-page_text.txt}"
    
    log_info "Извлекаю текст из HTML..."
    
    # Простое извлечение текста (удаляем HTML теги)
    # Более сложная обработка потребует дополнительных инструментов
    sed 's/<[^>]*>//g' "$html_file" | \
    sed 's/&nbsp;/ /g' | \
    sed 's/&amp;/\&/g' | \
    sed 's/&lt;/</g' | \
    sed 's/&gt;/>/g' | \
    sed 's/&quot;/"/g' | \
    tr -s ' \t\n' ' ' | \
    sed 's/^ *//;s/ *$//' > "$text_file"
    
    log_success "Текст извлечен и сохранен в: $text_file"
    
    # Показываем первые 300 символов текста
    echo
    log_info "Первые 300 символов извлеченного текста:"
    echo "=================================================="
    head -c 300 "$text_file" | cat
    if [[ $(wc -c < "$text_file") -gt 300 ]]; then
        echo "..."
    fi
    echo "=================================================="
}

# Основная функция
main() {
    # Проверяем количество аргументов
    if [[ $# -lt 1 ]]; then
        echo "Использование: $0 <URL> [output_file] [timeout]"
        echo "Пример: $0 https://example.com"
        echo "Пример: $0 https://example.com my_page.html 60"
        exit 1
    fi
    
    local url="$1"
    local output_file="${2:-page_content.html}"
    local timeout="${3:-30}"
    
    echo "=================================================="
    log_info "Скрипт загрузки веб-страницы"
    echo "=================================================="
    
    # Проверяем зависимости
    check_dependencies
    
    # Валидируем URL
    validate_url "$url"
    
    # Загружаем страницу
    fetch_page "$url" "$output_file" "$timeout"
    
    # Извлекаем текст
    extract_text "$output_file"
    
    echo
    log_success "Работа завершена успешно!"
    log_info "Файлы созданы:"
    log_info "  - $output_file (HTML содержимое)"
    log_info "  - page_text.txt (извлеченный текст)"
}

# Запускаем основную функцию
main "$@"