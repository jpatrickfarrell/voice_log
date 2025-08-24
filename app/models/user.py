from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.services.database import get_db
from flask import current_app

class User(UserMixin):
    def __init__(self, id, username, email, password_hash, is_admin=False, is_active=True, created_at=None, updated_at=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.is_admin = is_admin
        self.is_active = is_active
        self.created_at = created_at
        self.updated_at = updated_at

    @classmethod
    def get_by_id(cls, user_id):
        """Get user by ID"""
        with get_db(current_app.config['DATABASE_PATH']) as conn:
            row = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
            if row:
                return cls(**dict(row))
        return None

    @classmethod
    def get_by_username(cls, username):
        """Get user by username"""
        with get_db(current_app.config['DATABASE_PATH']) as conn:
            row = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            if row:
                return cls(**dict(row))
        return None

    @classmethod
    def get_by_email(cls, email):
        """Get user by email"""
        with get_db(current_app.config['DATABASE_PATH']) as conn:
            row = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
            if row:
                return cls(**dict(row))
        return None

    @classmethod
    def create(cls, username, email, password, is_admin=False):
        """Create a new user"""
        password_hash = generate_password_hash(password)
        
        with get_db(current_app.config['DATABASE_PATH']) as conn:
            cursor = conn.execute(
                'INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)',
                (username, email, password_hash, is_admin)
            )
            user_id = cursor.lastrowid
            return cls.get_by_id(user_id)

    def check_password(self, password):
        """Check if provided password matches"""
        return check_password_hash(self.password_hash, password)

    def update_password(self, new_password):
        """Update user password"""
        password_hash = generate_password_hash(new_password)
        with get_db(current_app.config['DATABASE_PATH']) as conn:
            conn.execute(
                'UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                (password_hash, self.id)
            )
            self.password_hash = password_hash

    def get_posts(self, include_private=False):
        """Get user's voice posts"""
        from app.models.voice_post import VoicePost
        return VoicePost.get_by_user(self.id, include_private=include_private)

    def get_post_count(self):
        """Get count of user's published posts"""
        with get_db(current_app.config['DATABASE_PATH']) as conn:
            row = conn.execute(
                'SELECT COUNT(*) as count FROM voice_posts WHERE user_id = ? AND is_published = TRUE',
                (self.id,)
            ).fetchone()
            return row['count'] if row else 0

    def __repr__(self):
        return f'<User {self.username}>'