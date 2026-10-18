from app import create_app
from app.config import Config

app = create_app()

if __name__ == '__main__':
    print(f"🚀 Asystent Konsultanta SAP startuje na http://{Config.HOST}:{Config.PORT}")
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG, use_reloader=False)
