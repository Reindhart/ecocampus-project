from flask import Flask
from .routes import init_routes
from .models import db
import os

def create_app():
    app = Flask(__name__, static_folder="../frontend/static", template_folder="../frontend/templates")
    app.secret_key = 'ecocampus-1234'

    # Configuración de SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join('..', 'frontend', 'static', 'img', 'reportes')
    app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

    db.init_app(app)

    with app.app_context():
        db.create_all()

    init_routes(app)
    return app
