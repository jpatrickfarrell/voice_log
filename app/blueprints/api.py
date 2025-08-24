from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.models.voice_post import VoicePost
from app.models.user import User
import os

api_bp = Blueprint('api', __name__)

@api_bp.route('/posts', methods=['GET'])
def list_posts():
    """API endpoint to list public posts"""
    page = request.args.get('page', 1, type=int)
    limit = min(request.args.get('limit', 20, type=int), 100)  # Max 100 per page
    offset = (page - 1) * limit
    
    posts = VoicePost.get_public_posts(limit=limit, offset=offset)
    
    posts_data = []
    for post in posts:
        author = User.get_by_id(post.user_id)
        analytics = post.get_analytics()
        
        posts_data.append({
            'id': post.id,
            'slug': post.slug,
            'title': post.title,
            'summary': post.summary,
            'duration_seconds': post.duration_seconds,
            'duration_formatted': post.format_duration(),
            'created_at': post.created_at,
            'author': {
                'username': author.username if author else 'Unknown'
            },
            'analytics': {
                'view_count': analytics['view_count'],
                'play_count': analytics['play_count']
            },
            'urls': {
                'view': f"/posts/{post.slug}",
                'audio': f"/posts/audio/{post.audio_filename}"
            }
        })
    
    return jsonify({
        'posts': posts_data,
        'page': page,
        'limit': limit,
        'has_more': len(posts_data) == limit
    })

@api_bp.route('/posts/<slug>', methods=['GET'])
def get_post(slug):
    """API endpoint to get single post"""
    post = VoicePost.get_by_slug(slug)
    
    if not post:
        return jsonify({'error': 'Post not found'}), 404
    
    # Check privacy
    if post.privacy_level == 'private':
        if not current_user.is_authenticated or current_user.id != post.user_id:
            return jsonify({'error': 'Post not found'}), 404
    
    author = User.get_by_id(post.user_id)
    analytics = post.get_analytics()
    
    post_data = {
        'id': post.id,
        'slug': post.slug,
        'title': post.title,
        'summary': post.summary,
        'transcript': post.transcript,
        'duration_seconds': post.duration_seconds,
        'duration_formatted': post.format_duration(),
        'privacy_level': post.privacy_level,
        'is_published': post.is_published,
        'created_at': post.created_at,
        'updated_at': post.updated_at,
        'author': {
            'username': author.username if author else 'Unknown'
        },
        'analytics': {
            'view_count': analytics['view_count'],
            'play_count': analytics['play_count'],
            'last_viewed': analytics['last_viewed']
        },
        'urls': {
            'view': f"/posts/{post.slug}",
            'audio': f"/posts/audio/{post.audio_filename}"
        }
    }
    
    return jsonify({'post': post_data})

@api_bp.route('/my-posts', methods=['GET'])
@login_required
def my_posts():
    """API endpoint for user's posts"""
    posts = current_user.get_posts(include_private=True)
    
    posts_data = []
    for post in posts:
        analytics = post.get_analytics()
        
        posts_data.append({
            'id': post.id,
            'slug': post.slug,
            'title': post.title,
            'summary': post.summary,
            'duration_seconds': post.duration_seconds,
            'duration_formatted': post.format_duration(),
            'privacy_level': post.privacy_level,
            'is_published': post.is_published,
            'created_at': post.created_at,
            'updated_at': post.updated_at,
            'analytics': {
                'view_count': analytics['view_count'],
                'play_count': analytics['play_count']
            },
            'urls': {
                'view': f"/posts/{post.slug}",
                'edit': f"/posts/edit/{post.slug}",
                'audio': f"/posts/audio/{post.audio_filename}"
            }
        })
    
    return jsonify({'posts': posts_data})

@api_bp.route('/stats', methods=['GET'])
def platform_stats():
    """API endpoint for platform statistics"""
    from app.services.database import get_db
    from flask import current_app
    
    with get_db(current_app.config['DATABASE_PATH']) as conn:
        # Public posts count
        public_posts = conn.execute(
            'SELECT COUNT(*) as count FROM voice_posts WHERE privacy_level = "public" AND is_published = TRUE'
        ).fetchone()['count']
        
        # Total users
        total_users = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()['count']
        
        # Total duration
        total_duration = conn.execute(
            'SELECT SUM(duration_seconds) as total FROM voice_posts WHERE privacy_level = "public" AND is_published = TRUE'
        ).fetchone()['total'] or 0
        
        # Total plays
        total_plays = conn.execute('''
            SELECT SUM(pa.play_count) as total 
            FROM post_analytics pa 
            JOIN voice_posts vp ON pa.post_id = vp.id 
            WHERE vp.privacy_level = "public" AND vp.is_published = TRUE
        ''').fetchone()['total'] or 0
        
        # Recent posts count (last 7 days)
        recent_posts = conn.execute('''
            SELECT COUNT(*) as count 
            FROM voice_posts 
            WHERE privacy_level = "public" 
            AND is_published = TRUE 
            AND datetime(created_at) >= datetime('now', '-7 days')
        ''').fetchone()['count']
    
    return jsonify({
        'total_posts': public_posts,
        'total_users': total_users,
        'total_duration_hours': round(total_duration / 3600, 1),
        'total_plays': total_plays,
        'recent_posts_7d': recent_posts
    })

