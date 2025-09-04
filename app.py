from flask import Flask, request, jsonify, render_template, session
from tiktok_downloader import snaptik
from datetime import datetime
import os

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
    
    try:
        video_data = snaptik(tiktok_url)
        
        for video in video_data:
            if LANGUAGES[lang]['watermark'] in video.quality.lower():
                return jsonify({
                    'success': True,
                    'video_url': video.url,
                    'title': f'tiktok_video_{datetime.now().strftime("%Y%m%d_%H%M%S")}.mp4',
                    'quality': 'HD ' + LANGUAGES[lang]['watermark']
                })
        
        return jsonify({'success': False, 'error': LANGUAGES[lang]['error_general']})
    
    except Exception as e:
        return jsonify({'success': False, 'error': LANGUAGES[lang]['error_general']})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)