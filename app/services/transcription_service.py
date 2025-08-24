import openai
import os
from flask import current_app

class TranscriptionService:
    @staticmethod
    def transcribe_audio(audio_file_path):
        """Transcribe audio file using OpenAI Whisper API"""
        api_key = os.environ.get('OPENAI_API_KEY')
        
        if not api_key:
            return None, "OpenAI API key not configured"
        
        try:
            client = openai.OpenAI(api_key=api_key)
            
            with open(audio_file_path, 'rb') as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
                
            return transcript, None
            
        except openai.OpenAIError as e:
            return None, f"OpenAI API error: {str(e)}"
        except FileNotFoundError:
            return None, "Audio file not found"
        except Exception as e:
            return None, f"Transcription error: {str(e)}"
    
    @staticmethod
    def generate_summary(transcript):
        """Generate summary from transcript using OpenAI GPT"""
        api_key = os.environ.get('OPENAI_API_KEY')
        
        if not api_key:
            return None, "OpenAI API key not configured"
        
        if not transcript or len(transcript.strip()) < 50:
            return "Brief voice note", None
        
        try:
            client = openai.OpenAI(api_key=api_key)
            
            prompt = f"""Create a concise, engaging summary of this voice note transcript. The summary should:
1. Be 1-3 sentences maximum
2. Capture the main topic or key insight
3. Be written in an engaging, blog-style tone
4. Work well as a preview for readers

Transcript:
{transcript}

Summary:"""
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.7
            )
            
            summary = response.choices[0].message.content.strip()
            return summary, None
            
        except openai.OpenAIError as e:
            return None, f"OpenAI API error: {str(e)}"
        except Exception as e:
            return None, f"Summary generation error: {str(e)}"
    
    @staticmethod
    def generate_title(transcript, max_length=60):
        """Generate a compelling title from transcript"""
        api_key = os.environ.get('OPENAI_API_KEY')
        
        if not api_key:
            return "Voice Note", None
        
        if not transcript or len(transcript.strip()) < 20:
            return "Quick Voice Note", None
        
        try:
            client = openai.OpenAI(api_key=api_key)
            
            prompt = f"""Create a compelling, concise title for this voice note transcript. The title should:
1. Be {max_length} characters or less
2. Capture the main topic or insight
3. Be engaging and clickable
4. Avoid generic words like "Voice Note" unless necessary

Transcript:
{transcript}

Title:"""
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=30,
                temperature=0.7
            )
            
            title = response.choices[0].message.content.strip()
            
            # Remove quotes if present
            if title.startswith('"') and title.endswith('"'):
                title = title[1:-1]
            
            # Truncate if too long
            if len(title) > max_length:
                title = title[:max_length-3] + "..."
            
            return title, None
            
        except openai.OpenAIError as e:
            return None, f"OpenAI API error: {str(e)}"
        except Exception as e:
            return None, f"Title generation error: {str(e)}"

    @staticmethod
    def process_audio_complete(audio_file_path):
        """Complete processing: transcription, title, and summary"""
        # Get transcript
        transcript, error = TranscriptionService.transcribe_audio(audio_file_path)
        if error:
            return None, None, None, error
        
        # Generate title
        title, title_error = TranscriptionService.generate_title(transcript)
        if title_error:
            title = "Voice Note"  # Fallback title
        
        # Generate summary
        summary, summary_error = TranscriptionService.generate_summary(transcript)
        if summary_error:
            summary = transcript[:200] + "..." if len(transcript) > 200 else transcript
        
        return transcript, title, summary, None