@api_bp.route('/user/<username>/posts', methods=['GET'])
def user_posts(username):
    """API endpoint for public posts by specific user"""
    user = User.get_by_username(username)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    posts = VoicePost.get_by_user(user.id, include_private=False)
    
    posts_data = []
    for post in posts:
        if post.is_published:  # Only published posts
            analytics = post.get_analytics()
            
            posts_data.append({
                'id': post.id,
                'slug': post.slug,
                'title': post.title,
                'summary': post.summary,
                'duration_seconds': post.duration_seconds,
                'duration_formatted': post.format_duration(),
                'created_at': post.created_at,
                'analytics': {
                    'view_count': analytics['view_count'],
                    'play_count': analytics['play_count']
                },
                'urls': {
                    'view': f"/posts/{post.slug}",
                    'audio': f"/posts/audio/{post.audio_filename}"
                }
            })
    
    return jsonify({
        'user': {
            'username': user.username
        },
        'posts': posts_data
    })

@api_bp.route('/ai-provider')
def get_ai_provider():
    """Get information about configured AI provider"""
    from app.services.transcription_service import TranscriptionService
    
    provider = TranscriptionService._get_api_provider()
    
    if provider == 'gemini':
        return jsonify({
            'provider': 'gemini',
            'name': 'Google Gemini',
            'models': ['gemini-1.5-flash', 'gemini-1.5-pro'],
            'capabilities': ['transcription', 'summary', 'title_generation']
        })
    elif provider == 'openai':
        return jsonify({
            'provider': 'openai',
            'name': 'OpenAI',
            'models': ['whisper-1', 'gpt-3.5-turbo', 'gpt-4'],
            'capabilities': ['transcription', 'summary', 'title_generation']
        })
    else:
        return jsonify({
            'provider': None,
            'name': 'None',
            'models': [],
            'capabilities': [],
            'error': 'No API key configured'
        })

@api_bp.route('/db-health')
def check_database_health():
    """Check database health and connectivity"""
    try:
        from app.services.database import check_database_health
        from app.services.database import get_db
        from flask import current_app
        
        # Check basic connectivity
        with get_db(current_app.config['DATABASE_PATH']) as conn:
            # Check if tables exist
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            table_names = [table[0] for table in tables]
            
            # Check voice_posts table structure
            voice_posts_columns = []
            if 'voice_posts' in table_names:
                voice_posts_columns = conn.execute("PRAGMA table_info(voice_posts)").fetchall()
            
            # Check post_analytics table structure
            post_analytics_columns = []
            if 'post_analytics' in table_names:
                post_analytics_columns = conn.execute("PRAGMA table_info(post_analytics)").fetchall()
            
            # Check users table structure
            users_columns = []
            if 'users' in table_names:
                users_columns = conn.execute("PRAGMA table_info(users)").fetchall()
            
            return jsonify({
                'status': 'healthy',
                'database_path': current_app.config['DATABASE_PATH'],
                'tables': table_names,
                'voice_posts_columns': voice_posts_columns,
                'post_analytics_columns': post_analytics_columns,
                'users_columns': users_columns
            })
            
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'error_type': type(e).__name__
        }), 500

