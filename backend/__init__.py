from flask import Flask
from .routes import init_routes

def create_app():
    app = Flask(__name__, static_folder="../frontend/static", template_folder="../frontend/templates")
    app.secret_key = 'ecocampus-1234'
    
    init_routes(app)

    return app