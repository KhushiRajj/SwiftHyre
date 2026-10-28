from flask import Flask, jsonify

from .config import get_config


def create_app(config_overrides: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config())
    if config_overrides:
        app.config.update(config_overrides)

    @app.get('/api/health')
    def health():
        return jsonify({'status': 'ok'})

    return app
