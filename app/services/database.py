import sqlite3
import os
from contextlib import contextmanager

def get_db_connection(db_path):
    """Get database connection with row factory"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def get_db(db_path):
    """Context manager for database connections"""
    conn = get_db_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_database(db_path):
    """Initialize database with tables"""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    with get_db(db_path) as conn:
        # Users table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Voice posts table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS voice_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                audio_filename TEXT NOT NULL,
                transcript TEXT,
                summary TEXT,
                duration_seconds REAL,
                privacy_level TEXT DEFAULT 'public' CHECK (privacy_level IN ('public', 'unlisted', 'private')),
                is_published BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Post analytics table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS post_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                view_count INTEGER DEFAULT 0,
                play_count INTEGER DEFAULT 0,
                last_viewed TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES voice_posts (id) ON DELETE CASCADE
            )
        ''')
        
        # Create indexes
        conn.execute('CREATE INDEX IF NOT EXISTS idx_voice_posts_user_id ON voice_posts (user_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_voice_posts_slug ON voice_posts (slug)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_voice_posts_privacy ON voice_posts (privacy_level)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_voice_posts_published ON voice_posts (is_published)')
        
        # Create default admin user if not exists
        conn.execute('''
            INSERT OR IGNORE INTO users (username, email, password_hash, is_admin)
            VALUES ('admin', 'admin@voicelog.com', 'pbkdf2:sha256:600000$default$4f5c8b9d0e1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e', TRUE)
        ''')

def check_database_health(db_path):
    """Check database health and connectivity"""
    try:
        with get_db(db_path) as conn:
            conn.execute('SELECT COUNT(*) FROM users')
            return True
    except Exception as e:
        print(f"Database health check failed: {e}")
        return False