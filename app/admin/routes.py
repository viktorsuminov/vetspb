from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.admin import admin_bp
from app.admin.forms import UserForm, SectionForm, SectionPermissionsForm, UserPermissionsForm
from app.models import User, Section
from app.extensions import db
from wtforms.validators import Length

@admin_bp.route('/')
@login_required
def admin_index():
    """Главная страница админки"""
    if not current_user.is_admin():
        flash('Доступ запрещен', 'error')
        return redirect(url_for('main.index'))
    return render_template('admin/index.html')

@admin_bp.route('/users')
@login_required
def user_management():
    """Управление пользователями"""
    if not current_user.can_manage_users():
        flash('Доступ запрещен', 'error')
        return redirect(url_for('main.index'))
    
    users = current_user.get_manageable_users()
    return render_template('admin/user_management.html', users=users)

@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
def create_user():
    """Создание нового пользователя"""
    if not current_user.can_create_users():
        flash('Доступ запрещен', 'error')
        return redirect(url_for('main.index'))
    
    form = UserForm()
    
    if form.validate_on_submit():
        # Проверяем, нет ли пользователя с таким логином
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('Пользователь с таким логином уже существует', 'error')
            return render_template('admin/user_form.html', form=form, title='Создание пользователя')
        
        # Создаем нового пользователя
        user = User(
            username=form.username.data,
            email=form.email.data or None,
            role_id=form.role_id.data,
            is_active=form.is_active.data,
            created_by_id=current_user.id
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'Пользователь {user.username} успешно создан!', 'success')
        return redirect(url_for('admin.user_management'))
    
    return render_template('admin/user_form.html', form=form, title='Создание пользователя')

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    """Редактирование пользователя"""
    user = User.query.get_or_404(user_id)
    
    if not current_user.can_edit_user(user):
        flash('Доступ запрещен', 'error')
        return redirect(url_for('admin.user_management'))
    
    form = UserForm(obj=user)
    form.password.validators = [Length(min=6)]  # Пароль не обязателен при редактировании
    
    if form.validate_on_submit():
        # Проверяем логин на уникальность (кроме текущего пользователя)
        existing_user = User.query.filter(
            User.username == form.username.data,
            User.id != user.id
        ).first()
        if existing_user:
            flash('Пользователь с таким логином уже существует', 'error')
            return render_template('admin/user_form.html', form=form, title='Редактирование пользователя', user=user)
        
        # Обновляем данные
        user.username = form.username.data
        user.email = form.email.data or None
        user.role_id = form.role_id.data
        user.is_active = form.is_active.data
        
        # Обновляем пароль, если он указан
        if form.password.data:
            user.set_password(form.password.data)
        
        db.session.commit()
        
        flash(f'Данные пользователя {user.username} обновлены!', 'success')
        return redirect(url_for('admin.user_management'))
    
    return render_template('admin/user_form.html', form=form, title='Редактирование пользователя', user=user)

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    """Удаление пользователя"""
    user = User.query.get_or_404(user_id)
    
    if not current_user.can_edit_user(user):
        flash('Доступ запрещен', 'error')
        return redirect(url_for('admin.user_management'))
    
    # Нельзя удалить себя
    if user.id == current_user.id:
        flash('Нельзя удалить собственный аккаунт', 'error')
        return redirect(url_for('admin.user_management'))
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    flash(f'Пользователь {username} удален', 'success')
    return redirect(url_for('admin.user_management'))

@admin_bp.route('/sections')
@login_required
def section_management():
    """Управление разделами"""
    if not current_user.can_create_sections():
        flash('Доступ запрещен', 'error')
        return redirect(url_for('main.index'))
    
    sections = Section.query.order_by(Section.title.asc()).all()
    return render_template('admin/section_management.html', sections=sections)

