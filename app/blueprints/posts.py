from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, send_from_directory, abort, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models.voice_post import VoicePost
from app.services.audio_service import save_audio_file, get_audio_duration, get_audio_metadata
from app.services.transcription_service import TranscriptionService
import os

posts_bp = Blueprint('posts', __name__)

@posts_bp.route('/processing/<int:post_id>')
@login_required
def processing_post(post_id):
    """Show processing page while AI is working on the post"""
    current_app.logger.info(f"Processing page requested for post_id: {post_id}")
    
    post = VoicePost.get_by_id(post_id)
    if not post:
        current_app.logger.error(f"Post not found for ID: {post_id}")
        abort(404)
    
    if post.user_id != current_user.id:
        current_app.logger.error(f"User {current_user.id} not authorized to access post {post_id}")
        abort(404)
    
    current_app.logger.info(f"Rendering processing page for post: {post.id}, slug: {post.slug}")
    current_app.logger.info(f"Post object attributes: {post.__dict__}")
    
    return render_template('posts/processing.html', post=post)

@posts_bp.route('/api/process-post/<int:post_id>', methods=['POST'])
@login_required
def process_post_background(post_id):
    """Background endpoint to process post with AI"""
    post = VoicePost.get_by_id(post_id)
    if not post or post.user_id != current_user.id:
        return jsonify({'error': 'Post not found'}), 404
    
    try:
        # Get user's AI training data
        user_ai_bio = current_user.ai_bio if hasattr(current_user, 'ai_bio') else None
        user_writing_samples = current_user.ai_writing_samples if hasattr(current_user, 'ai_writing_samples') else None
        
        # Get audio file path
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], post.audio_filename)
        
        # Process with AI
        transcript, gen_title, summary, error = TranscriptionService.process_audio_complete(
            filepath, user_ai_bio, user_writing_samples
        )
        
        if error:
            return jsonify({'error': error}), 500
        
        # Update post with AI-generated content
        post.update(
            transcript=transcript,
            summary=summary
        )
        
        # Update title if it was auto-generated from filename
        if post.title == os.path.splitext(post.audio_filename)[0]:
            post.update(title=gen_title)
        
        return jsonify({
            'success': True,
            'post_id': post.id,
            'slug': post.slug
        })
        
    except Exception as e:
        current_app.logger.error(f"Error processing post {post_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@posts_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_post():
    """Create new voice post"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        privacy_level = request.form.get('privacy_level', 'public')
        auto_process = request.form.get('auto_process') == 'on'
        
        # Validate privacy level
        if privacy_level not in ['public', 'unlisted', 'private']:
            privacy_level = 'public'
        
        # Handle file upload
        if 'audio_file' not in request.files:
            flash('No audio file uploaded', 'error')
            return render_template('posts/create.html')
        
        file = request.files['audio_file']
        if file.filename == '':
            flash('No file selected', 'error')
            return render_template('posts/create.html')
        
        # Save audio file
        filename, error = save_audio_file(file, current_app.config['UPLOAD_FOLDER'])
        if error:
            flash(error, 'error')
            return render_template('posts/create.html')
        
        # Get audio duration
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        duration = get_audio_duration(filepath)
        
        # Use filename as title if still no title
        if not title:
            generated_title = os.path.splitext(file.filename)[0]
        else:
            generated_title = title
        
        # Create post first (without transcript/summary)
        try:
            current_app.logger.info(f"Attempting to create post for user {current_user.id}")
            current_app.logger.info(f"Title: {generated_title}")
            current_app.logger.info(f"Audio filename: {filename}")
            current_app.logger.info(f"Duration: {duration}")
            current_app.logger.info(f"Privacy level: {privacy_level}")
            
            post = VoicePost.create(
                user_id=current_user.id,
                title=generated_title,
                audio_filename=filename,
                transcript=None,
                summary=None,
                duration_seconds=duration,
                privacy_level=privacy_level
            )
            
            if post:
                current_app.logger.info(f"Post created successfully with ID: {post.id}, slug: {post.slug}")
                
                if auto_process:
                    # Redirect to processing page for AI processing
                    return redirect(url_for('posts.processing_post', post_id=post.id))
                else:
                    # No AI processing, redirect to view post
                    flash('Voice post created successfully!', 'success')
                    return redirect(url_for('posts.view_post', slug=post.slug))
            else:
                current_app.logger.error("VoicePost.create() returned None")
                flash('Error creating post: VoicePost.create() returned None', 'error')
                
        except Exception as e:
            current_app.logger.error(f"Exception during post creation: {str(e)}")
            current_app.logger.error(f"Exception type: {type(e)}")
            import traceback
            current_app.logger.error(f"Traceback: {traceback.format_exc()}")
            flash(f'Error creating post: {str(e)}', 'error')
    
    return render_template('posts/create.html')

@posts_bp.route('/<slug>')
def view_post(slug):
    """View individual post"""
    post = VoicePost.get_by_slug(slug)
    
    if not post:
        abort(404)
    
    # Check privacy permissions
    if post.privacy_level == 'private':
        if not current_user.is_authenticated or current_user.id != post.user_id:
            abort(404)  # Pretend it doesn't exist
    
    # Increment view count
    post.increment_view_count()
    
    # Get post author
    from app.models.user import User
    author = User.get_by_id(post.user_id)
    
    # Get analytics
    analytics = post.get_analytics()
    
    return render_template('posts/view.html', post=post, author=author, analytics=analytics)

@posts_bp.route('/edit/<slug>', methods=['GET', 'POST'])
@login_required
def edit_post(slug):
    """Edit post"""
    post = VoicePost.get_by_slug(slug)
    
    if not post or post.user_id != current_user.id:
        abort(404)
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        summary = request.form.get('summary', '').strip()
        privacy_level = request.form.get('privacy_level', 'public')
        is_published = request.form.get('is_published') == 'on'
        
        # Validate privacy level
        if privacy_level not in ['public', 'unlisted', 'private']:
            privacy_level = 'public'
        
        if title:
            post.update(
                title=title,
                summary=summary,
                privacy_level=privacy_level,
                is_published=is_published
            )
            flash('Post updated successfully!', 'success')
            return redirect(url_for('posts.view_post', slug=post.slug))
        else:
            flash('Title is required', 'error')
    
    return render_template('posts/edit.html', post=post)

@posts_bp.route('/delete/<slug>', methods=['POST'])
@login_required
def delete_post(slug):
    """Delete post"""
    post = VoicePost.get_by_slug(slug)
    
    if not post or post.user_id != current_user.id:
        abort(404)
    
    post.delete()
    flash('Post deleted successfully!', 'success')
    return redirect(url_for('main.dashboard'))

@posts_bp.route('/my-posts')
@login_required
def my_posts():
    """User's posts management"""
    posts = current_user.get_posts(include_private=True)
    return render_template('posts/my_posts.html', posts=posts)

@posts_bp.route('/process/<slug>', methods=['POST'])
@login_required
def process_post(slug):
    """Process post for transcription and summary"""
    post = VoicePost.get_by_slug(slug)
    
    if not post or post.user_id != current_user.id:
        abort(404)
    
    # Get audio file path
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], post.audio_filename)
    
    if not os.path.exists(filepath):
        return jsonify({'success': False, 'error': 'Audio file not found'})
    
    try:
        transcript, title, summary, error = TranscriptionService.process_audio_complete(filepath)
        
        if error:
            return jsonify({'success': False, 'error': error})
        
        # Update post with generated content
        update_data = {}
        if transcript:
            update_data['transcript'] = transcript
        if summary:
            update_data['summary'] = summary
        
        if update_data:
            post.update(**update_data)
            
        return jsonify({
            'success': True,
            'transcript': transcript,
            'summary': summary,
            'suggested_title': title
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@posts_bp.route('/audio/<filename>')
def serve_audio(filename):
    """Serve audio files with proper headers"""
    try:
        current_app.logger.info(f"Attempting to serve audio: {filename}")
        current_app.logger.info(f"Upload folder: {current_app.config['UPLOAD_FOLDER']}")
        
        # Handle different file path scenarios
        file_path = None
        file_type = "unknown"
        
        # Check if this is a converted MP3 file (stored in converted/ subfolder)
        if filename.endswith('_converted.mp3'):
            converted_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'converted', filename)
            if os.path.exists(converted_path):
                file_path = converted_path
                file_type = "converted_mp3"
                current_app.logger.info(f"Found converted MP3 file: {converted_path}")
        
        # If not found as converted MP3, check if it's an original file
        if not file_path:
            original_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(original_path):
                file_path = original_path
                file_type = "original"
                current_app.logger.info(f"Found original audio file: {original_path}")
        
        # If still not found, check if it's a converted file without the _converted suffix
        if not file_path and not filename.endswith('_converted.mp3'):
            # Try to find the converted version
            base_name = os.path.splitext(filename)[0]
            converted_filename = f"{base_name}_converted.mp3"
            converted_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'converted', converted_filename)
            if os.path.exists(converted_path):
                file_path = converted_path
                file_type = "converted_mp3"
                current_app.logger.info(f"Found converted MP3 file (without suffix): {converted_path}")
        
        if not file_path:
            current_app.logger.error(f"Audio file not found: {filename}")
            current_app.logger.error(f"Checked paths:")
            current_app.logger.error(f"  - Converted: {os.path.join(current_app.config['UPLOAD_FOLDER'], 'converted', filename)}")
            current_app.logger.error(f"  - Original: {os.path.join(current_app.config['UPLOAD_FOLDER'], filename)}")
            abort(404, description=f"Audio file {filename} not found")
        
        # Get file info
        file_size = os.path.getsize(file_path)
        file_extension = os.path.splitext(filename)[1].lower()
        
        # Set appropriate MIME type
        mime_types = {
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.m4a': 'audio/mp4',
            '.aac': 'audio/aac',
            '.ogg': 'audio/ogg',
            '.flac': 'audio/flac',
            '.webm': 'audio/webm'
        }
        
        content_type = mime_types.get(file_extension, 'audio/mpeg')
        
        current_app.logger.info(f"Serving {file_type} file: {file_path} ({content_type}, {file_size} bytes)")
        
        # Set headers for audio streaming
        response = send_file(
            file_path,
            mimetype=content_type,
            as_attachment=False,
            conditional=True  # Enable range requests for streaming
        )
        
        # Add CORS headers
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, HEAD'
        response.headers['Access-Control-Allow-Headers'] = 'Range'
        
        # Add audio-specific headers
        response.headers['Accept-Ranges'] = 'bytes'
        response.headers['Content-Length'] = str(file_size)
        
        current_app.logger.info(f"Audio served successfully: {filename} ({content_type}, {file_size} bytes)")
        return response
        
    except Exception as e:
        current_app.logger.error(f"Error serving audio {filename}: {str(e)}")
        current_app.logger.error(f"Exception type: {type(e)}")
        import traceback
        current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        abort(500)

