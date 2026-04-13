from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectMultipleField, SubmitField
from wtforms.validators import DataRequired, Length
from app.models import Section
class ArticleForm(FlaskForm):
    """Форма для создания/редактирования статьи"""
    
    title = StringField('Заголовок статьи', validators=[
        DataRequired(message='Введите заголовок статьи'),
        Length(min=5, max=200, message='Заголовок должен быть от 5 до 200 символов')
    ])
    
    content = TextAreaField('Содержание статьи', validators=[
    DataRequired(message='Введите содержание статьи')
    ])
    
    sections = SelectMultipleField('Разделы', coerce=int, validators=[
        DataRequired(message='Выберите хотя бы один раздел')
    ])
    
    submit = SubmitField('Сохранить статью')
    
    def __init__(self, *args, **kwargs):
        super(ArticleForm, self).__init__(*args, **kwargs)
        try:
            from flask_login import current_user
            if current_user.is_authenticated:
                editable_sections = current_user.get_editable_sections_list()
                # Сортируем по алфавиту для выпадающего списка
                editable_sections = sorted(editable_sections, key=lambda x: x.title)
                self.sections.choices = [(s.id, s.title) for s in editable_sections]
            else:
                self.sections.choices = []
        except:
            self.sections.choices = []