@api_bp.route('/test-audio-conversion')
def test_audio_conversion():
    """Test audio conversion functionality"""
    try:
        from app.services.audio_service import AudioService
        from flask import current_app
        
        # Check if ffmpeg is available
        try:
            import subprocess
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=10)
            ffmpeg_available = result.returncode == 0
            ffmpeg_version = result.stdout.split('\n')[0] if ffmpeg_available else "Not available"
        except Exception as e:
            ffmpeg_available = False
            ffmpeg_version = f"Error: {str(e)}"
        
        # Check upload folder structure
        upload_folder = current_app.config['UPLOAD_FOLDER']
        converted_folder = os.path.join(upload_folder, 'converted')
        
        # Check if directories exist
        upload_exists = os.path.exists(upload_folder)
        converted_exists = os.path.exists(converted_folder)
        
        # List some audio files in uploads
        audio_files = []
        if upload_exists:
            for file in os.listdir(upload_folder):
                if file.lower().endswith(('.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac', '.webm')):
                    audio_files.append(file)
        
        return jsonify({
            'status': 'success',
            'ffmpeg_available': ffmpeg_available,
            'ffmpeg_version': ffmpeg_version,
            'upload_folder': upload_folder,
            'upload_folder_exists': upload_exists,
            'converted_folder': converted_folder,
            'converted_folder_exists': converted_exists,
            'audio_files_found': len(audio_files),
            'audio_files': audio_files[:10]  # Limit to first 10 files
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'error_type': type(e).__name__
        }), 500

@api_bp.route('/test-file/<filename>')
def test_file(filename):
    """Test if a specific file exists in various locations"""
    try:
        from flask import current_app
        import os
        
        upload_folder = current_app.config['UPLOAD_FOLDER']
        
        # Test various possible locations
        locations = {
            'upload_folder': upload_folder,
            'upload_folder_absolute': os.path.abspath(upload_folder),
            'current_working_directory': os.getcwd(),
            'project_root': os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'uploads_from_cwd': os.path.join(os.getcwd(), 'uploads'),
            'uploads_from_project_root': os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')
        }
        
        results = {}
        for name, path in locations.items():
            file_path = os.path.join(path, filename)
            exists = os.path.exists(file_path)
            results[name] = {
                'path': file_path,
                'exists': exists,
                'absolute': os.path.abspath(file_path)
            }
        
        # Also check if the uploads folder itself exists in various locations
        folder_results = {}
        for name, path in locations.items():
            folder_exists = os.path.exists(path)
            folder_results[name] = {
                'path': path,
                'exists': folder_exists,
                'absolute': os.path.abspath(path)
            }
        
        return jsonify({
            'status': 'success',
            'filename': filename,
            'file_locations': results,
            'folder_locations': folder_results
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'error_type': type(e).__name__
        }), 500

@api_bp.route('/debug-paths')
def debug_paths():
    """Debug file paths and configuration"""
    try:
        from flask import current_app
        import os
        
        # Get current working directory
        cwd = os.getcwd()
        
        # Get app configuration
        upload_folder = current_app.config['UPLOAD_FOLDER']
        database_path = current_app.config['DATABASE_PATH']
        
        # Get absolute paths
        upload_abs = os.path.abspath(upload_folder)
        database_abs = os.path.abspath(database_path)
        
        # Check if paths exist
        upload_exists = os.path.exists(upload_folder)
        database_exists = os.path.exists(database_path)
        
        # List contents of upload folder
        upload_contents = []
        if upload_exists:
            try:
                upload_contents = os.listdir(upload_folder)
            except Exception as e:
                upload_contents = [f"Error listing directory: {str(e)}"]
        
        # Check converted folder
        converted_folder = os.path.join(upload_folder, 'converted')
        converted_exists = os.path.exists(converted_folder)
        converted_contents = []
        if converted_exists:
            try:
                converted_contents = os.listdir(converted_folder)
            except Exception as e:
                converted_contents = [f"Error listing directory: {str(e)}"]
        
        # Check specific file paths mentioned in error
        test_files = [
            'recording_2ec0d5ba.webm',
            'recording_2ec0d5ba_converted.mp3'
        ]
        
        file_checks = {}
        for test_file in test_files:
            # Check in uploads folder
            upload_file_path = os.path.join(upload_folder, test_file)
            upload_file_exists = os.path.exists(upload_file_path)
            
            # Check in converted folder
            converted_file_path = os.path.join(upload_folder, 'converted', test_file)
            converted_file_exists = os.path.exists(converted_file_path)
            
            file_checks[test_file] = {
                'upload_path': upload_file_path,
                'upload_exists': upload_file_exists,
                'converted_path': converted_file_path,
                'converted_exists': converted_file_exists
            }
        
        return jsonify({
            'status': 'success',
            'current_working_directory': cwd,
            'upload_folder': upload_folder,
            'upload_folder_absolute': upload_abs,
            'upload_folder_exists': upload_exists,
            'upload_folder_contents': upload_contents,
            'converted_folder': converted_folder,
            'converted_folder_exists': converted_exists,
            'converted_folder_contents': converted_contents,
            'database_path': database_path,
            'database_path_absolute': database_abs,
            'database_exists': database_exists,
            'app_root': os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'file_checks': file_checks
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'error_type': type(e).__name__
        }), 500

@api_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@api_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500