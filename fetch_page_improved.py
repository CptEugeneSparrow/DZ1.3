#!/usr/bin/env python3
"""
Улучшенный скрипт для получения содержимого веб-страницы
Использует curl для загрузки и BeautifulSoup для лучшего извлечения текста
"""

import subprocess
import sys
import re
from urllib.parse import urlparse
from html.parser import HTMLParser

class ImprovedHTMLParser(HTMLParser):
    """Улучшенный парсер для извлечения текста из HTML"""
    def __init__(self):
        super().__init__()
        self.text = []
        self.ignore_tags = {
            'script', 'style', 'head', 'meta', 'link', 'noscript',
            'iframe', 'embed', 'object', 'applet', 'canvas'
        }
        self.ignore_content = False
        self.in_body = False
        self.current_tag = None
    
    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        
        if tag == 'body':
            self.in_body = True
        elif tag in self.ignore_tags:
            self.ignore_content = True
        elif tag in ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'span', 'li', 'td', 'th']:
            # Добавляем перенос строки перед блочными элементами
            if self.text and not self.text[-1].endswith('\n'):
                self.text.append('\n')
    
    def handle_endtag(self, tag):
        if tag == 'body':
            self.in_body = False
        elif tag in self.ignore_tags:
            self.ignore_content = False
        elif tag in ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'li']:
            # Добавляем перенос строки после блочных элементов
            if self.text and not self.text[-1].endswith('\n'):
                self.text.append('\n')
    
    def handle_data(self, data):
        if self.in_body and not self.ignore_content and data.strip():
            # Очищаем данные от лишних пробелов
            clean_data = re.sub(r'\s+', ' ', data.strip())
            if clean_data:
                self.text.append(clean_data)
    
    def get_clean_text(self):
        """Возвращает очищенный текст с правильными переносами строк"""
        text = ' '.join(self.text)
        # Убираем множественные пробелы и переносы строк
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
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
    Извлекает читаемый текст из HTML с улучшенной обработкой
    
    Args:
        html_content (str): HTML содержимое
    
    Returns:
        str: Очищенный текст
    """
    try:
        parser = ImprovedHTMLParser()
        parser.feed(html_content)
        return parser.get_clean_text()
    except Exception as e:
        return f"Ошибка парсинга HTML: {str(e)}"

def extract_metadata_from_html(html_content):
    """
    Извлекает метаданные из HTML
    
    Args:
        html_content (str): HTML содержимое
    
    Returns:
        dict: Словарь с метаданными
    """
    metadata = {}
    
    # Извлекаем заголовок
    title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
    if title_match:
        metadata['title'] = title_match.group(1).strip()
    
    # Извлекаем описание
    desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', html_content, re.IGNORECASE)
    if desc_match:
        metadata['description'] = desc_match.group(1).strip()
    
    # Извлекаем ключевые слова
    keywords_match = re.search(r'<meta[^>]*name=["\']keywords["\'][^>]*content=["\']([^"\']*)["\']', html_content, re.IGNORECASE)
    if keywords_match:
        metadata['keywords'] = keywords_match.group(1).strip()
    
    return metadata

def main():
    """Основная функция"""
    if len(sys.argv) != 2:
        print("Использование: python fetch_page_improved.py <URL>")
        print("Пример: python fetch_page_improved.py https://example.com")
        sys.exit(1)
    
    url = sys.argv[1]
    print(f"🔍 Загружаю содержимое страницы: {url}")
    print("=" * 60)
    
    # Получаем содержимое
    result = fetch_page_content(url)
    
    if not result['success']:
        print(f"❌ Ошибка: {result['error']}")
        sys.exit(1)
    
    print("✅ Страница успешно загружена!")
    print(f"📄 Размер содержимого: {len(result['content'])} символов")
    print("-" * 60)
    
    # Извлекаем метаданные
    metadata = extract_metadata_from_html(result['content'])
    if metadata:
        print("📋 Метаданные:")
        for key, value in metadata.items():
            print(f"   {key}: {value}")
        print("-" * 60)
    
    # Извлекаем текст
    text_content = extract_text_from_html(result['content'])
    
    print("📝 Извлеченный текст:")
    print("=" * 60)
    print(text_content[:1500] + "..." if len(text_content) > 1500 else text_content)
    print("=" * 60)
    
    # Сохраняем в файлы
    try:
        # Сохраняем HTML
        with open('page_content.html', 'w', encoding='utf-8') as f:
            f.write(f"<!-- URL: {url} -->\n")
            f.write(result['content'])
        
        # Сохраняем текст
        with open('page_text_improved.txt', 'w', encoding='utf-8') as f:
            f.write(f"URL: {url}\n")
            f.write("=" * 60 + "\n")
            if metadata:
                f.write("МЕТАДАННЫЕ:\n")
                for key, value in metadata.items():
                    f.write(f"{key}: {value}\n")
                f.write("-" * 60 + "\n")
            f.write("ИЗВЛЕЧЕННЫЙ ТЕКСТ:\n")
            f.write("=" * 60 + "\n")
            f.write(text_content)
        
        print(f"💾 Файлы сохранены:")
        print(f"   📄 page_content.html (HTML содержимое)")
        print(f"   📝 page_text_improved.txt (улучшенный текст)")
        
    except Exception as e:
        print(f"⚠️  Не удалось сохранить в файл: {str(e)}")

if __name__ == "__main__":
    main()