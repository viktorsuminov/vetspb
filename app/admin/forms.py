from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, SelectField, BooleanField, 
                    SubmitField, TextAreaField, SelectMultipleField)
from wtforms.validators import DataRequired, Length, Email, Optional
from app.models import Role, User, Section

class UserForm(FlaskForm):
    """Форма для создания/редактирования пользователя"""
    
    username = StringField('Логин', validators=[
        DataRequired(message='Введите логин'),
        Length(min=3, max=64, message='Логин должен быть от 3 до 64 символов')
    ])
    
    email = StringField('Email', validators=[
        Optional(),
        Email(message='Введите корректный email')
    ])
    
    password = PasswordField('Пароль', validators=[
        DataRequired(message='Введите пароль'),
        Length(min=6, message='Пароль должен быть не менее 6 символов')
    ])
    
    role_id = SelectField('Роль', coerce=int, validators=[
        DataRequired(message='Выберите роль')
    ])
    
    is_active = BooleanField('Активный', default=True)
    
    submit = SubmitField('Сохранить')
    
    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        # Динамически заполняем выбор ролей
        self.role_id.choices = [(role.id, role.name) for role in Role.query.order_by(Role.level.desc()).all()]


class SectionForm(FlaskForm):
    """Форма для создания/редактирования раздела"""
    
    title = StringField('Название раздела', validators=[
        DataRequired(message='Введите название раздела'),
        Length(min=2, max=100, message='Название должно быть от 2 до 100 символов')
    ])
    
    description = TextAreaField('Описание раздела', validators=[
        Length(max=500, message='Описание не должно превышать 500 символов')
    ])
    
    submit = SubmitField('Сохранить')

class SectionPermissionsForm(FlaskForm):
    """Форма для управления правами доступа к разделу"""
    
    editors = SelectMultipleField('Редакторы раздела', coerce=int)
    readers = SelectMultipleField('Читатели раздела', coerce=int)
    submit = SubmitField('Сохранить права доступа')
    
    def __init__(self, *args, **kwargs):
        super(SectionPermissionsForm, self).__init__(*args, **kwargs)
        # Заполняем выбор пользователями (кроме руководителей - они и так имеют доступ)
        users = User.query.filter(User.role.has(Role.name.in_(['Старший оператор', 'Оператор', 'Стажер']))).all()
        # Сортируем пользователей по имени
        users = sorted(users, key=lambda x: x.username)
        self.editors.choices = [(u.id, u.username) for u in users]
        self.readers.choices = [(u.id, u.username) for u in users]

class UserPermissionsForm(FlaskForm):
    """Форма для управления правами доступа пользователя"""
    
    editable_sections = SelectMultipleField('Разделы для редактирования', coerce=int)
    readable_sections = SelectMultipleField('Разделы для чтения', coerce=int)
    submit = SubmitField('Сохранить права доступа')
    
    def __init__(self, *args, **kwargs):
        super(UserPermissionsForm, self).__init__(*args, **kwargs)
        # Все разделы для выбора
        all_sections = Section.query.order_by(Section.title.asc()).all()
        self.editable_sections.choices = [(s.id, s.title) for s in all_sections]
        self.readable_sections.choices = [(s.id, s.title) for s in all_sections]