from flask_login import LoginManager

login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User
    return User.get_by_id(user_id)