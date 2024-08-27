from app import db
from datetime import datetime

class PlaylistImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    playlist_name = db.Column(db.String(255), nullable=False)
    playlist_link = db.Column(db.String(255), nullable=False)
    playlist_owner = db.Column(db.String(255), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
