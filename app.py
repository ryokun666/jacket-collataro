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
    try:
        playlist_id = playlist_url.split("/")[-1].split("?")[0]
        playlist_details = sp.playlist(playlist_id)
        playlist_name = playlist_details['name']
        playlist_description = playlist_details['description']
        playlist_owner = playlist_details['owner']['display_name']
        playlist_link = playlist_details['external_urls']['spotify']

        limit = 100  # ここで取得するトラック数を制限
        offset = 0
        tracks = []
        while True:
            results = sp.playlist_tracks(playlist_id, limit=limit, offset=offset)
            if not results['items']:
                break
            tracks.extend(results['items'])
            offset += limit

        image_data = []
        seen_urls = set()

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

        images = []
        for data in image_data:
            response = requests.get(data['url'])
            img = Image.open(BytesIO(response.content))
            img = img.resize((300, 300))
            images.append((img, data))

        return images, playlist_name, playlist_description, playlist_owner, playlist_link
    
    except Exception as e:
        print(f"Error: {e}")
        return [], None, None, None, None

    try:
        # プレイリストIDを抽出
        playlist_id = playlist_url.split("/")[-1].split("?")[0]

        # プレイリストの詳細を取得
        playlist_details = sp.playlist(playlist_id)
        playlist_name = playlist_details['name']
        playlist_description = playlist_details['description']
        playlist_owner = playlist_details['owner']['display_name']
        playlist_link = playlist_details['external_urls']['spotify']
        
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

        return images, playlist_name, playlist_description, playlist_owner, playlist_link
    
    except Exception as e:
        print(f"Error: {e}")
        return [], None, None, None, None


def create_square_mosaic(images, shuffle=False):
    if shuffle:
        random.shuffle(images)
    
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
    playlist_name = None
    playlist_description = None
    playlist_owner = None
    playlist_link = None

    if request.method == 'POST':
        playlist_url = request.form['playlist_url']
        shuffle = 'shuffle' in request.form 
        remove_duplicates = 'remove_duplicates' in request.form
        images, playlist_name, playlist_description, playlist_owner, playlist_link = get_playlist_images(playlist_url, remove_duplicates)
        mosaic_image = create_square_mosaic(images, shuffle)
        mosaic_image_path = 'static/mosaic_image.jpg'
        mosaic_image.save(mosaic_image_path)
        response = make_response(render_template('index.html', mosaic_image_url=mosaic_image_path, shuffle=shuffle, remove_duplicates=remove_duplicates, playlist_name=playlist_name, playlist_description=playlist_description, playlist_owner=playlist_owner, playlist_link=playlist_link))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    response = make_response(render_template('index.html', mosaic_image_url=None, shuffle=False, remove_duplicates=False, playlist_name=playlist_name, playlist_description=playlist_description, playlist_owner=playlist_owner, playlist_link=playlist_link))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

if __name__ == '__main__':
    app.run(debug=True)
