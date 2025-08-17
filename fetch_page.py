#!/usr/bin/env python3
"""
Простой и надежный скрипт для получения содержимого веб-страницы
Использует curl для загрузки и обработки ошибок
"""

import subprocess
import sys
import re
from urllib.parse import urlparse
from html.parser import HTMLParser

class SimpleHTMLParser(HTMLParser):
    """Простой парсер для извлечения текста из HTML"""
    def __init__(self):
        super().__init__()
        self.text = []
        self.ignore_tags = {'script', 'style', 'head', 'meta', 'link'}
        self.ignore_content = False
    
    def handle_starttag(self, tag, attrs):
        if tag in self.ignore_tags:
            self.ignore_content = True
    
    def handle_endtag(self, tag):
        if tag in self.ignore_tags:
            self.ignore_content = False
    
    def handle_data(self, data):
        if not self.ignore_content and data.strip():
            self.text.append(data.strip())
    
    def get_clean_text(self):
        """Возвращает очищенный текст без лишних пробелов"""
        text = ' '.join(self.text)
        # Убираем множественные пробелы и переносы строк
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

def fetch_page_content(url, timeout=30, user_agent=None):
    """
    Получает содержимое веб-страницы с помощью curl
    
    Args:
        url (str): URL страницы для загрузки
        timeout (int): Таймаут в секундах
        user_agent (str): Пользовательский User-Agent
    
    Returns:
        dict: Словарь с результатом {'success': bool, 'content': str, 'error': str}
    """
    
    # Валидация URL
    try:
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            return {
                'success': False,
                'content': None,
                'error': f"Неверный URL: {url}"
            }
    except Exception as e:
        return {
            'success': False,
            'content': None,
            'error': f"Ошибка парсинга URL: {str(e)}"
        }
    
    # Подготовка команды curl
    curl_cmd = [
        'curl',
        '--silent',           # Тихий режим (без прогресс-бара)
        '--show-error',       # Показывать ошибки
        '--max-time', str(timeout),  # Таймаут
        '--connect-timeout', '10',   # Таймаут подключения
        '--retry', '2',       # Количество попыток
        '--retry-delay', '1', # Задержка между попытками
        '--location',         # Следовать редиректам
        '--compressed',       # Поддержка сжатия
        '--fail',            # Возвращать ошибку при HTTP ошибках
        '--user-agent', user_agent or 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
    ]
    
    # Добавляем URL в конец команды
    curl_cmd.append(url)
    
    try:
        # Выполняем команду curl
        result = subprocess.run(
            curl_cmd,
            capture_output=True,
            text=True,
            timeout=timeout + 5  # Дополнительный таймаут для subprocess
        )
        
        # Проверяем результат
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else f"curl вернул код {result.returncode}"
            return {
                'success': False,
                'content': None,
                'error': f"Ошибка curl: {error_msg}"
            }
        
        content = result.stdout.strip()
        
        if not content:
            return {
                'success': False,
                'content': None,
                'error': "Получен пустой ответ от сервера"
            }
        
        return {
            'success': True,
            'content': content,
            'error': None
        }
        
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'content': None,
            'error': f"Превышен таймаут ({timeout} секунд)"
        }
    except FileNotFoundError:
        return {
            'success': False,
            'content': None,
            'error': "curl не найден в системе. Установите curl: sudo apt-get install curl"
        }
    except Exception as e:
        return {
            'success': False,
            'content': None,
            'error': f"Неожиданная ошибка: {str(e)}"
        }

def extract_text_from_html(html_content):
    """
    Извлекает читаемый текст из HTML
    
    Args:
        html_content (str): HTML содержимое
    
    Returns:
        str: Очищенный текст
    """
    try:
        parser = SimpleHTMLParser()
        parser.feed(html_content)
        return parser.get_clean_text()
    except Exception as e:
        return f"Ошибка парсинга HTML: {str(e)}"

def main():
    """Основная функция"""
    if len(sys.argv) != 2:
        print("Использование: python fetch_page.py <URL>")
        print("Пример: python fetch_page.py https://example.com")
        sys.exit(1)
    
    url = sys.argv[1]
    print(f"Загружаю содержимое страницы: {url}")
    print("-" * 50)
    
    # Получаем содержимое
    result = fetch_page_content(url)
    
    if not result['success']:
        print(f"❌ Ошибка: {result['error']}")
        sys.exit(1)
    
    print("✅ Страница успешно загружена!")
    print(f"📄 Размер содержимого: {len(result['content'])} символов")
    print("-" * 50)
    
    # Извлекаем текст
    text_content = extract_text_from_html(result['content'])
    
    print("📝 Извлеченный текст:")
    print("=" * 50)
    print(text_content[:1000] + "..." if len(text_content) > 1000 else text_content)
    print("=" * 50)
    
    # Сохраняем в файл
    try:
        with open('page_content.txt', 'w', encoding='utf-8') as f:
            f.write(f"URL: {url}\n")
            f.write("=" * 50 + "\n")
            f.write("HTML содержимое:\n")
            f.write(result['content'])
            f.write("\n\n" + "=" * 50 + "\n")
            f.write("Извлеченный текст:\n")
            f.write(text_content)
        
        print(f"💾 Содержимое сохранено в файл: page_content.txt")
        
    except Exception as e:
        print(f"⚠️  Не удалось сохранить в файл: {str(e)}")

if __name__ == "__main__":
    main()