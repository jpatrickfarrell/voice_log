from flask import Flask
from app.extensions import login_manager
from app.services.database import init_database
import os

def create_app(config_object=None):
    # Get the project root directory (where the app folder is located)
    app_dir = os.path.dirname(os.path.abspath(__file__))  # app/ directory
    project_root = os.path.dirname(app_dir)  # project root (parent of app/)
    
    template_dir = os.path.join(project_root, 'templates')
    static_dir = os.path.join(project_root, 'static')
    
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SIGNUP_CODE'] = os.environ.get('SIGNUP_CODE', 'VOICE2024')
    
    # Check if UPLOAD_FOLDER environment variable is set
    env_upload_folder = os.environ.get('UPLOAD_FOLDER')
    if env_upload_folder:
        print(f"UPLOAD_FOLDER environment variable found: {env_upload_folder}")
        app.config['UPLOAD_FOLDER'] = env_upload_folder
    else:
        app.config['UPLOAD_FOLDER'] = os.path.join(project_root, 'uploads')
    
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
    
    # Check if DATABASE_PATH environment variable is set
    env_database_path = os.environ.get('DATABASE_PATH')
    if env_database_path:
        print(f"DATABASE_PATH environment variable found: {env_database_path}")
        app.config['DATABASE_PATH'] = env_database_path
    else:
        app.config['DATABASE_PATH'] = os.path.join(project_root, 'data', 'voice_log.db')
    
    # Debug: Log the paths being used
    print(f"Project root: {project_root}")
    print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"Database path: {app.config['DATABASE_PATH']}")
    print(f"Environment UPLOAD_FOLDER: {env_upload_folder}")
    print(f"Environment DATABASE_PATH: {env_database_path}")
    
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('data', exist_ok=True)
    
    # Initialize extensions
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    # Initialize database
    init_database(app.config['DATABASE_PATH'])
    
    # Register blueprints
    from app.blueprints.main import main_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.posts import posts_bp
    from app.blueprints.api import api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(posts_bp, url_prefix='/posts')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app