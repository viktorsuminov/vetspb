from app.extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Таблица для связи многие-ко-многим: Раздел <-> Статья
article_sections = db.Table('article_sections',
    db.Column('article_id', db.Integer, db.ForeignKey('article.id'), primary_key=True),
    db.Column('section_id', db.Integer, db.ForeignKey('section.id'), primary_key=True)
)

# Таблица для связи: какие пользователи могут редактировать какие разделы
section_editors = db.Table('section_editors',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('section_id', db.Integer, db.ForeignKey('section.id'), primary_key=True)
)

# Таблица для связи: какие пользователи могут читать какие разделы
section_readers = db.Table('section_readers',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('section_id', db.Integer, db.ForeignKey('section.id'), primary_key=True)
)

class Role(db.Model):
    """Модель ролей пользователей"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.String(200))
    level = db.Column(db.Integer, default=0)  # Уровень привилегий (для сортировки)
    users = db.relationship('User', backref='role', lazy=True)
    
    @classmethod
    def get_admin_role(cls):
        return cls.query.filter_by(name='Руководитель').first()
    
    @classmethod
    def get_supervisor_role(cls):
        return cls.query.filter_by(name='Супервизор').first()
    
    @classmethod
    def get_senior_operator_role(cls):
        return cls.query.filter_by(name='Старший оператор').first()
    
    def __repr__(self):
        return f'<Role {self.name}>'

class User(UserMixin, db.Model):
    """Модель пользователя"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Кто создал пользователя
    
    # Связи
    editable_sections = db.relationship('Section', secondary=section_editors, backref='editors')
    readable_sections = db.relationship('Section', secondary=section_readers, backref='readers')
    
    # Связь для созданных пользователей
    created_users = db.relationship('User', backref=db.backref('created_by', remote_side=[id]))
    
    def set_password(self, password):
        """Установка хэшированного пароля"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Проверка пароля"""
        return check_password_hash(self.password_hash, password)
    
    # === МЕТОДЫ ПРОВЕРКИ ПРАВ ===
    
    def is_admin(self):
        """Является ли пользователь руководителем?"""
        return self.role.name == 'Руководитель'
    
    def is_supervisor(self):
        """Является ли пользователь супервизором?"""
        return self.role.name == 'Супервизор'
    
    def can_manage_users(self):
        """Может ли управлять пользователями?"""
        return self.is_admin()
    
    def can_create_users(self):
        """Может ли создавать новых пользователей?"""
        return self.is_admin()
    
    def can_edit_user(self, target_user):
        """Может ли редактировать другого пользователя?"""
        if self.is_admin() and target_user.id != self.id:
            return True
        return False
    
    def can_change_role(self, target_user, new_role):
        """Может ли изменить роль пользователя?"""
        if not self.is_admin():
            return False
        
        if target_user.id == self.id:
            return False
        
        if new_role.name == 'Руководитель':
            return True
            
        return True
    
    def can_edit_section(self, section):
        """Может ли пользователь редактировать раздел?"""
        if self.role.name in ['Руководитель', 'Супервизор']:
            return True
        return section in self.editable_sections
    
    def can_read_section(self, section):
        """Может ли пользователь читать раздел?"""
        if self.role.name in ['Руководитель', 'Супервизор', 'Старший оператор']:
            return True
        return section in self.readable_sections
    
    def get_manageable_users(self):
        """Получить список пользователей, которыми можно управлять"""
        if self.is_admin():
            return User.query.filter(User.id != self.id).all()
        else:
            return []

    def can_create_sections(self):
        """Может ли создавать разделы?"""
        return self.role.name in ['Руководитель', 'Супервизор']
    
    def get_editable_sections_list(self):
        """Получить список разделов, которые пользователь может редактировать (по алфавиту)"""
        if self.role.name in ['Руководитель', 'Супервизор']:
            return Section.query.order_by(Section.title.asc()).all()
        return sorted(self.editable_sections, key=lambda x: x.title)
    
    def get_readable_sections_list(self):
        """Получить список разделов, которые пользователь может читать (по алфавиту)"""
        if self.role.name in ['Руководитель', 'Супервизор', 'Старший оператор']:
            return Section.query.order_by(Section.title.asc()).all()
        return sorted(self.readable_sections, key=lambda x: x.title)
    
    # === МЕТОДЫ ДЛЯ ПЕРЕДАЧИ ПРАВ РУКОВОДИТЕЛЯ ===
    
    def can_transfer_admin(self, target_user):
        """Может ли передать роль руководителя другому пользователю?"""
        if not self.is_admin():
            return False
        
        if target_user.id == self.id:
            return False
        
        if not target_user.is_active:
            return False
            
        if target_user.role.name not in ['Супервизор', 'Старший оператор']:
            return False
            
        return True
    
    def transfer_admin_role(self, target_user, confirmation_password):
        """Безопасная передача роли руководителя"""
        from flask import current_app
        
        if not self.can_transfer_admin(target_user):
            raise PermissionError("Недостаточно прав для передачи роли руководителя")
        
        if not self.check_password(confirmation_password):
            raise ValueError("Неверный пароль для подтверждения операции")
        
        admin_role = Role.query.filter_by(name='Руководитель').first()
        old_role = target_user.role
        
        try:
            target_user.role = admin_role
            
            supervisor_role = Role.query.filter_by(name='Супервизор').first()
            self.role = supervisor_role
            
            self._log_admin_transfer(target_user, old_role)
            
            db.session.commit()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def _log_admin_transfer(self, new_admin, old_role):
        """Логирование передачи прав"""
        print(f"ПЕРЕДАЧА ПРАВ: {self.username} -> {new_admin.username}")
        print(f"Бывшая роль нового руководителя: {old_role.name}")
        print(f"Время: {datetime.utcnow()}")
    
    def get_admin_transfer_candidates(self):
        """Получить список пользователей, которым можно передать права руководителя"""
        if not self.is_admin():
            return []
        
        candidates = User.query.filter(
            User.is_active == True,
            User.id != self.id,
            User.role_id.in_(
                db.select(Role.id).filter(Role.name.in_(['Супервизор', 'Старший оператор']))
            )
        ).all()
        
        return candidates
    
    def __repr__(self):
        return f'<User {self.username}>'

