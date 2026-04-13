from flask import render_template, redirect, url_for
from app.main import main_bp
from flask_login import current_user

@main_bp.route('/')
def index():
    """Главная страница - перенаправляем в зависимости от авторизации"""
    if current_user.is_authenticated:
        return redirect(url_for('wiki.wiki_index'))  # Авторизованных - в базу знаний
    else:
        return redirect(url_for('auth.login'))  # Неавторизованных - на вход

@main_bp.route('/debug')
def debug_info():
    from app.models import User, Role
    users_count = User.query.count()
    roles_count = Role.query.count()
    users = User.query.all()
    
    debug_info = {
        'users_count': users_count,
        'roles_count': roles_count,
        'users': [{'id': u.id, 'username': u.username, 'role': u.role.name} for u in users],
    }
    
    return debug_info