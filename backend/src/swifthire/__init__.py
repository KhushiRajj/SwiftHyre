from flask import Flask, jsonify

from .applications.recruiter_routes import recruiter_applications_bp
from .applications.routes import applications_bp
from .applications.service import ApplicationService
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
    app.extensions['application_service'] = ApplicationService()

    app.register_blueprint(auth_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(applications_bp)
    app.register_blueprint(recruiter_applications_bp)

    @app.get('/api/health')
    def health():
        return jsonify({'status': 'ok'})

    return app
