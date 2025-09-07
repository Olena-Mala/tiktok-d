from flask import Flask, request, jsonify, render_template, send_from_directory
import requests
from datetime import datetime
import os
import re
import logging
from urllib.parse import urlparse, quote
from functools import wraps
import time
import threading
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def keep_alive():
    """Будильник для сайта - звоним себе каждые 5 минут"""
    while True:
        try:
            # ЗАМЕНИТЕ НА ВАШ РЕАЛЬНЫЙ АДРЕС!
            requests.get('https://tiktok-downloader-9e9d.onrender.com/health', timeout=10)
            logger.info(f"Будильник сработал! {datetime.now()}")
        except Exception as e:
            logger.error(f"Будильник не сработал: {e}")
        time.sleep(300)  # Спим 5 минут

# Включаем будильник только для реального сайта
if not os.environ.get('WERKZEUG_RUN_MAIN'):
    keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
    keep_alive_thread.start()
    logger.info("Будильник включен!")

# Кеш для хранения результатов запросов (в памяти, для продакшена лучше использовать Redis)
request_cache = {}
CACHE_TIMEOUT = 300  # 5 минут

# Теперь только русский язык
LANGUAGES = {
    'ru': {
        'title': 'Скачать видео из TikTok без водяного знака',
        'description': 'Бесплатное скачивание видео из TikTok без водяного знака в высоком качестве. Быстро, просто, без регистрации!',
        'keywords': 'скачать тикток, tiktok скачать, без водяного знака, видео тикток, tiktok download',
        'placeholder': 'Вставьте ссылку на видео TikTok...',
        'download_btn': 'Скачать видео',
        'loading': 'Обработка запроса...',
        'error_url': 'Пожалуйста, введите корректную ссылку на видео TikTok',
        'error_invalid_url': 'Некорректная ссылка TikTok',
        'error_timeout': 'Превышено время ожидания. Попробуйте позже',
        'error_api': 'Сервис временно недоступен. Попробуйте другую ссылку',
        'success': 'Видео готово к скачиванию!',
        'error_general': 'Ошибка обработки. Попробуйте другую ссылку',
        'watermark': 'без водяного знака',
        'language': 'Русский'
    }
}

