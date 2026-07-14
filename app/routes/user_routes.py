from flask import Blueprint, request, session
from app.models import db, User
from app.utils.response import success_response, error_response
from app.utils.auth import login_required, require_role
from werkzeug.security import generate_password_hash

from flask import request
from app.routes import user_bp

@user_bp.route('/users', methods=['GET'])
@login_required
def get_users():
    if session.get('role') not in ['superadmin', 'admin']:
        return error_response('Forbidden. Insufficient permissions.', status_code=403)
    users = User.query.all()
    return success_response([u.to_dict() for u in users])

@user_bp.route('/users', methods=['POST'])
@login_required
@require_role('superadmin')
def create_user():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'admin')
    name = data.get('name')
    email = data.get('email')

    if not username or not password:
        return error_response('Username and password are required', 400)
        
    if User.query.filter_by(username=username).first():
        return error_response('Username already exists', 400)
        
    new_user = User(
        username=username,
        password_hash=generate_password_hash(password),
        password_plain=password,
        role=role,
        name=name,
        email=email
    )
    db.session.add(new_user)
    db.session.commit()
    
    return success_response({'message': 'User created successfully', 'user': new_user.to_dict()}, 201)

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
@require_role('superadmin')
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return error_response('User not found', 404)
        
    if user.role == 'superadmin' and User.query.filter_by(role='superadmin').count() == 1:
        return error_response('Cannot delete the last superadmin', 400)
        
    db.session.delete(user)
    db.session.commit()
    return success_response({'message': 'User deleted'})

@user_bp.route('/users/<int:user_id>/reset_password', methods=['POST'])
@login_required
@require_role('superadmin')
def reset_password(user_id):
    data = request.json
    new_password = data.get('password')
    
    if not new_password:
        return error_response('New password is required', 400)
        
    user = User.query.get(user_id)
    if not user:
        return error_response('User not found', 404)
        
    user.password_hash = generate_password_hash(new_password)
    user.password_plain = new_password
    db.session.commit()
    
    return success_response({'message': 'Password reset successfully'})
