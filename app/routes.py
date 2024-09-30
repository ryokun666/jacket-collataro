from flask import render_template, request
from app import app, db
from app.models import PlaylistImage

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # フォームからのデータを処理して画像を生成
        # ここでプレイリスト情報と生成した画像のURLを取得
        # 例:
        playlist_name = "サンプルプレイリスト"
        playlist_link = "https://example.com"
        playlist_owner = "ユーザー名"
        mosaic_image_path = "/static/mosaic_image.jpg"

        # データベースに保存
        playlist_image = PlaylistImage(
            playlist_name=playlist_name,
            playlist_link=playlist_link,
            playlist_owner=playlist_owner,
            image_url=mosaic_image_path
        )
        db.session.add(playlist_image)
        db.session.commit()

    # 直近5件の履歴を取得
    recent_images = PlaylistImage.query.order_by(PlaylistImage.created_at.desc()).limit(5).all()

    return render_template('index.html', recent_images=recent_images)
