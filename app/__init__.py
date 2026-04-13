from flask import Flask
from app.extensions import db, login_manager, migrate, csrf

def create_app(config_class='config.DevelopmentConfig'):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Инициализируем расширения
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    from app.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Регистрируем Blueprints
    from app.main import main_bp
    from app.auth import auth_bp
    from app.admin import admin_bp
    from app.wiki import wiki_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(wiki_bp, url_prefix='/wiki')
    
    # Импортируем модели
    from app import models
    
    with app.app_context():
        db.create_all()
        from app.models import create_initial_data
        create_initial_data()

    from app.wiki.routes import upload_file
    csrf.exempt(upload_file)
    
    return app