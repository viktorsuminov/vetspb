from flask import Blueprint

wiki_bp = Blueprint('wiki', __name__)

from app.wiki import routes