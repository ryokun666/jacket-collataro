import os
import math
import requests
import random
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv
from flask import Flask, request, render_template, make_response
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# .envファイルを読み込む
load_dotenv()

# Spotify APIの認証情報を環境変数から取得
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

# 認証
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET))

app = Flask(__name__)

# アプリケーション起動時にmosaic_image.jpgを削除
mosaic_image_path = 'static/mosaic_image.jpg'
if os.path.exists(mosaic_image_path):
    os.remove(mosaic_image_path)

def get_playlist_images(playlist_url, remove_duplicates=False):
    # プレイリストIDを抽出
    playlist_id = playlist_url.split("/")[-1].split("?")[0]

    # プレイリストのトラックを取得
    results = sp.playlist_tracks(playlist_id)
    tracks = results['items']

    # 画像とメタデータのリスト
    image_data = []

    seen_urls = set()  # 重複を除くためのセット

    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])

    for item in tracks:
        track = item['track']
        if track['album']['images']:
            url = track['album']['images'][0]['url']
            if remove_duplicates and url in seen_urls:
                continue
            seen_urls.add(url)
            image_data.append({
                'url': url,
                'artist': track['album']['artists'][0]['name'],
                'album_release_date': track['album']['release_date'],
                'track_name': track['name']
            })

    # 画像のダウンロードと正方形画像への加工
    images = []
    for data in image_data:
        response = requests.get(data['url'])
        img = Image.open(BytesIO(response.content))
        img = img.resize((300, 300))  # サイズは適宜調整してください
        images.append((img, data))

    return images

def create_square_mosaic(images, shuffle=False, sort_by=None):
    if shuffle:
        random.shuffle(images)
    elif sort_by == 'artist':
        images.sort(key=lambda x: x[1]['artist'])
    elif sort_by == 'album_release_date':
        images.sort(key=lambda x: x[1]['album_release_date'])
    elif sort_by == 'track_name':
        images.sort(key=lambda x: x[1]['track_name'])
    
    num_images = len(images)
    num_cols = int(math.sqrt(num_images))
    num_rows = math.ceil(num_images / num_cols)
    width, height = images[0][0].size
    mosaic_size = min(num_cols, num_rows)
    
    mosaic = Image.new('RGB', (mosaic_size * width, mosaic_size * height))

    for index, (img, _) in enumerate(images[:mosaic_size * mosaic_size]):
        row, col = divmod(index, mosaic_size)
        mosaic.paste(img, (col * width, row * height))

    return mosaic

@app.route('/', methods=['GET', 'POST'])
def index():
    selected_sort_by = None
    if request.method == 'POST':
        playlist_url = request.form['playlist_url']
        shuffle = 'shuffle' in request.form
        sort_by = request.form.get('sort_by', None)
        remove_duplicates = 'remove_duplicates' in request.form
        images = get_playlist_images(playlist_url, remove_duplicates)
        mosaic_image = create_square_mosaic(images, shuffle, sort_by)
        mosaic_image_path = 'static/mosaic_image.jpg'
        mosaic_image.save(mosaic_image_path)
        selected_sort_by = sort_by
        response = make_response(render_template('index.html', mosaic_image_url=mosaic_image_path, selected_sort_by=selected_sort_by, shuffle=shuffle, remove_duplicates=remove_duplicates))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    # GETリクエスト時のキャッシュ削除ヘッダーの設定
    response = make_response(render_template('index.html', mosaic_image_url=None, selected_sort_by=selected_sort_by, shuffle=False, remove_duplicates=False))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

if __name__ == '__main__':
    app.run(debug=True)
