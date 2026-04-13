from flask import render_template, redirect, url_for, flash, request, abort, jsonify, current_app
from flask_login import login_required, current_user
from app.wiki import wiki_bp
from app.wiki.forms import ArticleForm
from app.models import Article, Section
from app.extensions import db
import os
from werkzeug.utils import secure_filename

# Исправленная функция allowed_file — без current_app в глобальной области
def allowed_file(filename):
    """Проверка разрешенных расширений файлов"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@wiki_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Загрузка изображений для редактора"""
    
    if 'file' not in request.files:
        return jsonify({'error': 'Файл не найден'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'Файл не выбран'}), 400

    if file and allowed_file(file.filename):
        # Путь: app/static/uploads/
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)

        filename = secure_filename(file.filename)
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename

        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)

        # Генерируем URL через static
        url = url_for('static', filename=f'uploads/{filename}', _external=True)
        return jsonify({'url': url})

    return jsonify({'error': 'Недопустимый тип файла'}), 400

# УДАЛЕНО: @wiki_bp.route('/uploads/<filename>') — не нужно!

@wiki_bp.route('/')
@login_required
def wiki_index():
    """Главная страница базы знаний"""
    readable_sections = current_user.get_readable_sections_list()
    readable_sections = sorted(readable_sections, key=lambda x: x.title)
    
    sections_with_articles = []
    for section in readable_sections:
        readable_articles = [article for article in section.articles if article.can_user_read(current_user)]
        readable_articles = sorted(readable_articles, key=lambda x: x.title)
        if readable_articles:
            sections_with_articles.append({
                'section': section,
                'articles': readable_articles
            })
    
    return render_template('wiki/index.html', 
                         sections_with_articles=sections_with_articles,
                         readable_sections=readable_sections)

@wiki_bp.route('/articles')
@login_required
def article_list():
    all_articles = Article.query.all()
    readable_articles = [article for article in all_articles if article.can_user_read(current_user)]
    return render_template('wiki/article_list.html', articles=readable_articles)

@wiki_bp.route('/articles/<int:article_id>')
@login_required
def view_article(article_id):
    article = Article.query.get_or_404(article_id)
    if not article.can_user_read(current_user):
        abort(403)
    return render_template('wiki/view_article.html', article=article)

@wiki_bp.route('/articles/create', methods=['GET', 'POST'])
@login_required
def create_article():
    editable_sections = current_user.get_editable_sections_list()
    if not editable_sections:
        flash('У вас нет прав для создания статей в каких-либо разделах', 'error')
        return redirect(url_for('wiki.wiki_index'))
    
    form = ArticleForm()
    
    if form.validate_on_submit():
        article = Article(
            title=form.title.data,
            content=form.content.data,
            author_id=current_user.id
        )
        selected_sections = Section.query.filter(Section.id.in_(form.sections.data)).all()
        article.sections = selected_sections
        db.session.add(article)
        db.session.commit()
        flash(f'Статья "{article.title}" успешно создана!', 'success')
        return redirect(url_for('wiki.view_article', article_id=article.id))
    
    return render_template('wiki/article_form.html', form=form, title='Создание статьи')

@wiki_bp.route('/articles/<int:article_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_article(article_id):
    article = Article.query.get_or_404(article_id)
    if not article.can_user_edit(current_user):
        abort(403)
    
    form = ArticleForm(obj=article)
    if request.method == 'GET':
        form.sections.data = [section.id for section in article.sections]
    
    if form.validate_on_submit():
        article.title = form.title.data
        article.content = form.content.data
        selected_sections = Section.query.filter(Section.id.in_(form.sections.data)).all()
        article.sections = selected_sections
        db.session.commit()
        flash(f'Статья "{article.title}" успешно обновлена!', 'success')
        return redirect(url_for('wiki.view_article', article_id=article.id))
    
    return render_template('wiki/article_form.html', form=form, title='Редактирование статьи', article=article)

@wiki_bp.route('/articles/<int:article_id>/delete', methods=['POST'])
@login_required
def delete_article(article_id):
    article = Article.query.get_or_404(article_id)
    if not article.can_user_edit(current_user):
        abort(403)
    
    title = article.title
    db.session.delete(article)
    db.session.commit()
    flash(f'Статья "{title}" удалена', 'success')
    return redirect(url_for('wiki.wiki_index'))

@wiki_bp.route('/search')
@login_required
def search():
    """Поиск по статьям"""
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 2:
        flash('Введите поисковый запрос (минимум 2 символа)', 'warning')
        return redirect(url_for('wiki.index'))
    
    # Простой поиск по заголовку и содержанию
    search_results = []
    all_articles = Article.query.all()
    
    for article in all_articles:
        # Проверяем права доступа
        if not article.can_user_read(current_user):
            continue
            
        # Ищем в заголовке и содержании
        query_lower = query.lower()
        title_match = query_lower in article.title.lower() if article.title else False
        content_match = query_lower in (article.content.lower() if article.content else '')
        
        if title_match or content_match:
            # Подсветка совпадений в превью
            preview = article.get_content_preview(200) if article.content else ""
            if content_match and article.content:
                # Простая подсветка (можно улучшить)
                preview = preview.lower().replace(query_lower, f'<mark>{query_lower}</mark>')
            
            search_results.append({
                'article': article,
                'title_match': title_match,
                'content_match': content_match,
                'preview': preview
            })
    
    # Сортируем: сначала совпадения в заголовке, потом в содержании
    search_results.sort(key=lambda x: (not x['title_match'], not x['content_match']))
    
    return render_template('wiki/search_results.html', 
                         query=query,
                         results=search_results,
                         results_count=len(search_results))