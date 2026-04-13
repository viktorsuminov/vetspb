from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length

class LoginForm(FlaskForm):
    """Форма входа в систему"""
    username = StringField('Логин', validators=[
        DataRequired(message='Введите логин'),
        Length(min=3, max=64, message='Логин должен быть от 3 до 64 символов')
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(message='Введите пароль')
    ])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')