def cache_decorator(timeout=300):
    """Декоратор для кеширования результатов функций"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            current_time = time.time()
            
            # Проверяем есть ли результат в кеше и не устарел ли он
            if cache_key in request_cache:
                result, timestamp = request_cache[cache_key]
                if current_time - timestamp < timeout:
                    logger.info(f"Using cached result for {cache_key}")
                    return result
            
            # Выполняем функцию и сохраняем результат
            result = func(*args, **kwargs)
            request_cache[cache_key] = (result, current_time)
            return result
        return wrapper
    return decorator

def is_valid_tiktok_url(url):
    """Проверяет, является ли ссылка валидным TikTok URL"""
    if not url or len(url) > 200:
        return False
    
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return False
        
        # Паттерны для валидации TikTok ссылок
        patterns = [
            r'^https?://(www\.)?tiktok\.com/@[^/]+/video/\d+',
            r'^https?://(www\.)?tiktok\.com/t/[^/]+/\d+',
            r'^https?://vm\.tiktok\.com/[A-Za-z0-9]+',
            r'^https?://vt\.tiktok\.com/[A-Za-z0-9]+',
            r'^https?://(www\.)?tiktok\.com/v/\d+'
        ]
        
        return any(re.match(pattern, url) for pattern in patterns)
    except:
        return False

def sanitize_url(url):
    """Очищает и нормализует URL"""
    if not url:
        return None
    
    # Убираем лишние пробелы
    url = url.strip()
    
    # Добавляем https:// если отсутствует
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    return url

@cache_decorator(timeout=300)
def get_tiktok_video(url):
    """Функция для получения видео с кешированием"""
    apis = [
        {
            'url': f"https://api.tikmate.app/api/download?url={quote(url)}",
            'parser': lambda data: data.get('video_url')
        },
        {
            'url': f"https://api.tiktokdownload.net/download?url={quote(url)}",
            'parser': lambda data: data.get('data', {}).get('play') if data.get('data') else None
        },
        {
            'url': f"https://www.tikwm.com/api/?url={quote(url)}",
            'parser': lambda data: data.get('wmplay') or (data.get('data', {}).get('play') if data.get('data') else None)
        },
        {
            'url': f"https://api.douyin.wtf/api?url={quote(url)}",
            'parser': lambda data: data.get('nwm_video_url') or data.get('video_data', {}).get('nwm_video_url')
        }
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json',
        'Referer': 'https://www.tiktok.com/'
    }
    
    for api in apis:
        try:
            logger.info(f"Trying API: {api['url']}")
            response = requests.get(api['url'], headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                video_url = api['parser'](data)
                
                if video_url:
                    # Проверяем, что полученная ссылка валидна
                    if video_url.startswith(('http://', 'https://')):
                        logger.info(f"Successfully got video from API: {api['url']}")
                        return {
                            'success': True, 
                            'video_url': video_url,
                            'source': api['url']
                        }
                    else:
                        logger.warning(f"Invalid video URL from API: {video_url}")
            
            time.sleep(0.5)  # Небольшая задержка между запросами
            
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout for API: {api['url']}")
            continue
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {api['url']}: {e}")
            continue
        except ValueError as e:
            logger.error(f"JSON parse error for {api['url']}: {e}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error for {api['url']}: {e}")
            continue
    
    return {'success': False, 'error': 'Не удалось обработать видео'}

@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html', lang=LANGUAGES['ru'])

@app.route('/api/download')
def download_video():
    """API endpoint для скачивания видео"""
    tiktok_url = request.args.get('url')
    lang = LANGUAGES['ru']
    
    # Валидация URL
    if not tiktok_url:
        return jsonify({'success': False, 'error': lang['error_url']})
    
    # Санитизация и нормализация URL
    tiktok_url = sanitize_url(tiktok_url)
    
    if not is_valid_tiktok_url(tiktok_url):
        return jsonify({'success': False, 'error': lang['error_invalid_url']})
    
    logger.info(f"Processing TikTok URL: {tiktok_url}")
    
    try:
        result = get_tiktok_video(tiktok_url)
        
        if result['success']:
            return jsonify({
                'success': True,
                'video_url': result['video_url'],
                'title': f'tiktok_video_{datetime.now().strftime("%Y%m%d_%H%M%S")}.mp4',
                'source': result.get('source', 'unknown')
            })
        else:
            return jsonify({'success': False, 'error': lang['error_general']})
            
    except requests.exceptions.Timeout:
        logger.error(f"Timeout processing URL: {tiktok_url}")
        return jsonify({'success': False, 'error': lang['error_timeout']})
    except Exception as e:
        logger.error(f"Error processing URL {tiktok_url}: {e}")
        return jsonify({'success': False, 'error': lang['error_api']})

# ====== СТАТИЧЕСКИЕ СТРАНИЦЫ ======
@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/howto')
def howto():
    return render_template('howto.html')

@app.route('/about')
def about():
    return render_template('about.html')

# ====== SEO ФАЙЛЫ ======
@app.route('/robots.txt')
def robots():
    content = '''User-agent: *
Allow: /
Disallow: /admin/
Disallow: /api/

Sitemap: https://tiktok-downloader-9e9d.onrender.com/sitemap.xml'''
    return content, 200, {'Content-Type': 'text/plain'}

@app.route('/sitemap.xml')
def sitemap():
    base_url = 'https://tiktok-downloader-9e9d.onrender.com'
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    content = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>{base_url}</loc>
        <lastmod>{current_date}</lastmod>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>{base_url}/privacy</loc>
        <lastmod>{current_date}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>{base_url}/terms</loc>
        <lastmod>{current_date}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>{base_url}/howto</loc>
        <lastmod>{current_date}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.9</priority>
    </url>
    <url>
        <loc>{base_url}/about</loc>
        <lastmod>{current_date}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.7</priority>
    </url>
</urlset>'''
    return content, 200, {'Content-Type': 'application/xml'}

# ====== КЕШИРОВАНИЕ ======
@app.after_request
def add_header(response):
    """
    Добавляет заголовки кэширования для статических файлов.
    """
    if request.path == '/' or request.path.endswith(('.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.webp')):
        response.cache_control.max_age = 300
        response.cache_control.public = True
        response.cache_control.must_revalidate = True
    return response

# ====== ОБРАБОТКА ОШИБОК ======
@app.errorhandler(404)
def not_found(error):
    return render_template('index.html', lang=LANGUAGES['ru']), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Server error: {error}")
    return render_template('index.html', lang=LANGUAGES['ru']), 500

@app.errorhandler(429)
def too_many_requests(error):
    return jsonify({'success': False, 'error': 'Слишком много запросов. Попробуйте позже'}), 429

# ====== СТАТИЧЕСКИЕ ФАЙЛЫ ======
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

# ====== HEALTH CHECK ======
@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
