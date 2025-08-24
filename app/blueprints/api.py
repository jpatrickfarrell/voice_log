from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.models.voice_post import VoicePost
from app.models.user import User

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

@api_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@api_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500