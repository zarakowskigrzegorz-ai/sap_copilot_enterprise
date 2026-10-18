from flask import Flask
from app.database.db_manager import init_db

def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    # Inicjalizacja bazy danych w pamięci (DuckDB)
    init_db()

    # Rejestracja Blueprinta API i widoków
    from app.routes.api_routes import api_bp
    app.register_blueprint(api_bp)

    return app
