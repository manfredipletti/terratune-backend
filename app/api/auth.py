from flask import request, jsonify
from app.models import User
from app import db
from app.api import bp

from flask_jwt_extended import create_access_token


@bp.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json() or {}

    if 'username' not in data or 'password' not in data:
        return jsonify({'error': 'must include username and password fields'}), 400
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'username already exists'}), 400

    user = User()
    user.username = data['username']
    user.set_password(data['password'])

    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'User created successfully'}), 201


@bp.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}

    if 'username' not in data or 'password' not in data:
        return jsonify({'error': 'must include username and password fields'}), 400

    user = User.query.filter_by(username=data['username']).first()

    if user is None or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid username or password'}), 401  # Unauthorized

    access_token = create_access_token(identity=user.id)

    return jsonify(access_token=access_token)