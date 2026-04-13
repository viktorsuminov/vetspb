from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length

class SearchForm(FlaskForm):
    query = StringField('Поиск', validators=[
        DataRequired(message='Введите поисковый запрос'),
        Length(min=2, max=100, message='Запрос должен быть от 2 до 100 символов')
    ])
    submit = SubmitField('Найти')