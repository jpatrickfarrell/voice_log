from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.services.database import get_db
from flask import current_app
import os

class User(UserMixin):
    def __init__(self, id, username, email, password_hash, is_admin=False, is_active=True, ai_bio=None, ai_writing_samples=None, display_name=None, website=None, short_bio=None, instagram=None, linkedin=None, twitter=None, facebook=None, created_at=None, updated_at=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.is_admin = is_admin
        self._is_active = is_active
        self.ai_bio = ai_bio
        self.ai_writing_samples = ai_writing_samples
        self.display_name = display_name
        self.website = website
        self.short_bio = short_bio
        self.instagram = instagram
        self.linkedin = linkedin
        self.twitter = twitter
        self.facebook = facebook
        self.created_at = created_at
        self.updated_at = updated_at

    @property
    def is_active(self):
        """Flask-Login required property"""
        return self._is_active

    @is_active.setter
    def is_active(self, value):
        """Allow setting is_active value"""
        self._is_active = value

    @classmethod
    def get_by_id(cls, user_id):
        """Get user by ID"""
        try:
            current_app.logger.info(f"Attempting to fetch user by ID: {user_id}")
            
            # Check if database file exists
            if not os.path.exists(current_app.config['DATABASE_PATH']):
                current_app.logger.error(f"Database file does not exist: {current_app.config['DATABASE_PATH']}")
                return None
            
            with get_db(current_app.config['DATABASE_PATH']) as conn:
                # First, let's check what columns exist in the users table
                cursor = conn.execute("PRAGMA table_info(users)")
                columns = cursor.fetchall()
                current_app.logger.info(f"Users table columns: {columns}")
                
                row = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
                current_app.logger.info(f"Query result: {row}")
                
                if row:
                    current_app.logger.info(f"Found user by ID: {user_id}")
                    current_app.logger.info(f"Row type: {type(row)}")
                    current_app.logger.info(f"Row data: {row}")
                    
                    # Handle both sqlite3.Row and regular tuples
                    if hasattr(row, 'keys'):
                        # sqlite3.Row object
                        user_data = dict(row)
                        current_app.logger.info(f"Using sqlite3.Row, user_data: {user_data}")
                    else:
                        # Regular tuple - extract by position
                        user_data = {
                            'id': row[0],
                            'username': row[1],
                            'email': row[2],
                            'password_hash': row[3],
                            'is_admin': row[4],
                            'is_active': row[5],
                            'ai_bio': row[6] if len(row) > 6 else None,
                            'ai_writing_samples': row[7] if len(row) > 7 else None,
                            'display_name': row[8] if len(row) > 8 else None,
                            'website': row[9] if len(row) > 9 else None,
                            'short_bio': row[10] if len(row) > 10 else None,
                            'instagram': row[11] if len(row) > 11 else None,
                            'linkedin': row[12] if len(row) > 12 else None,
                            'twitter': row[13] if len(row) > 13 else None,
                            'facebook': row[14] if len(row) > 14 else None,
                            'created_at': row[15] if len(row) > 15 else None,
                            'updated_at': row[16] if len(row) > 16 else None
                        }
                        current_app.logger.info(f"Using tuple, user_data: {user_data}")
                    
                    # Create user instance
                    user = cls(
                        id=user_data['id'],
                        username=user_data['username'],
                        email=user_data['email'],
                        password_hash=user_data['password_hash'],
                        is_admin=user_data.get('is_admin', False),
                        is_active=user_data.get('is_active', True),
                        ai_bio=user_data.get('ai_bio'),
                        ai_writing_samples=user_data.get('ai_writing_samples'),
                        display_name=user_data.get('display_name'),
                        website=user_data.get('website'),
                        short_bio=user_data.get('short_bio'),
                        instagram=user_data.get('instagram'),
                        linkedin=user_data.get('linkedin'),
                        twitter=user_data.get('twitter'),
                        facebook=user_data.get('facebook'),
                        created_at=user_data.get('created_at'),
                        updated_at=user_data.get('updated_at')
                    )
                    current_app.logger.info(f"Created user instance: {user}")
                    return user
                else:
                    current_app.logger.info(f"No user found with ID: {user_id}")
                    return None
        except Exception as e:
            current_app.logger.error(f"Error fetching user by ID {user_id}: {e}")
            current_app.logger.error(f"Exception type: {type(e)}")
            import traceback
            current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        return None

    @classmethod
    def get_by_username(cls, username):
        """Get user by username"""
        try:
            current_app.logger.info(f"Attempting to fetch user by username: {username}")
            
            # Check if database file exists
            if not os.path.exists(current_app.config['DATABASE_PATH']):
                current_app.logger.error(f"Database file does not exist: {current_app.config['DATABASE_PATH']}")
                return None
            
            with get_db(current_app.config['DATABASE_PATH']) as conn:
                row = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
                if row:
                    # Handle both sqlite3.Row and regular tuples
                    if hasattr(row, 'keys'):
                        # sqlite3.Row object
                        user_data = dict(row)
                    else:
                        # Regular tuple - extract by position
                        user_data = {
                            'id': row[0],
                            'username': row[1],
                            'email': row[2],
                            'password_hash': row[3],
                            'is_admin': row[4],
                            'is_active': row[5],
                            'ai_bio': row[8] if len(row) > 8 else None,
                            'ai_writing_samples': row[9] if len(row) > 9 else None,
                            'display_name': row[10] if len(row) > 10 else None,
                            'website': row[11] if len(row) > 11 else None,
                            'short_bio': row[12] if len(row) > 12 else None,
                            'instagram': row[13] if len(row) > 13 else None,
                            'linkedin': row[14] if len(row) > 14 else None,
                            'twitter': row[15] if len(row) > 15 else None,
                            'facebook': row[16] if len(row) > 16 else None,
                            'created_at': row[6],
                            'updated_at': row[7]
                        }
                    
                    return cls(
                        id=user_data['id'],
                        username=user_data['username'],
                        email=user_data['email'],
                        password_hash=user_data['password_hash'],
                        is_admin=user_data.get('is_admin', False),
                        is_active=user_data.get('is_active', True),
                        ai_bio=user_data.get('ai_bio'),
                        ai_writing_samples=user_data.get('ai_writing_samples'),
                        display_name=user_data.get('display_name'),
                        website=user_data.get('website'),
                        short_bio=user_data.get('short_bio'),
                        instagram=user_data.get('instagram'),
                        linkedin=user_data.get('linkedin'),
                        twitter=user_data.get('twitter'),
                        facebook=user_data.get('facebook'),
                        created_at=user_data.get('created_at'),
                        updated_at=user_data.get('updated_at')
                    )
        except Exception as e:
            current_app.logger.error(f"Error fetching user by username {username}: {e}")
        return None

    @classmethod
    def get_by_email(cls, email):
        """Get user by email"""
        try:
            current_app.logger.info(f"Attempting to fetch user by email: {email}")
            
            # Check if database file exists
            if not os.path.exists(current_app.config['DATABASE_PATH']):
                current_app.logger.error(f"Database file does not exist: {current_app.config['DATABASE_PATH']}")
                return None
            
            with get_db(current_app.config['DATABASE_PATH']) as conn:
                # First, let's check what columns exist in the users table
                cursor = conn.execute("PRAGMA table_info(users)")
                columns = cursor.fetchall()
                current_app.logger.info(f"Users table columns: {columns}")
                
                row = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
                current_app.logger.info(f"Query result: {row}")
                
                if row:
                    current_app.logger.info(f"Found user by email: {email}")
                    current_app.logger.info(f"Row type: {type(row)}")
                    current_app.logger.info(f"Row data: {row}")
                    
                    # Handle both sqlite3.Row and regular tuples
                    if hasattr(row, 'keys'):
                        # sqlite3.Row object
                        user_data = dict(row)
                        current_app.logger.info(f"Using sqlite3.Row, user_data: {user_data}")
                    else:
                        # Regular tuple - extract by position
                        user_data = {
                            'id': row[0],
                            'username': row[1],
                            'email': row[2],
                            'password_hash': row[3],
                            'is_admin': row[4],
                            'is_active': row[5],
                            'created_at': row[6],
                            'updated_at': row[7]
                        }
                        current_app.logger.info(f"Using tuple, user_data: {user_data}")
                    
                    # Create user instance
                    user = cls(
                        id=user_data['id'],
                        username=user_data['username'],
                        email=user_data['email'],
                        password_hash=user_data['password_hash'],
                        is_admin=user_data.get('is_admin', False),
                        is_active=user_data.get('is_active', True),
                        created_at=user_data.get('created_at'),
                        updated_at=user_data.get('updated_at')
                    )
                    current_app.logger.info(f"Created user instance: {user}")
                    return user
                else:
                    current_app.logger.info(f"No user found with email: {email}")
                    return None
        except Exception as e:
            current_app.logger.error(f"Error fetching user by email {email}: {e}")
            current_app.logger.error(f"Exception type: {type(e)}")
            import traceback
            current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        return None

    @classmethod
    def create(cls, username, email, password, is_admin=False):
        """Create a new user"""
        password_hash = generate_password_hash(password)
        
        try:
            current_app.logger.info(f"Creating user: {username} with email: {email}")
            current_app.logger.info(f"Database path: {current_app.config['DATABASE_PATH']}")
            
            # Check if database file exists
            if not os.path.exists(current_app.config['DATABASE_PATH']):
                current_app.logger.error(f"Database file does not exist: {current_app.config['DATABASE_PATH']}")
                return None
            
            with get_db(current_app.config['DATABASE_PATH']) as conn:
                # Check if user already exists
                existing_user = conn.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email)).fetchone()
                if existing_user:
                    current_app.logger.error(f"User already exists with username: {username} or email: {email}")
                    return None
                
                cursor = conn.execute(
                    'INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)',
                    (username, email, password_hash, is_admin)
                )
                user_id = cursor.lastrowid
                current_app.logger.info(f"User inserted with ID: {user_id}")
                
                if user_id:
                    # Fetch the newly created user
                    current_app.logger.info(f"Fetching newly created user with ID: {user_id}")
                    user = cls.get_by_id(user_id)
                    if user:
                        current_app.logger.info(f"Successfully created and fetched user: {user}")
                        return user
                    else:
                        current_app.logger.error(f"Failed to fetch user after creation. User ID: {user_id}")
                        return None
                else:
                    current_app.logger.error("Failed to get user ID after creation")
                    return None
                    
        except Exception as e:
            current_app.logger.error(f"Error creating user {username}: {e}")
            current_app.logger.error(f"Exception type: {type(e)}")
            import traceback
            current_app.logger.error(f"Traceback: {traceback.format_exc()}")
            raise

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

    def update_ai_training(self, ai_bio=None, ai_writing_samples=None):
        """Update AI training data"""
        with get_db(current_app.config['DATABASE_PATH']) as conn:
            if ai_bio is not None:
                conn.execute(
                    'UPDATE users SET ai_bio = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                    (ai_bio, self.id)
                )
                self.ai_bio = ai_bio
            
            if ai_writing_samples is not None:
                conn.execute(
                    'UPDATE users SET ai_writing_samples = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                    (ai_writing_samples, self.id)
                )
                self.ai_writing_samples = ai_writing_samples

    def update_profile(self, display_name=None, website=None, short_bio=None, instagram=None, linkedin=None, twitter=None, facebook=None):
        """Update user profile information"""
        with get_db(current_app.config['DATABASE_PATH']) as conn:
            if display_name is not None:
                conn.execute(
                    'UPDATE users SET display_name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                    (display_name, self.id)
                )
                self.display_name = display_name
            
            if website is not None:
                conn.execute(
                    'UPDATE users SET website = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                    (website, self.id)
                )
                self.website = website
            
            if short_bio is not None:
                conn.execute(
                    'UPDATE users SET short_bio = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                    (short_bio, self.id)
                )
                self.short_bio = short_bio
            
            if instagram is not None:
                conn.execute(
                    'UPDATE users SET instagram = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                    (instagram, self.id)
                )
                self.instagram = instagram
            
            if linkedin is not None:
                conn.execute(
                    'UPDATE users SET linkedin = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                    (linkedin, self.id)
                )
                self.linkedin = linkedin
            
            if twitter is not None:
                conn.execute(
                    'UPDATE users SET twitter = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                    (twitter, self.id)
                )
                self.twitter = twitter
            
            if facebook is not None:
                conn.execute(
                    'UPDATE users SET facebook = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                    (facebook, self.id)
                )
                self.facebook = facebook

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