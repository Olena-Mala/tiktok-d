from flask import Flask, request, jsonify, render_template, session
import requests
from datetime import datetime
import os
import re

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Налаштування мов
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
    },
    'en': {
        'title': 'Download TikTok Video Without Watermark',
        'description': 'Free TikTok video download without watermark in high quality. Fast, easy, no registration required!',
        'keywords': 'tiktok download, download tiktok video, no watermark, tiktok saver, tiktok video download',
        'placeholder': 'Paste TikTok video link...',
        'download_btn': 'Download Video',
        'loading': 'Processing request...',
        'error_url': 'Please enter video link',
        'success': 'Video ready for download!',
        'error_general': 'Processing error. Try another link',
        'watermark': 'without watermark',
        'language': 'English'
    }
}

def download_tiktok_video(url):
    """Альтернативний метод завантаження через API"""
    try:
        # Використовуємо сторонній API сервіс
        api_url = f"https://api.tiktokdownload.net/download?url={url}"
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('video_url'):
                return {
                    'success': True,
                    'video_url': data['video_url'],
                    'title': f'tiktok_video_{datetime.now().strftime("%Y%m%d_%H%M%S")}.mp4'
                }
        
        # Резервний метод
        api_url_2 = f"https://api.tikmate.app/api/download?url={url}"
        response_2 = requests.get(api_url_2, timeout=10)
        
        if response_2.status_code == 200:
            data_2 = response_2.json()
            if data_2.get('video_url'):
                return {
                    'success': True,
                    'video_url': data_2['video_url'],
                    'title': f'tiktok_video_{datetime.now().strftime("%Y%m%d_%H%M%S")}.mp4'
                }
        
        return {'success': False, 'error': 'Не вдалося обробити видео'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.route('/')
def index():
    lang = request.args.get('lang', 'ru')
    session['lang'] = lang
    return render_template('index.html', lang=LANGUAGES[lang])

@app.route('/set_language/<language>')
def set_language(language):
    if language in LANGUAGES:
        session['lang'] = language
    return jsonify({'success': True})

@app.route('/api/download')
def download_video():
    tiktok_url = request.args.get('url')
    lang = session.get('lang', 'ru')
    
    if not tiktok_url:
        return jsonify({'success': False, 'error': LANGUAGES[lang]['error_url']})
    
    # Перевіряємо чи це посилання TikTok
    if 'tiktok.com' not in tiktok_url:
        return jsonify({'success': False, 'error': 'Неверная ссылка TikTok'})
    
    result = download_tiktok_video(tiktok_url)
    
    if result['success']:
        return jsonify({
            'success': True,
            'video_url': result['video_url'],
            'title': result['title'],
            'quality': 'HD без водяного знака'
        })
    else:
        return jsonify({'success': False, 'error': LANGUAGES[lang]['error_general']})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
