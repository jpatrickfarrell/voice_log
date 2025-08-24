import uuid
from datetime import datetime
from app.services.database import get_db
from flask import current_app, url_for
import os

class VoicePost:
    def __init__(self, id, user_id, title, slug, audio_filename, transcript=None, summary=None,
                 duration_seconds=None, privacy_level='public', is_published=True, 
                 created_at=None, updated_at=None):
        self.id = id
        self.user_id = user_id
        self.title = title
        self.slug = slug
        self.audio_filename = audio_filename
        self.transcript = transcript
        self.summary = summary
        self.duration_seconds = duration_seconds
        self.privacy_level = privacy_level
        self.is_published = is_published
        self.created_at = created_at
        self.updated_at = updated_at

    @classmethod
    def create(cls, user_id, title, audio_filename, transcript=None, summary=None,
               duration_seconds=None, privacy_level='public'):
        """Create a new voice post"""
        slug = cls._generate_unique_slug(title)
        
        with get_db(current_app.config['DATABASE_PATH']) as conn:
            cursor = conn.execute('''
                INSERT INTO voice_posts 
                (user_id, title, slug, audio_filename, transcript, summary, duration_seconds, privacy_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, title, slug, audio_filename, transcript, summary, duration_seconds, privacy_level))
            
            post_id = cursor.lastrowid
            
            # Initialize analytics
            conn.execute('''
                INSERT INTO post_analytics (post_id, view_count, play_count)
                VALUES (?, 0, 0)
            ''', (post_id,))
            
            return cls.get_by_id(post_id)

    @classmethod
    def get_by_id(cls, post_id):
        """Get post by ID"""
        with get_db(current_app.config['DATABASE_PATH']) as conn:
            row = conn.execute('SELECT * FROM voice_posts WHERE id = ?', (post_id,)).fetchone()
            if row:
                return cls(**dict(row))
        return None

    @classmethod
    def get_by_slug(cls, slug):
        """Get post by slug"""
        with get_db(current_app.config['DATABASE_PATH']) as conn:
            row = conn.execute('SELECT * FROM voice_posts WHERE slug = ?', (slug,)).fetchone()
            if row:
                return cls(**dict(row))
        return None

    @classmethod
    def get_public_posts(cls, limit=20, offset=0):
        """Get public published posts"""
        with get_db(current_app.config['DATABASE_PATH']) as conn:
            rows = conn.execute('''
                SELECT vp.*, u.username 
                FROM voice_posts vp 
                JOIN users u ON vp.user_id = u.id
                WHERE vp.privacy_level = 'public' AND vp.is_published = TRUE
                ORDER BY vp.created_at DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset)).fetchall()
            
            posts = []
            for row in rows:
                post = cls(**{k: v for k, v in dict(row).items() if k != 'username'})
                post.username = row['username']
                posts.append(post)
            
            return posts

    @classmethod
    def get_by_user(cls, user_id, include_private=False):
        """Get posts by user"""
        query = '''
            SELECT * FROM voice_posts 
            WHERE user_id = ?
        '''
        params = [user_id]
        
        if not include_private:
            query += ' AND privacy_level = "public"'
        
        query += ' ORDER BY created_at DESC'
        
        with get_db(current_app.config['DATABASE_PATH']) as conn:
            rows = conn.execute(query, params).fetchall()
            return [cls(**dict(row)) for row in rows]

    @classmethod
    def _generate_unique_slug(cls, title):
        """Generate a unique slug from title"""
        import re
        
        # Create base slug from title
        base_slug = re.sub(r'[^\w\s-]', '', title.lower())
        base_slug = re.sub(r'[-\s]+', '-', base_slug).strip('-')
        
        # Add UUID suffix to ensure uniqueness
        unique_suffix = str(uuid.uuid4())[:8]
        slug = f"{base_slug}-{unique_suffix}"
        
        return slug

    def update(self, **kwargs):
        """Update post attributes"""
        updateable_fields = ['title', 'transcript', 'summary', 'privacy_level', 'is_published']
        
        set_clause = []
        params = []
        
        for field, value in kwargs.items():
            if field in updateable_fields:
                set_clause.append(f'{field} = ?')
                params.append(value)
                setattr(self, field, value)
        
        if set_clause:
            set_clause.append('updated_at = CURRENT_TIMESTAMP')
            params.append(self.id)
            
            with get_db(current_app.config['DATABASE_PATH']) as conn:
                conn.execute(
                    f'UPDATE voice_posts SET {", ".join(set_clause)} WHERE id = ?',
                    params
                )

    def delete(self):
        """Delete post and associated files"""
        # Delete audio file
        audio_path = os.path.join(current_app.config['UPLOAD_FOLDER'], self.audio_filename)
        if os.path.exists(audio_path):
            os.remove(audio_path)
        
        # Delete from database
        with get_db(current_app.config['DATABASE_PATH']) as conn:
            conn.execute('DELETE FROM voice_posts WHERE id = ?', (self.id,))

    def get_audio_url(self):
        """Get URL for audio file"""
        return url_for('posts.serve_audio', filename=self.audio_filename)

    def get_public_url(self):
        """Get public URL for post"""
        return url_for('posts.view_post', slug=self.slug)

    def increment_view_count(self):
        """Increment view count"""
        with get_db(current_app.config['DATABASE_PATH']) as conn:
            conn.execute('''
                UPDATE post_analytics 
                SET view_count = view_count + 1, last_viewed = CURRENT_TIMESTAMP
                WHERE post_id = ?
            ''', (self.id,))

    def increment_play_count(self):
        """Increment play count"""
        with get_db(current_app.config['DATABASE_PATH']) as conn:
            conn.execute('''
                UPDATE post_analytics 
                SET play_count = play_count + 1
                WHERE post_id = ?
            ''', (self.id,))

    def get_analytics(self):
        """Get post analytics"""
        with get_db(current_app.config['DATABASE_PATH']) as conn:
            row = conn.execute('''
                SELECT view_count, play_count, last_viewed
                FROM post_analytics WHERE post_id = ?
            ''', (self.id,)).fetchone()
            
            if row:
                return dict(row)
            
            return {'view_count': 0, 'play_count': 0, 'last_viewed': None}

    def format_duration(self):
        """Format duration in minutes and seconds"""
        if not self.duration_seconds:
            return "Unknown"
        
        minutes = int(self.duration_seconds // 60)
        seconds = int(self.duration_seconds % 60)
        return f"{minutes}:{seconds:02d}"

    def __repr__(self):
        return f'<VoicePost {self.title}>'