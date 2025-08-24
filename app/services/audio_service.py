import os
import uuid
from werkzeug.utils import secure_filename
import subprocess
import wave
import contextlib
import tempfile
from flask import current_app
import logging

logger = logging.getLogger(__name__)

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

class AudioService:
    """Service for handling audio file operations including conversion to MP3"""
    
    @staticmethod
    def convert_to_mp3(input_path, output_filename=None):
        """
        Convert audio file to MP3 format using ffmpeg
        
        Args:
            input_path (str): Path to input audio file
            output_filename (str): Optional output filename (without extension)
            
        Returns:
            tuple: (mp3_path, success, error_message)
        """
        try:
            # Debug: Log the paths being used
            logger.info(f"AudioService.convert_to_mp3 called with input_path: {input_path}")
            logger.info(f"Current working directory: {os.getcwd()}")
            
            # Check if input file exists
            if not os.path.exists(input_path):
                logger.error(f"Input file not found: {input_path}")
                logger.error(f"Absolute path: {os.path.abspath(input_path)}")
                return None, False, f"Input file not found: {input_path}"
            
            # Generate output filename if not provided
            if not output_filename:
                base_name = os.path.splitext(os.path.basename(input_path))[0]
                output_filename = f"{base_name}_converted"
            
            # Create output directory for converted files
            converted_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'converted')
            logger.info(f"Creating converted directory: {converted_dir}")
            os.makedirs(converted_dir, exist_ok=True)
            
            # Set output path
            output_path = os.path.join(converted_dir, f"{output_filename}.mp3")
            logger.info(f"Output path: {output_path}")
            
            # Check if ffmpeg is available
            try:
                subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                return None, False, "ffmpeg is not installed or not available in PATH"
            
            # Convert to MP3 with good quality settings
            cmd = [
                'ffmpeg',
                '-i', input_path,  # Input file
                '-c:a', 'mp3',     # Audio codec: MP3
                '-b:a', '192k',    # Bitrate: 192kbps for good quality
                '-ar', '44100',    # Sample rate: 44.1kHz
                '-ac', '2',        # Channels: Stereo
                '-y',              # Overwrite output file if it exists
                output_path
            ]
            
            logger.info(f"Converting audio: {' '.join(cmd)}")
            
            # Run conversion
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                # Verify output file exists and has size > 0
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    logger.info(f"Audio conversion successful: {output_path}")
                    return output_path, True, None
                else:
                    return None, False, "Output file is empty or missing after conversion"
            else:
                error_msg = f"ffmpeg conversion failed: {result.stderr}"
                logger.error(error_msg)
                return None, False, error_msg
                
        except subprocess.TimeoutExpired:
            return None, False, "Audio conversion timed out (took longer than 5 minutes)"
        except Exception as e:
            error_msg = f"Audio conversion error: {str(e)}"
            logger.error(error_msg)
            return None, False, error_msg
    
    @staticmethod
    def get_audio_info(file_path):
        """
        Get audio file information using ffprobe
        
        Args:
            file_path (str): Path to audio file
            
        Returns:
            dict: Audio file information
        """
        try:
            if not os.path.exists(file_path):
                return None
            
            # Check if ffprobe is available
            try:
                subprocess.run(['ffprobe', '-version'], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                return None
            
            # Get audio information
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            if result.returncode == 0:
                import json
                info = json.loads(result.stdout)
                return info
            else:
                logger.error(f"ffprobe failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting audio info: {str(e)}")
            return None
    
    @staticmethod
    def cleanup_temp_files(file_paths):
        """
        Clean up temporary audio files
        
        Args:
            file_paths (list): List of file paths to delete
        """
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Cleaned up temporary file: {file_path}")
            except Exception as e:
                logger.error(f"Error cleaning up file {file_path}: {str(e)}")
    
    @staticmethod
    def is_mp3(file_path):
        """
        Check if file is already in MP3 format
        
        Args:
            file_path (str): Path to audio file
            
        Returns:
            bool: True if file is MP3, False otherwise
        """
        if not file_path:
            return False
        
        # Check file extension
        _, ext = os.path.splitext(file_path.lower())
        return ext == '.mp3'
    
    @staticmethod
    def get_converted_mp3_path(original_filename):
        """
        Get the path to the converted MP3 file for a given original filename
        
        Args:
            original_filename (str): Original audio filename
            
        Returns:
            str: Path to converted MP3 file
        """
        base_name = os.path.splitext(original_filename)[0]
        converted_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'converted')
        return os.path.join(converted_dir, f"{base_name}_converted.mp3")