import os
import uuid
from werkzeug.utils import secure_filename
import subprocess
import wave
import contextlib

ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'flac', 'm4a', 'aac', 'ogg', 'webm'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def allowed_audio_file(filename):
    """Check if file has allowed audio extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_AUDIO_EXTENSIONS

def get_unique_filename(filename):
    """Generate unique filename while preserving extension"""
    name, ext = os.path.splitext(secure_filename(filename))
    unique_name = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
    return unique_name

def save_audio_file(file, upload_folder):
    """Save uploaded audio file and return filename"""
    if not file or file.filename == '':
        return None, "No file selected"
    
    if not allowed_audio_file(file.filename):
        return None, f"File type not allowed. Supported formats: {', '.join(ALLOWED_AUDIO_EXTENSIONS)}"
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        return None, f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
    
    filename = get_unique_filename(file.filename)
    filepath = os.path.join(upload_folder, filename)
    
    try:
        file.save(filepath)
        return filename, None
    except Exception as e:
        return None, f"Error saving file: {str(e)}"

def get_audio_duration(filepath):
    """Get duration of audio file in seconds"""
    try:
        # Try with ffprobe first (more reliable)
        result = subprocess.run([
            'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
            '-of', 'csv=p=0', filepath
        ], capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except (subprocess.SubprocessError, FileNotFoundError, ValueError):
        pass
    
    # Fallback for WAV files using wave module
    if filepath.lower().endswith('.wav'):
        try:
            with contextlib.closing(wave.open(filepath, 'r')) as f:
                frames = f.getnframes()
                rate = f.getframerate()
                return frames / float(rate)
        except:
            pass
    
    # If all else fails, return None
    return None

def convert_to_web_format(input_filepath, output_folder):
    """Convert audio to web-friendly format (MP3) if needed"""
    name, ext = os.path.splitext(os.path.basename(input_filepath))
    
    # If already MP3, no conversion needed
    if ext.lower() == '.mp3':
        return os.path.basename(input_filepath), None
    
    output_filename = f"{name}.mp3"
    output_filepath = os.path.join(output_folder, output_filename)
    
    try:
        # Use ffmpeg to convert to MP3
        result = subprocess.run([
            'ffmpeg', '-i', input_filepath, 
            '-codec:a', 'libmp3lame', 
            '-b:a', '128k',  # 128kbps bitrate for web
            '-y',  # Overwrite output file
            output_filepath
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            # Remove original file if conversion successful
            if os.path.exists(output_filepath):
                os.remove(input_filepath)
                return output_filename, None
            else:
                return None, "Conversion failed: output file not created"
        else:
            return None, f"Conversion failed: {result.stderr}"
            
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        # If ffmpeg not available, keep original file
        return os.path.basename(input_filepath), f"Warning: Could not convert to MP3 (ffmpeg not found). Using original format."

def validate_audio_file(filepath):
    """Validate that file is actually an audio file"""
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'quiet', '-select_streams', 'a:0',
            '-show_entries', 'stream=codec_type', '-of', 'csv=p=0',
            filepath
        ], capture_output=True, text=True)
        
        return result.returncode == 0 and 'audio' in result.stdout
    except (subprocess.SubprocessError, FileNotFoundError):
        # Fallback: check file extension
        return allowed_audio_file(filepath)

def get_audio_metadata(filepath):
    """Extract metadata from audio file"""
    metadata = {
        'duration': get_audio_duration(filepath),
        'format': os.path.splitext(filepath)[1][1:].upper(),
        'size': os.path.getsize(filepath) if os.path.exists(filepath) else 0
    }
    
    try:
        # Try to get additional metadata with ffprobe
        result = subprocess.run([
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', filepath
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            
            # Extract format info
            if 'format' in data:
                format_info = data['format']
                metadata['bitrate'] = format_info.get('bit_rate')
                
                # Extract title from tags if available
                if 'tags' in format_info:
                    tags = format_info['tags']
                    metadata['title'] = tags.get('title') or tags.get('Title')
                    metadata['artist'] = tags.get('artist') or tags.get('Artist')
            
            # Extract audio stream info
            audio_streams = [s for s in data.get('streams', []) if s.get('codec_type') == 'audio']
            if audio_streams:
                stream = audio_streams[0]
                metadata['sample_rate'] = stream.get('sample_rate')
                metadata['channels'] = stream.get('channels')
                metadata['codec'] = stream.get('codec_name')
                
    except (subprocess.SubprocessError, FileNotFoundError, json.JSONDecodeError):
        pass
    
    return metadata