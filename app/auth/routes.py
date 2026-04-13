from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app.auth import auth_bp
from app.auth.forms import LoginForm
from app.models import User

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа в систему"""
    
    if current_user.is_authenticated:
        return redirect(url_for('wiki.wiki_index'))  # ⬅️ Меняем на wiki_index
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data) and user.is_active:
            login_user(user, remember=form.remember_me.data)
            
            next_page = request.args.get('next')
            # Проверяем, что next_page безопасный (начинается с /)
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            
            flash(f'Добро пожаловать, {user.username}!', 'success')
            return redirect(url_for('wiki.wiki_index'))  # ⬅️ Всегда на базу знаний после входа
            
        else:
            flash('Неверный логин или пароль', 'error')
    
    return render_template('auth/login.html', title='Вход в систему', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """Выход из системы"""
    logout_user()
    flash('Вы успешно вышли из системы', 'info')
    return redirect(url_for('main.index'))