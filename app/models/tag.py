from app.services.database import get_db
from flask import current_app

class Tag:
    def __init__(self, id, name, description=None, color='#6c757d', created_at=None):
        self.id = id
        self.name = name
        self.description = description
        self.color = color
        self.created_at = created_at
    
    @classmethod
    def get_by_id(cls, tag_id):
        """Get tag by ID"""
        with get_db(current_app.config['DATABASE_PATH']) as conn:
            row = conn.execute('SELECT * FROM tags WHERE id = ?', (tag_id,)).fetchone()
            if row:
                return cls(**dict(row))
            return None
    
    @classmethod
    def get_by_name(cls, name):
        """Get tag by name"""
        with get_db(current_app.config['DATABASE_PATH']) as conn:
            row = conn.execute('SELECT * FROM tags WHERE name = ?', (name,)).fetchone()
            if row:
                return cls(**dict(row))
            return None
    
    @classmethod
    def get_all(cls):
        """Get all tags"""
        with get_db(current_app.config['DATABASE_PATH']) as conn:
            rows = conn.execute('SELECT * FROM tags ORDER BY name').fetchall()
            return [cls(**dict(row)) for row in rows]
    
    @classmethod
    def create(cls, name, description=None, color='#6c757d'):
        """Create a new tag"""
        with get_db(current_app.config['DATABASE_PATH']) as conn:
            cursor = conn.execute(
                'INSERT INTO tags (name, description, color) VALUES (?, ?, ?)',
                (name, description, color)
            )
            tag_id = cursor.lastrowid
            return cls.get_by_id(tag_id)
    
    def update(self, **kwargs):
        """Update tag attributes"""
        updateable_fields = ['name', 'description', 'color']
        
        set_clause = []
        params = []
        
        for field, value in kwargs.items():
            if field in updateable_fields:
                set_clause.append(f'{field} = ?')
                params.append(value)
                setattr(self, field, value)
        
        if set_clause:
            params.append(self.id)
            with get_db(current_app.config['DATABASE_PATH']) as conn:
                conn.execute(
                    f'UPDATE tags SET {", ".join(set_clause)} WHERE id = ?',
                    params
                )
    
    def delete(self):
        """Delete tag (will also remove from all posts)"""
        with get_db(current_app.config['DATABASE_PATH']) as conn:
            conn.execute('DELETE FROM tags WHERE id = ?', (self.id,))
    
    @classmethod
    def get_tags_for_post(cls, post_id):
        """Get all tags for a specific post"""
        with get_db(current_app.config['DATABASE_PATH']) as conn:
            rows = conn.execute('''
                SELECT t.* FROM tags t
                JOIN post_tags pt ON t.id = pt.tag_id
                WHERE pt.post_id = ?
                ORDER BY t.name
            ''', (post_id,)).fetchall()
            return [cls(**dict(row)) for row in rows]
    
    @classmethod
    def add_tag_to_post(cls, post_id, tag_id):
        """Add a tag to a post"""
        with get_db(current_app.config['DATABASE_PATH']) as conn:
            try:
                conn.execute(
                    'INSERT INTO post_tags (post_id, tag_id) VALUES (?, ?)',
                    (post_id, tag_id)
                )
                return True
            except Exception:
                return False
    
    @classmethod
    def remove_tag_from_post(cls, post_id, tag_id):
        """Remove a tag from a post"""
        with get_db(current_app.config['DATABASE_PATH']) as conn:
            conn.execute(
                'DELETE FROM post_tags WHERE post_id = ? AND tag_id = ?',
                (post_id, tag_id)
            )
    
    @classmethod
    def get_popular_tags(cls, limit=10):
        """Get most popular tags by usage count"""
        with get_db(current_app.config['DATABASE_PATH']) as conn:
            rows = conn.execute('''
                SELECT t.*, COUNT(pt.post_id) as usage_count
                FROM tags t
                JOIN post_tags pt ON t.id = pt.tag_id
                JOIN voice_posts vp ON pt.post_id = vp.id
                WHERE vp.privacy_level = 'public' AND vp.is_published = TRUE
                GROUP BY t.id
                ORDER BY usage_count DESC
                LIMIT ?
            ''', (limit,)).fetchall()
            
            tags = []
            for row in rows:
                tag = cls(**{k: v for k, v in dict(row).items() if k != 'usage_count'})
                tag.usage_count = row['usage_count']
                tags.append(tag)
            
            return tags
