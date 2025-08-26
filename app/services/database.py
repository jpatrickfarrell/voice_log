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
    print(f"Initializing database at: {db_path}")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    with get_db(db_path) as conn:
        print("Creating users table...")
        # Users table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                ai_bio TEXT,
                ai_writing_samples TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("Users table created/verified")
        
        # Add AI training columns if they don't exist (for existing databases)
        try:
            conn.execute('ALTER TABLE users ADD COLUMN ai_bio TEXT')
            print("Added ai_bio column to existing users table")
        except sqlite3.OperationalError:
            # Column already exists
            print("ai_bio column already exists")
            
        try:
            conn.execute('ALTER TABLE users ADD COLUMN ai_writing_samples TEXT')
            print("Added ai_writing_samples column to existing users table")
        except sqlite3.OperationalError:
            # Column already exists
            print("ai_writing_samples column already exists")
        
        # Add new profile fields if they don't exist (for existing databases)
        try:
            conn.execute('ALTER TABLE users ADD COLUMN display_name TEXT')
            print("Added display_name column to existing users table")
        except sqlite3.OperationalError:
            # Column already exists
            print("display_name column already exists")
            
        try:
            conn.execute('ALTER TABLE users ADD COLUMN website TEXT')
            print("Added website column to existing users table")
        except sqlite3.OperationalError:
            # Column already exists
            print("website column already exists")
            
        try:
            conn.execute('ALTER TABLE users ADD COLUMN short_bio TEXT')
            print("Added short_bio column to existing users table")
        except sqlite3.OperationalError:
            # Column already exists
            print("short_bio column already exists")
            
        try:
            conn.execute('ALTER TABLE users ADD COLUMN instagram TEXT')
            print("Added instagram column to existing users table")
        except sqlite3.OperationalError:
            # Column already exists
            print("instagram column already exists")
            
        try:
            conn.execute('ALTER TABLE users ADD COLUMN linkedin TEXT')
            print("Added linkedin column to existing users table")
        except sqlite3.OperationalError:
            # Column already exists
            print("linkedin column already exists")
            
        try:
            conn.execute('ALTER TABLE users ADD COLUMN twitter TEXT')
            print("Added twitter column to existing users table")
        except sqlite3.OperationalError:
            # Column already exists
            print("twitter column already exists")
            
        try:
            conn.execute('ALTER TABLE users ADD COLUMN facebook TEXT')
            print("Added facebook column to existing users table")
        except sqlite3.OperationalError:
            # Column already exists
            print("facebook column already exists")
        
        print("Creating voice_posts table...")
        # Voice posts table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS voice_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                audio_filename TEXT NOT NULL,
                converted_mp3_path TEXT,
                header_image TEXT,
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
        print("Voice_posts table created/verified")
        
        # Add converted_mp3_path column if it doesn't exist (for existing databases)
        try:
            conn.execute('ALTER TABLE voice_posts ADD COLUMN converted_mp3_path TEXT')
            print("Added converted_mp3_path column to existing voice_posts table")
        except sqlite3.OperationalError:
            # Column already exists
            print("converted_mp3_path column already exists")
        
        # Add header_image column if it doesn't exist (for existing databases)
        try:
            conn.execute('ALTER TABLE voice_posts ADD COLUMN header_image TEXT')
            print("Added header_image column to existing voice_posts table")
        except sqlite3.OperationalError:
            # Column already exists
            print("header_image column already exists")
        
        print("Creating post_analytics table...")
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
        print("Post_analytics table created/verified")
        
        # Create indexes
        print("Creating indexes...")
        conn.execute('CREATE INDEX IF NOT EXISTS idx_voice_posts_user_id ON voice_posts (user_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_voice_posts_slug ON voice_posts (slug)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_voice_posts_privacy ON voice_posts (privacy_level)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_voice_posts_published ON voice_posts (is_published)')
        print("Indexes created/verified")
        
        # Create tags table
        print("Creating tags table...")
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                color TEXT DEFAULT '#6c757d',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("Tags table created/verified")
        
        # Create post_tags junction table
        print("Creating post_tags table...")
        conn.execute('''
            CREATE TABLE IF NOT EXISTS post_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES voice_posts (id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE,
                UNIQUE(post_id, tag_id)
            )
        ''')
        print("Post_tags table created/verified")
        
        # Create indexes for tags
        print("Creating tag indexes...")
        conn.execute('CREATE INDEX IF NOT EXISTS idx_tags_name ON tags (name)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_post_tags_post_id ON post_tags (post_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_post_tags_tag_id ON post_tags (tag_id)')
        print("Tag indexes created/verified")
        
        # Create subscriptions table
        print("Creating subscriptions table...")
        conn.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subscriber_id INTEGER NOT NULL,
                creator_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subscriber_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (creator_id) REFERENCES users (id) ON DELETE CASCADE,
                UNIQUE(subscriber_id, creator_id)
            )
        ''')
        print("Subscriptions table created/verified")
        
        # Create indexes for subscriptions
        print("Creating subscription indexes...")
        conn.execute('CREATE INDEX IF NOT EXISTS idx_subscriptions_subscriber_id ON subscriptions (subscriber_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_subscriptions_creator_id ON subscriptions (creator_id)')
        print("Subscription indexes created/verified")
        
        # Insert some default tags
        print("Inserting default tags...")
        default_tags = [
            ('Technology', 'Tech and software related content', '#007bff'),
            ('Business', 'Business and entrepreneurship content', '#28a745'),
            ('Health', 'Health and wellness content', '#dc3545'),
            ('Education', 'Educational and learning content', '#ffc107'),
            ('Entertainment', 'Entertainment and media content', '#e83e8c'),
            ('Science', 'Scientific and research content', '#17a2b8'),
            ('Lifestyle', 'Lifestyle and personal content', '#6f42c1'),
            ('News', 'Current events and news content', '#fd7e14')
        ]
        
        for tag_name, description, color in default_tags:
            conn.execute('''
                INSERT OR IGNORE INTO tags (name, description, color)
                VALUES (?, ?, ?)
            ''', (tag_name, description, color))
        print("Default tags inserted/verified")
        
        # Create default admin user if not exists
        print("Checking for default admin user...")
        conn.execute('''
            INSERT OR IGNORE INTO users (username, email, password_hash, is_admin)
            VALUES ('admin', 'admin@voicelog.com', 'pbkdf2:sha256:600000$default$4f5c8b9d0e1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e', TRUE)
        ''')
        print("Database initialization complete!")

def check_database_health(db_path):
    """Check database health and connectivity"""
    try:
        with get_db(db_path) as conn:
            conn.execute('SELECT COUNT(*) FROM users')
            return True
    except Exception as e:
        print(f"Database health check failed: {e}")
        return False