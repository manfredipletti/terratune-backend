from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from .config import Config
from flask_cors import CORS

# Inizializza le estensioni, ma senza un'app specifica
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
jwt = JWTManager()

def create_app(config_class=Config):
    # Crea e configura l'istanza dell'app
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Lega le estensioni all'istanza dell'app
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # Importa i modelli per farli riconoscere da Flask-Migrate
    from app import models
    from app.api import bp as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')


    return app