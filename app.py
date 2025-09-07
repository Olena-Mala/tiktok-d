from flask import Flask, request, jsonify, render_template, send_from_directory
import requests
from datetime import datetime
import os
import re

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Тепер тільки російська мова
LANGUAGES = {
    'ru': {
        'title': 'Скачать видео из TikTok без водяного знака',
        'description': 'Бесплатное скачивание видео из TikTok без водяного знака в высоком качестве. Быстро, просто, без регистрации!',
        'keywords': 'скачать тикток, tiktok скачать, без водяного знака, видео тикток, tiktok download',
        'placeholder': 'Вставьте ссылку на видео TikTok...',
        'download_btn': 'Скачать видео',
        'loading': 'Обработка запроса...',
        'error_url': 'Пожалуйста, введите ссылку на видео',
        'success': 'Видео готово к скачиванию!',
        'error_general': 'Ошибка обработки. Попробуйте другую ссылку',
        'watermark': 'без водяного знака',
        'language': 'Русский'
    }
}

def get_tiktok_video(url):
    """Функція для отримання відео"""
    apis = [
        f"https://api.tikmate.app/api/download?url={url}",
        f"https://api.tiktokdownload.net/download?url={url}",
        f"https://www.tikwm.com/api/?url={url}",
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for api_url in apis:
        try:
            response = requests.get(api_url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if data.get('video_url'):
                    return {'success': True, 'video_url': data['video_url']}
                elif data.get('data') and data['data'].get('play'):
                    return {'success': True, 'video_url': data['data']['play']}
                elif data.get('wmplay'):
                    return {'success': True, 'video_url': data['wmplay']}
        except:
            continue
    
    return {'success': False, 'error': 'Не удалось обработать видео'}

@app.route('/')
def index():
    return render_template('index.html', lang=LANGUAGES['ru'])

# ====== НОВЫЕ СТРАНИЦЫ ======
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

@app.route('/api/download')
def download_video():
    tiktok_url = request.args.get('url')
    lang = LANGUAGES['ru']
    
    if not tiktok_url or 'tiktok.com' not in tiktok_url:
        return jsonify({'success': False, 'error': lang['error_url']})
    
    result = get_tiktok_video(tiktok_url)
    
    if result['success']:
        return jsonify({
            'success': True,
            'video_url': result['video_url'],
            'title': f'tiktok_video_{datetime.now().strftime("%Y%m%d_%H%M%S")}.mp4'
        })
    else:
        return jsonify({'success': False, 'error': lang['error_general']})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
# ====== SEO ФАЙЛЫ ======
@app.route('/robots.txt')
def robots():
    return send_from_directory('.', 'robots.txt')

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory('.', 'sitemap.xml')

# ====== ОБРАБОТКА ОШИБОК ======
@app.errorhandler(404)
def not_found(error):
    return render_template('index.html', lang=LANGUAGES['ru']), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('index.html', lang=LANGUAGES['ru']), 500
