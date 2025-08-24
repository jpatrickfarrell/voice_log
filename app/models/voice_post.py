import uuid
from datetime import datetime
from app.services.database import get_db
from flask import current_app, url_for
import os

class VoicePost:
    def __init__(self, id, user_id, title, slug, audio_filename, transcript=None, summary=None,
                 duration_seconds=None, privacy_level='public', is_published=True, 
                 created_at=None, updated_at=None, converted_mp3_path=None):
        self.id = id
        self.user_id = user_id
        self.title = title
        self.slug = slug
        self.audio_filename = audio_filename
        self.converted_mp3_path = converted_mp3_path
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
        try:
            current_app.logger.info(f"Creating voice post: user_id={user_id}, title='{title}', audio_filename='{audio_filename}'")
            
            slug = cls._generate_unique_slug(title)
            current_app.logger.info(f"Generated slug: {slug}")
            
            # Convert audio to MP3 if not already MP3
            converted_mp3_path = None
            from app.services.audio_service import AudioService
            
            if not AudioService.is_mp3(audio_filename):
                current_app.logger.info("Converting audio to MP3 format...")
                input_path = os.path.join(current_app.config['UPLOAD_FOLDER'], audio_filename)
                mp3_path, success, error = AudioService.convert_to_mp3(input_path)
                
                if success:
                    # Store relative path from upload folder
                    converted_mp3_path = os.path.relpath(mp3_path, current_app.config['UPLOAD_FOLDER'])
                    current_app.logger.info(f"Audio converted to MP3: {converted_mp3_path}")
                else:
                    current_app.logger.warning(f"Audio conversion failed: {error}")
                    # Continue without conversion, but log the warning
            else:
                current_app.logger.info("Audio is already in MP3 format")
            
            # Use a single database connection for the entire operation
            from app.services.database import get_db_connection
            conn = get_db_connection(current_app.config['DATABASE_PATH'])
            
            try:
                current_app.logger.info("Executing INSERT statement for voice_posts")
                current_app.logger.info(f"Connection type: {type(conn)}")
                
                cursor = conn.execute('''
                    INSERT INTO voice_posts 
                    (user_id, title, slug, audio_filename, converted_mp3_path, transcript, summary, duration_seconds, privacy_level)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, title, slug, audio_filename, converted_mp3_path, transcript, summary, duration_seconds, privacy_level))
                
                post_id = cursor.lastrowid
                current_app.logger.info(f"Inserted voice post with ID: {post_id}")
                
                if not post_id:
                    current_app.logger.error("No post ID returned from INSERT")
                    conn.rollback()
                    return None
                
                # Initialize analytics
                current_app.logger.info("Creating post analytics entry")
                conn.execute('''
                    INSERT INTO post_analytics (post_id, view_count, play_count)
                    VALUES (?, 0, 0)
                ''', (post_id,))
                
                # Verify the post was actually inserted
                current_app.logger.info("Verifying post insertion...")
                verify_row = conn.execute('SELECT id, title, slug FROM voice_posts WHERE id = ?', (post_id,)).fetchone()
                if verify_row:
                    current_app.logger.info(f"Post verification successful: {dict(verify_row)}")
                else:
                    current_app.logger.error("Post verification failed - post not found after insertion!")
                    conn.rollback()
                    return None
                
                # Commit the transaction
                current_app.logger.info("Committing transaction...")
                conn.commit()
                current_app.logger.info("Transaction committed successfully")
                
                # Now fetch the newly created post using a separate connection
                current_app.logger.info(f"Fetching newly created post with ID: {post_id}")
                post = cls.get_by_id(post_id)
                
                if post:
                    current_app.logger.info(f"Successfully created and fetched post: {post}")
                    return post
                else:
                    current_app.logger.error(f"Failed to fetch post after creation. Post ID: {post_id}")
                    return None
                    
            except Exception as e:
                current_app.logger.error(f"Error during post creation: {str(e)}")
                conn.rollback()
                raise
            finally:
                conn.close()
                    
        except Exception as e:
            current_app.logger.error(f"Error creating voice post: {str(e)}")
            current_app.logger.error(f"Exception type: {type(e)}")
            import traceback
            current_app.logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    @classmethod
    def get_by_id(cls, post_id):
        """Get post by ID"""
        try:
            current_app.logger.info(f"Fetching post by ID: {post_id}")
            current_app.logger.info(f"Database path: {current_app.config['DATABASE_PATH']}")
            
            with get_db(current_app.config['DATABASE_PATH']) as conn:
                current_app.logger.info("Executing SELECT query for post")
                query = 'SELECT * FROM voice_posts WHERE id = ?'
                current_app.logger.info(f"Query: {query} with params: ({post_id},)")
                
                row = conn.execute(query, (post_id,)).fetchone()
                
                if row:
                    current_app.logger.info(f"Found post row: {dict(row)}")
                    current_app.logger.info(f"Row type: {type(row)}")
                    current_app.logger.info(f"Row keys: {list(dict(row).keys())}")
                    
                    try:
                        # Check if all required fields are present
                        required_fields = ['id', 'user_id', 'title', 'slug', 'audio_filename']
                        missing_fields = [field for field in required_fields if field not in dict(row)]
                        if missing_fields:
                            current_app.logger.error(f"Missing required fields: {missing_fields}")
                            return None
                        
                        post = cls(**dict(row))
                        current_app.logger.info(f"Successfully created post object: {post}")
                        current_app.logger.info(f"Post object attributes: {post.__dict__}")
                        return post
                    except Exception as e:
                        current_app.logger.error(f"Error creating post object from row: {str(e)}")
                        current_app.logger.error(f"Row data: {dict(row)}")
                        current_app.logger.error(f"Exception type: {type(e)}")
                        import traceback
                        current_app.logger.error(f"Traceback: {traceback.format_exc()}")
                        return None
                else:
                    current_app.logger.error(f"No post found with ID: {post_id}")
                    # Let's also check if the table has any data at all
                    count = conn.execute('SELECT COUNT(*) FROM voice_posts').fetchone()[0]
                    current_app.logger.info(f"Total posts in table: {count}")
                    return None
                    
        except Exception as e:
            current_app.logger.error(f"Error fetching post by ID {post_id}: {str(e)}")
            current_app.logger.error(f"Exception type: {type(e)}")
            import traceback
            current_app.logger.error(f"Traceback: {traceback.format_exc()}")
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
        """Get the URL for the audio file, prioritizing converted MP3 if available"""
        if self.converted_mp3_path:
            return f"/posts/audio/{self.converted_mp3_path}"
        return f"/posts/audio/{self.audio_filename}"
    
    def get_audio_path(self):
        """Get the file system path for the audio file, prioritizing converted MP3 if available"""
        from flask import current_app
        
        if self.converted_mp3_path:
            return os.path.join(current_app.config['UPLOAD_FOLDER'], self.converted_mp3_path)
        return os.path.join(current_app.config['UPLOAD_FOLDER'], self.audio_filename)
    
    def has_mp3_version(self):
        """Check if a converted MP3 version is available"""
        return bool(self.converted_mp3_path)

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