import os
import math
import requests
import random
import uuid 
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv
from flask import Flask, request, render_template, make_response, jsonify
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from app.models import db, PlaylistImage 
from flask_migrate import Migrate  # 追加

# .envファイルを読み込む
load_dotenv()

# Spotify APIの認証情報を環境変数から取得
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

# 認証
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET))

app = Flask(__name__)
app.config.from_object('config.Config')
db.init_app(app)

# Flask-Migrateの設定
migrate = Migrate(app, db)

# UUIDを使ってユニークな画像パスを作成する関数
def generate_unique_image_path():
    return f'static/mosaic_image_{uuid.uuid4().hex}.jpg'

def get_playlist_images(playlist_url, remove_duplicates=False):
    try:
        playlist_id = playlist_url.split("/")[-1].split("?")[0]
        playlist_details = sp.playlist(playlist_id)
        playlist_name = playlist_details['name']
        playlist_description = playlist_details['description']
        playlist_owner = playlist_details['owner']['display_name']
        playlist_owner_link = playlist_details['owner']['external_urls']['spotify']  # オーナーのリンクを取得
        playlist_link = playlist_details['external_urls']['spotify']

        limit = 100  # Spotify API の制限に合わせて100に設定
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
            img = img.resize((150, 150))
            images.append((img, data))

        return images, playlist_name, playlist_description, playlist_owner, playlist_owner_link, playlist_link
    
    except Exception as e:
        print(f"Error: {e}")
        return [], None, None, None, None, None

def create_square_mosaic(images, shuffle=False):
    if not images:
        raise ValueError("No images to create a mosaic.") 

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

@app.route('/load_more_images')
def load_more_images():
    offset = int(request.args.get('offset', 0))
    images_query = PlaylistImage.query.filter_by(hide_from_history=False).order_by(PlaylistImage.created_at.desc()).offset(offset).limit(5)
    images = []
    for image in images_query:
        images.append({
            'playlist_name': image.playlist_name,
            'playlist_link': image.playlist_link,
            'playlist_owner': image.playlist_owner,
            'playlist_owner_link': image.playlist_owner_link,
            'image_url': image.image_url
        })

    has_more = len(images) == 5  # 取得した画像が5つなら、さらにデータがある可能性がある
    return jsonify({'images': images, 'has_more': has_more})

# @app.route('/', methods=['GET', 'POST'])
# def index():
#     playlist_name = None
#     playlist_description = None
#     playlist_owner = None
#     playlist_owner_link = None
#     playlist_link = None

#     if request.method == 'POST':
#         # フォームのデータを取得
#         playlist_url = request.form['playlist_url']
#         shuffle = 'shuffle' in request.form 
#         remove_duplicates = 'remove_duplicates' in request.form
#         hide_from_history = 'hide_from_history' in request.form
        
#         # プレイリスト画像の取得・作成
#         images, playlist_name, playlist_description, playlist_owner, playlist_owner_link, playlist_link = get_playlist_images(playlist_url, remove_duplicates)
#         mosaic_image = create_square_mosaic(images, shuffle)
#         mosaic_image_path = generate_unique_image_path()  # ユニークなファイルパスを生成
#         mosaic_image.save(mosaic_image_path)
        
#         # データベースに保存
#         playlist_image = PlaylistImage(
#             playlist_name=playlist_name,
#             playlist_link=playlist_link,
#             playlist_owner=playlist_owner,
#             playlist_owner_link=playlist_owner_link,  
#             image_url=mosaic_image_path,
#             hide_from_history=hide_from_history  # 非表示フラグを保存
#         )
#         db.session.add(playlist_image)
#         db.session.commit()
        
#         # POST後のレスポンスに最新の履歴を反映
#         recent_images = PlaylistImage.query.filter_by(hide_from_history=False).order_by(PlaylistImage.created_at.desc()).limit(5).all()
#         response = make_response(render_template('index.html', mosaic_image_url=mosaic_image_path, shuffle=shuffle, remove_duplicates=remove_duplicates, playlist_name=playlist_name, playlist_description=playlist_description, playlist_owner=playlist_owner, playlist_owner_link=playlist_owner_link, playlist_link=playlist_link, recent_images=recent_images))
#         response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
#         response.headers['Pragma'] = 'no-cache'
#         response.headers['Expires'] = '0'
#         return response

#     # 非表示フラグが立っていないもののみ表示する
#     recent_images = PlaylistImage.query.filter_by(hide_from_history=False).order_by(PlaylistImage.created_at.desc()).limit(5).all()
#     response = make_response(render_template('index.html', recent_images=recent_images, mosaic_image_url=None, shuffle=False, remove_duplicates=False, playlist_name=playlist_name, playlist_description=playlist_description, playlist_owner=playlist_owner, playlist_owner_link=playlist_owner_link, playlist_link=playlist_link))
#     response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
#     response.headers['Pragma'] = 'no-cache'
#     response.headers['Expires'] = '0'
#     return response

# if __name__ == '__main__':

from flask import Flask, request, render_template, make_response, jsonify, redirect

@app.route('/', methods=['GET', 'POST'])
def index():
    return redirect("https://jacket-collection.vercel.app/", code=302)

if __name__ == '__main__':
    with app.app_context():
        from flask_migrate import upgrade
        upgrade()

    app.run(debug=True)
    # アプリケーション起動時に自動的にマイグレーションを適用する
    with app.app_context():
        from flask_migrate import upgrade
        upgrade()

    app.run(debug=True)