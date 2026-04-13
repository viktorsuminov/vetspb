#!/usr/bin/env python3
from app import create_app
from app.extensions import db

app = create_app()

with app.app_context():
    print("🔧 Принудительно создаем начальные данные...")
    
    from app.models import Role, User
    
    # Создаем роли
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
            print(f"✅ Создана роль: {role_data['name']}")
    
    db.session.commit()
    
    # Создаем администратора, если его нет
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
        print("✅ Создан пользователь по умолчанию: admin / admin123")
    else:
        print("ℹ️  Пользователи уже существуют")
    
    # Проверяем результат
    users_count = User.query.count()
    roles_count = Role.query.count()
    print(f"\n📊 Итог: {users_count} пользователей, {roles_count} ролей")