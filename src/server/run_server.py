"""
- 2025-08-07 - [추가] - v0.7.0: Flask 서버 기본 구조
- 기능: 사용자 등록, 인증 코드 발급, 인증 확인 API 엔드포인트 구현
- 2025-08-08 - [수정] - v1.0.0: 위치 공유 및 목록 제공 API 구현
- 2025-08-09 - [수정] - v1.5.0: 인증 시 길드 정보 조회 기능 추가
- 기능: /verify 엔드포인트에서 인증 성공 후, 알비온 API로 길드 정보를 조회하여 DB에 저장
- 2025-08-09 - [수정] - v1.5.1: 사용자 목록에 길드 정보 추가
- 기능: /get-locations 응답에 사용자의 길드 이름을 포함
- 2025-08-09 - [수정] - v1.5.4: 실제 알비온 API 연동
- 기능: get_player_info_from_api 함수가 실제 외부 API를 호출하도록 수정
- 2025-08-09 - [수정] - v1.5.5: 서버 선택 기반 API 호출
- 기능: 클라이언트가 선택한 서버에 맞는 API 주소로 길드 정보를 요청
- 2025-08-09 - [수정] - v1.5.6: 서버 정보 저장/조회 로직 구현
- 기능: /register에서 서버 정보를 저장하고, /verify에서 DB의 서버 정보를 사용
- 2025-08-09 - [수정] - v1.6.0: 지역 간 거리 계산 기능 연동
- 기능: /get-locations 요청 시, 요청자와 다른 유저 간의 거리를 계산하여 함께 반환
- 2025-08-09 - [수정] - v1.6.2: 가상 사용자 추가, 버그 수정, 성능 최적화
- 기능: 서버 시작 시 가상 사용자 생성, 본인 거리 0으로 수정, DB 조회 최적화
- 2025-08-09 - [수정] - v1.6.4: 가상 사용자 위치를 블랙존으로 변경
- 기능: 테스트를 위해 가상 사용자들이 블랙존에 위치하도록 수정

"""
import random  # random 임포트 추가
from datetime import datetime, timedelta

import requests
from flask import Flask, request, jsonify

from src.server.database import db, User
from src.config.settings import API_SERVERS
from src.core.map_logic import get_distance


# ... (create_app, app, locations은 이전과 동일) ...
def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///beacon.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app


app = create_app()
locations = {}


# --- v1.6.4 수정: 가상 사용자 위치 변경 ---
def initialize_dummy_users():
    """서버 시작 시 테스트용 가상 사용자를 생성합니다."""
    with app.app_context():
        db.create_all()

        dummy_users = {
            "BraveWarrior": {"server": "West (Americas)", "guild_name": "Warriors of Light", "zone": "Sandrift Steppe"},
            "ShadowClaw": {"server": "East (Asia)", "guild_name": "Silent Assassins", "zone": "Sandrift Coast"}
        }

        for username, info in dummy_users.items():
            user = User.query.filter_by(username=username).first()
            if not user:
                new_user = User(
                    username=username, server=info["server"],
                    guild_name=info["guild_name"], is_verified=True
                )
                db.session.add(new_user)
                print(f"가상 사용자 '{username}' 생성.")

            locations[username] = {
                'zone': info["zone"],
                'group_size': random.randint(5, 50),
                'timestamp': datetime.utcnow()
            }

        db.session.commit()
        print("가상 사용자 초기화 완료.")


# ... (나머지 모든 함수는 이전과 동일합니다) ...
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username, server = data.get('username'), data.get('server')
    if not username or not server: return jsonify({'error': '사용자 이름과 서버 정보가 필요합니다.'}), 400
    user = User.query.filter_by(username=username).first()
    if user:
        user.server = server
        db.session.commit()
        return jsonify({'message': f'기존 사용자 {username}의 서버 정보가 업데이트되었습니다.'}), 200
    else:
        new_user = User(username=username, server=server)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': f'{username} 사용자가 성공적으로 등록되었습니다.'}), 201


def get_player_info_from_api(username, server):
    print(f"[{server} 서버 API] '{username}'의 정보 요청 중...")
    base_url = API_SERVERS.get(server)
    if not base_url: return None
    url = f"{base_url}/search?q={username}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            for player in data.get('players', []):
                if player.get('Name').lower() == username.lower(): return player
            return None
        return None
    except requests.exceptions.RequestException:
        return None


@app.route('/verify', methods=['POST'])
def verify_user():
    data = request.get_json()
    username = data.get('username')
    user = User.query.filter_by(username=username).first()
    if not user: return jsonify({'error': '등록되지 않은 사용자입니다.'}), 404
    if not user.server: return jsonify({'error': '서버 정보가 등록되지 않았습니다.'}), 400
    user.is_verified = True
    player_data = get_player_info_from_api(username, user.server)
    if player_data and player_data.get('GuildName'):
        user.guild_name = player_data['GuildName']
        user.guild_id = player_data['GuildId']
    db.session.commit()
    return jsonify({'message': '서버에 인증 상태가 성공적으로 기록되었습니다.'}), 200


@app.route('/update-location', methods=['POST'])
def update_location():
    data = request.get_json()
    username = data.get('username')
    user = User.query.filter_by(username=username, is_verified=True).first()
    if not user: return jsonify({'error': '인증되지 않은 사용자입니다.'}), 403
    locations[username] = {'zone': data.get('zone'), 'group_size': data.get('group_size'),
                           'timestamp': datetime.utcnow()}
    return jsonify({'message': '위치가 업데이트되었습니다.'}), 200


@app.route('/get-locations', methods=['POST'])
def get_locations():
    requesting_user_data = request.get_json()
    requesting_user_name = requesting_user_data.get('username')

    if not requesting_user_name or requesting_user_name not in locations:
        return jsonify([]), 200

    requesting_user_zone = locations[requesting_user_name]['zone']
    active_users_response = []
    five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)

    active_usernames = [uname for uname, data in locations.items() if data['timestamp'] > five_minutes_ago]
    users_from_db = User.query.filter(User.username.in_(active_usernames)).all()
    user_db_dict = {user.username: user for user in users_from_db}

    for username in active_usernames:
        user_location_data = locations[username]
        user_db_info = user_db_dict.get(username)

        if username == requesting_user_name:
            distance = 0
        else:
            distance = get_distance(requesting_user_zone, user_location_data['zone'])

        active_users_response.append({
            'username': username,
            'guild_name': user_db_info.guild_name if user_db_info else "",
            'zone': user_location_data['zone'],
            'group_size': user_location_data['group_size'],
            'distance': distance,
            'last_updated': user_location_data['timestamp'].strftime('%H:%M:%S')
        })

    all_known_users = list(locations.keys())
    for username in all_known_users:
        if locations[username]['timestamp'] <= five_minutes_ago:
            del locations[username]

    return jsonify(active_users_response), 200


if __name__ == '__main__':
    initialize_dummy_users()
    app.run(host='0.0.0.0', port=5000, debug=True)