@admin_bp.route('/sections/create', methods=['GET', 'POST'])
@login_required
def create_section():
    """Создание нового раздела"""
    if not current_user.can_create_sections():
        flash('Доступ запрещен', 'error')
        return redirect(url_for('main.index'))
    
    form = SectionForm()
    
    if form.validate_on_submit():
        section = Section(
            title=form.title.data,
            description=form.description.data,
            created_by=current_user.id
        )
        
        db.session.add(section)
        db.session.commit()
        
        flash(f'Раздел "{section.title}" успешно создан!', 'success')
        return redirect(url_for('admin.section_management'))
    
    return render_template('admin/section_form.html', form=form, title='Создание раздела')

@admin_bp.route('/sections/<int:section_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_section(section_id):
    """Редактирование раздела"""
    section = Section.query.get_or_404(section_id)
    
    if not current_user.can_edit_section(section):
        flash('Доступ запрещен', 'error')
        return redirect(url_for('admin.section_management'))
    
    form = SectionForm(obj=section)
    
    if form.validate_on_submit():
        section.title = form.title.data
        section.description = form.description.data
        section.order = form.order.data
        
        db.session.commit()
        
        flash(f'Раздел "{section.title}" обновлен!', 'success')
        return redirect(url_for('admin.section_management'))
    
    return render_template('admin/section_form.html', form=form, title='Редактирование раздела', section=section)

@admin_bp.route('/sections/<int:section_id>/permissions', methods=['GET', 'POST'])
@login_required
def section_permissions(section_id):
    """Управление правами доступа к разделу"""
    section = Section.query.get_or_404(section_id)
    
    if not current_user.can_edit_section(section):
        flash('Доступ запрещен', 'error')
        return redirect(url_for('admin.section_management'))
    
    form = SectionPermissionsForm()
    
    # Заполняем текущие значения при загрузке формы
    if request.method == 'GET':
        form.editors.data = [editor.id for editor in section.editors]
        form.readers.data = [reader.id for reader in section.readers]
    
    if form.validate_on_submit():
        # Обновляем редакторов
        section.editors = User.query.filter(User.id.in_(form.editors.data)).all()
        
        # Обновляем читателей
        section.readers = User.query.filter(User.id.in_(form.readers.data)).all()
        
        db.session.commit()
        
        flash(f'Права доступа к разделу "{section.title}" обновлены!', 'success')
        return redirect(url_for('admin.section_management'))
    
    return render_template('admin/section_permissions.html', form=form, section=section)

@admin_bp.route('/sections/<int:section_id>/delete', methods=['POST'])
@login_required
def delete_section(section_id):
    """Удаление раздела"""
    section = Section.query.get_or_404(section_id)
    
    if not current_user.can_edit_section(section):
        flash('Доступ запрещен', 'error')
        return redirect(url_for('admin.section_management'))
    
    title = section.title
    db.session.delete(section)
    db.session.commit()
    
    flash(f'Раздел "{title}" удален', 'success')
    return redirect(url_for('admin.section_management'))

@admin_bp.route('/users/<int:user_id>/permissions', methods=['GET', 'POST'])
@login_required
def user_permissions(user_id):
    """Управление правами доступа пользователя"""
    user = User.query.get_or_404(user_id)
    
    if not current_user.can_edit_user(user):
        flash('Доступ запрещен', 'error')
        return redirect(url_for('admin.user_management'))
    
    form = UserPermissionsForm()
    
    # Заполняем текущие значения при загрузке формы
    if request.method == 'GET':
        form.editable_sections.data = [section.id for section in user.editable_sections]
        form.readable_sections.data = [section.id for section in user.readable_sections]
    
    if form.validate_on_submit():
        try:
            # Обновляем разделы для редактирования
            user.editable_sections = Section.query.filter(Section.id.in_(form.editable_sections.data)).all()
            
            # Обновляем разделы для чтения
            user.readable_sections = Section.query.filter(Section.id.in_(form.readable_sections.data)).all()
            
            db.session.commit()
            
            flash(f'Права доступа для пользователя {user.username} обновлены!', 'success')
            return redirect(url_for('admin.user_management'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при обновлении прав: {str(e)}', 'error')
    
    return render_template('admin/user_permissions.html', 
                         form=form, 
                         user=user)