@posts_bp.route('/increment-play/<slug>', methods=['POST'])
def increment_play(slug):
    """Increment play count for analytics"""
    post = VoicePost.get_by_slug(slug)
    
    if not post:
        return jsonify({'success': False, 'error': 'Post not found'})
    
    # Check privacy permissions
    if post.privacy_level == 'private':
        if not current_user.is_authenticated or current_user.id != post.user_id:
            return jsonify({'success': False, 'error': 'Access denied'})
    
    post.increment_play_count()
    return jsonify({'success': True})

@posts_bp.route('/upload-quick', methods=['POST'])
@login_required
def upload_quick():
    """Quick upload endpoint for mobile/AJAX uploads"""
    if 'audio' not in request.files:
        return jsonify({'success': False, 'error': 'No audio file'})
    
    file = request.files['audio']
    title = request.form.get('title', '').strip()
    privacy_level = request.form.get('privacy_level', 'public')
    
    # Save audio file
    filename, error = save_audio_file(file, current_app.config['UPLOAD_FOLDER'])
    if error:
        return jsonify({'success': False, 'error': error})
    
    # Get duration
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    duration = get_audio_duration(filepath)
    
    # Use filename as title if not provided
    if not title:
        title = os.path.splitext(file.filename)[0]
    
    # Create post
    post = VoicePost.create(
        user_id=current_user.id,
        title=title,
        audio_filename=filename,
        duration_seconds=duration,
        privacy_level=privacy_level
    )
    
    if post:
        return jsonify({
            'success': True,
            'post_id': post.id,
            'slug': post.slug,
            'url': url_for('posts.view_post', slug=post.slug)
        })
    else:
        return jsonify({'success': False, 'error': 'Failed to create post'})