from flask import Flask, jsonify

from .auth.routes import auth_bp
from .auth.service import RecruiterService
from .config import get_config
from .jobs.routes import jobs_bp
from .jobs.service import JobService


def create_app(config_overrides: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config())
    if config_overrides:
        app.config.update(config_overrides)

    app.extensions['recruiter_service'] = RecruiterService()
    app.extensions['job_service'] = JobService()

    app.register_blueprint(auth_bp)
    app.register_blueprint(jobs_bp)

    @app.get('/api/health')
    def health():
        return jsonify({'status': 'ok'})

    return app
