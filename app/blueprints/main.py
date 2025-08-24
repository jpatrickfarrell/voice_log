from flask import Blueprint, render_template, request, jsonify
from flask_login import current_user, login_required
from app.models.voice_post import VoicePost
from app.models.user import User

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Homepage - show recent public posts"""
    posts = VoicePost.get_public_posts(limit=10)
    return render_template('main/index.html', posts=posts)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    user_posts = current_user.get_posts(include_private=True)
    user_stats = {
        'total_posts': len(user_posts),
        'public_posts': len([p for p in user_posts if p.privacy_level == 'public']),
        'private_posts': len([p for p in user_posts if p.privacy_level == 'private']),
        'unlisted_posts': len([p for p in user_posts if p.privacy_level == 'unlisted'])
    }
    
    # Get analytics for user posts
    total_views = 0
    total_plays = 0
    
    for post in user_posts:
        analytics = post.get_analytics()
        total_views += analytics['view_count']
        total_plays += analytics['play_count']
    
    user_stats['total_views'] = total_views
    user_stats['total_plays'] = total_plays
    
    return render_template('main/dashboard.html', 
                         posts=user_posts[:10],  # Show recent 10
                         stats=user_stats)

@main_bp.route('/discover')
def discover():
    """Discover page - browse all public posts"""
    page = request.args.get('page', 1, type=int)
    limit = 20
    offset = (page - 1) * limit
    
    posts = VoicePost.get_public_posts(limit=limit, offset=offset)
    
    # Check if there are more posts
    has_more = len(posts) == limit
    
    return render_template('main/discover.html', 
                         posts=posts, 
                         page=page, 
                         has_more=has_more)

@main_bp.route('/about')
def about():
    """About page"""
    return render_template('main/about.html')

@main_bp.route('/api/stats')
def api_stats():
    """API endpoint for platform statistics"""
    # Get total posts and users
    from app.services.database import get_db
    from flask import current_app
    
    with get_db(current_app.config['DATABASE_PATH']) as conn:
        # Total public posts
        public_posts = conn.execute(
            'SELECT COUNT(*) as count FROM voice_posts WHERE privacy_level = "public" AND is_published = TRUE'
        ).fetchone()['count']
        
        # Total users
        total_users = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()['count']
        
        # Total listening time (sum of all durations)
        total_duration = conn.execute(
            'SELECT SUM(duration_seconds) as total FROM voice_posts WHERE privacy_level = "public" AND is_published = TRUE'
        ).fetchone()['total'] or 0
        
        # Total plays
        total_plays = conn.execute(
            'SELECT SUM(play_count) as total FROM post_analytics pa JOIN voice_posts vp ON pa.post_id = vp.id WHERE vp.privacy_level = "public"'
        ).fetchone()['total'] or 0
    
    return jsonify({
        'total_posts': public_posts,
        'total_users': total_users,
        'total_hours': round(total_duration / 3600, 1),
        'total_plays': total_plays
    })

@main_bp.context_processor
def inject_user():
    """Make current user available in all templates"""
    return dict(current_user=current_user)