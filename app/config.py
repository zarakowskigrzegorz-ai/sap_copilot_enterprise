import os

class Config:
    HOST = os.environ.get('HOST', '127.0.0.1')
    PORT = int(os.environ.get('PORT', 5001))
    DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 'yes')
    OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'sap_copilot_pro')
    
    # Baza danych DuckDB (domyślnie trwały plik 'data/sap_copilot.duckdb'; dla testów można ustawić ':memory:')
    DB_PATH = os.environ.get('DB_PATH', 'data/sap_copilot.duckdb')
    
    # Parametry i progi biznesowe SAP
    APPROVAL_THRESHOLD_PLN = float(os.environ.get('APPROVAL_THRESHOLD_PLN', 10000.0))
    DEFAULT_PLANT = os.environ.get('DEFAULT_PLANT', 'JAN1')
    DEFAULT_PRICE_PLN = float(os.environ.get('DEFAULT_PRICE_PLN', 50.0))