class Section(db.Model):
    """Модель раздела базы знаний"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    articles = db.relationship('Article', secondary=article_sections, backref='sections', 
                              order_by='Article.title')
    
    def __repr__(self):
        return f'<Section {self.title}>'

    def can_user_edit(self, user):
        """Может ли пользователь редактировать этот раздел?"""
        return user.can_edit_section(self)
    
    def can_user_read(self, user):
        """Может ли пользователь читать этот раздел?"""
        return user.can_read_section(self)
    
    def get_editors(self):
        """Получить список редакторов раздела"""
        return self.editors
    
    def get_readers(self):
        """Получить список читателей раздела"""
        return self.readers
    
    def add_editor(self, user):
        """Добавить редактора раздела"""
        if user not in self.editors:
            self.editors.append(user)
    
    def remove_editor(self, user):
        """Удалить редактора раздела"""
        if user in self.editors:
            self.editors.remove(user)
    
    def add_reader(self, user):
        """Добавить читателя раздела"""
        if user not in self.readers:
            self.readers.append(user)
    
    def remove_reader(self, user):
        """Удалить читателя раздела"""
        if user in self.readers:
            self.readers.remove(user)

class Article(db.Model):
    """Модель статьи"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    def __repr__(self):
        return f'<Article {self.title}>'

    def can_user_edit(self, user):
        """Может ли пользователь редактировать статью?"""
        # Проверяем, есть ли у пользователя права на редактирование ХОТЯ БЫ одного раздела статьи
        return any(user.can_edit_section(section) for section in self.sections)
    
    def can_user_read(self, user):
        """Может ли пользователь читать статью?"""
        # Проверяем, есть ли у пользователя права на чтение ВСЕХ разделов статьи
        return all(user.can_read_section(section) for section in self.sections)
    
    def add_to_section(self, section):
        """Добавить статью в раздел"""
        if section not in self.sections:
            self.sections.append(section)
    
    def remove_from_section(self, section):
        """Удалить статью из раздела"""
        if section in self.sections:
            self.sections.remove(section)
    
    def get_content_preview(self, length=200):
        """Получить превью содержания"""
        if self.content:
            return self.content[:length] + '...' if len(self.content) > length else self.content
        return "Нет содержания"
    @classmethod
    def search(cls, query, user):
        """Поиск статей с учетом прав доступа"""
        results = []
        all_articles = cls.query.all()
        
        for article in all_articles:
            if not article.can_user_read(user):
                continue
                
            if (query.lower() in (article.title.lower() if article.title else '') or
                query.lower() in (article.content.lower() if article.content else '')):
                results.append(article)
        
        return results

def create_initial_data():
    """Создание начальных данных (роли, первого пользователя)"""
    
    roles_data = [
        {'name': 'Руководитель', 'description': 'Полный доступ ко всему', 'level': 100},
        {'name': 'Супервизор', 'description': 'Управление разделами и статьями', 'level': 80},
        {'name': 'Старший оператор', 'description': 'Редактирование статей', 'level': 60},
        {'name': 'Оператор', 'description': 'Чтение разрешенных разделов', 'level': 40},
        {'name': 'Стажер', 'description': 'Ограниченный доступ', 'level': 20}
    ]
    
    for role_data in roles_data:
        role = Role.query.filter_by(name=role_data['name']).first()
        if not role:
            role = Role(**role_data)
            db.session.add(role)
    
    db.session.commit()
    
    if User.query.count() == 0:
        admin_role = Role.query.filter_by(name='Руководитель').first()
        admin_user = User(
            username='admin',
            email='admin@vetclinic.ru',
            role=admin_role
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        db.session.commit()
        print("Создан пользователь по умолчанию: admin / admin123")