from flask import Flask, jsonify

from .applications.recruiter_routes import recruiter_applications_bp
from .applications.routes import applications_bp
from .applications.service import ApplicationService
from .assessments.routes import assessments_bp
from .auth.routes import auth_bp
from .auth.service import RecruiterService
from .coding.routes import coding_bp
from .coding.runner import CodeRunner
from .coding.service import CodingChallengeService
from .config import get_config
from .jobs.routes import jobs_bp
from .jobs.service import JobService
from .reporting.routes import reporting_bp
from .workflow.routes import workflow_bp


def create_app(config_overrides: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config())
    if config_overrides:
        app.config.update(config_overrides)

    app.extensions['recruiter_service'] = RecruiterService()
    app.extensions['job_service'] = JobService()
    app.extensions['application_service'] = ApplicationService()
    app.extensions['coding_service'] = CodingChallengeService(
        runner=CodeRunner(api_key=app.config.get('ONLINECOMPILER_API_KEY')),
    )

    app.register_blueprint(auth_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(applications_bp)
    app.register_blueprint(recruiter_applications_bp)
    app.register_blueprint(workflow_bp)
    app.register_blueprint(assessments_bp)
    app.register_blueprint(reporting_bp)
    app.register_blueprint(coding_bp)

    @app.get('/api/health')
    def health():
        return jsonify({'status': 'ok'})

    return app
