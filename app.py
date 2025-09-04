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

def get_tiktok_video(url):
    """Спробуємо всі можливі API послідовно"""
    apis = [
        # Список робочих API
        f"https://api.tikmate.app/api/download?url={url}",
        f"https://api.tiktokdownload.net/download?url={url}",
        f"https://tikdown.org/api?url={url}",
        f"https://www.tikwm.com/api/?url={url}",
        f"https://tiktok-downloader-download-tiktok-videos-without-watermark.p.rapidapi.com/vid/index?url={url}"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for api_url in apis:
        try:
            print(f"Trying API: {api_url}")
            response = requests.get(api_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Перевіряємо різні формати відповідей
                if data.get('video_url'):
                    return {'success': True, 'video_url': data['video_url']}
                elif data.get('data') and data['data'].get('play'):
                    return {'success': True, 'video_url': data['data']['play']}
                elif data.get('wmplay'):
                    return {'success': True, 'video_url': data['wmplay']}
                elif data.get('nolwmplay'):
                    return {'success': True, 'video_url': data['nolwmplay']}
                elif data.get('url'):
                    return {'success': True, 'video_url': data['url']}
                    
        except Exception as e:
            print(f"API failed: {e}")
            continue
    
    # Якщо всі API не спрацювали, спробуємо через парсинг
    try:
        return extract_video_directly(url)
    except:
        return {'success': False, 'error': 'Все API временно не работают'}

def extract_video_directly(url):
    """Спроба прямого парсингу"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        html_content = response.text
        
        # Шукаємо посилання на відео в HTML
        video_url_match = re.search(r'"playAddr":"(https?://[^"]+\.mp4[^"]*)"', html_content)
        if video_url_match:
            video_url = video_url_match.group(1).replace('\\u002F', '/')
            return {'success': True, 'video_url': video_url}
            
    except Exception as e:
        print(f"Direct parsing failed: {e}")
    
    return {'success': False, 'error': 'Не удалось обработать видео'}

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
    
    if 'tiktok.com' not in tiktok_url:
        return jsonify({'success': False, 'error': 'Неверная ссылка TikTok'})
    
    result = get_tiktok_video(tiktok_url)
    
    if result['success']:
        return jsonify({
            'success': True,
            'video_url': result['video_url'],
            'title': f'tiktok_video_{datetime.now().strftime("%Y%m%d_%H%M%S")}.mp4',
            'quality': 'HD без водяного знака'
        })
    else:
        return jsonify({
            'success': False, 
            'error': 'Не удалось загрузить видео. Попробуйте: 1) Другое видео 2) Через 5 минут 3) Другой аккаунт TikTok'
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
