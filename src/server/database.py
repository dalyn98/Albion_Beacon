"""
- 2025-08-07 - [추가] - v0.7.0: 데이터베이스 모델 정의
- 기능: Flask-SQLAlchemy를 사용하여 User 모델(테이블) 생성
- 2025-08-09 - [수정] - v1.5.0: 길드 정보 필드 추가
- 기능: User 모델에 guild_name, guild_id 컬럼 추가
- 2025-08-09 - [수정] - v1.5.6: 서버 정보 필드 추가
- 기능: User 모델에 server 컬럼 추가

"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    guild_name = db.Column(db.String(100), nullable=True)
    guild_id = db.Column(db.String(100), nullable=True)
    # --- v1.5.6 추가 ---
    server = db.Column(db.String(20), nullable=True) # 예: 'East (Asia)'

    def __repr__(self):
        return f'<User {self.username}>'