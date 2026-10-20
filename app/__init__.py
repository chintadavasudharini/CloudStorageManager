from flask import Flask, session
from app.config import Config
from app.s3_service import S3Service
from app.models import init_db, get_user_by_id

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize SQLite database
    with app.app_context():
        init_db()

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.api import api_bp
    from app.routes.auth import auth_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/auth")

    @app.context_processor
    def inject_global_data():
        is_demo = session.get("demo_mode", app.config.get("ENABLE_DEMO_MODE", True))
        current_region = session.get("aws_region", app.config.get("AWS_DEFAULT_REGION", "us-east-1"))
        has_custom_creds = bool(session.get("aws_access_key") or app.config.get("AWS_ACCESS_KEY_ID"))
        
        current_user = None
        user_id = session.get("user_id")
        if user_id:
            current_user = get_user_by_id(user_id)

        return {
            "current_user": current_user,
            "is_demo_mode": is_demo,
            "current_region": current_region,
            "has_custom_creds": has_custom_creds
        }

    return app

def get_s3_service_for_session():
    """Returns an initialized S3Service instance based on session or environment configuration."""
    from flask import current_app
    
    # Check if user explicitly toggled demo mode
    if session.get("demo_mode") is True:
        return S3Service(is_demo=True, region=session.get("aws_region", "us-east-1"))
    
    # Check session credentials
    session_key = session.get("aws_access_key")
    session_secret = session.get("aws_secret_key")
    session_region = session.get("aws_region")
    
    if session_key and session_secret:
        return S3Service(
            access_key=session_key,
            secret_key=session_secret,
            region=session_region or current_app.config.get("AWS_DEFAULT_REGION", "us-east-1"),
            is_demo=False
        )

    # Check env / app config credentials
    app_key = current_app.config.get("AWS_ACCESS_KEY_ID")
    app_secret = current_app.config.get("AWS_SECRET_ACCESS_KEY")
    app_region = current_app.config.get("AWS_DEFAULT_REGION", "us-east-1")
    
    if app_key and app_secret:
        return S3Service(
            access_key=app_key,
            secret_key=app_secret,
            region=app_region,
            is_demo=False
        )

    # Fallback to demo mode if enabled
    if current_app.config.get("ENABLE_DEMO_MODE", True):
        return S3Service(is_demo=True, region=app_region)

    # Otherwise default boto3 chain
    return S3Service(region=app_region, is_demo=False)
