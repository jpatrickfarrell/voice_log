import openai
import os
import requests
from flask import current_app

class TranscriptionService:
    @staticmethod
    def _get_api_provider():
        """Determine which API provider to use based on available keys"""
        openai_key = os.environ.get('OPENAI_API_KEY')
        gemini_key = os.environ.get('GEMINI_API_KEY')
        
        if gemini_key:
            return 'gemini'
        elif openai_key:
            return 'openai'
        else:
            return None
    
    @staticmethod
    def transcribe_audio(audio_file_path):
        """Transcribe audio file using available API provider"""
        provider = TranscriptionService._get_api_provider()
        
        if not provider:
            return None, "No API key configured (neither OPENAI_API_KEY nor GEMINI_API_KEY)"
        
        if provider == 'gemini':
            return TranscriptionService._transcribe_with_gemini(audio_file_path)
        else:
            return TranscriptionService._transcribe_with_openai(audio_file_path)
    
    @staticmethod
    def _transcribe_with_gemini(audio_file_path):
        """Transcribe audio file using Google Gemini API"""
        api_key = os.environ.get('GEMINI_API_KEY')
        
        try:
            current_app.logger.info("Using Google Gemini API for transcription")
            
            # Read audio file and convert to base64
            import base64
            with open(audio_file_path, 'rb') as audio_file:
                audio_data = audio_file.read()
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # Determine file type from extension
            file_extension = audio_file_path.lower().split('.')[-1]
            mime_type = {
                'mp3': 'audio/mpeg',
                'wav': 'audio/wav',
                'm4a': 'audio/mp4',
                'webm': 'audio/webm',
                'ogg': 'audio/ogg',
                'flac': 'audio/flac'
            }.get(file_extension, 'audio/mpeg')
            
            # Prepare the request to Gemini API
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            
            payload = {
                "contents": [{
                    "parts": [
                        {
                            "text": "Please transcribe this audio file accurately and format it for readability. Break the transcript into logical paragraphs every 3-4 sentences or when there are natural speech breaks (like pauses, topic changes, or transitional phrases). Use <p> tags to separate paragraphs. Return only the formatted transcript without any additional commentary."
                        },
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": audio_base64
                            }
                        }
                    ]
                }],
                "generationConfig": {
                    "temperature": 0.1,
                    "topK": 1,
                    "topP": 1,
                    "maxOutputTokens": 8192
                }
            }
            
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            
            if 'candidates' in result and len(result['candidates']) > 0:
                transcript = result['candidates'][0]['content']['parts'][0]['text']
                current_app.logger.info("Gemini transcription successful")
                return transcript.strip(), None
            else:
                current_app.logger.error("Gemini API returned no candidates")
                return None, "Gemini API returned no transcription result"
                
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Gemini API request error: {str(e)}")
            return None, f"Gemini API request error: {str(e)}"
        except Exception as e:
            current_app.logger.error(f"Gemini transcription error: {str(e)}")
            current_app.logger.error(f"Error type: {type(e)}")
            import traceback
            current_app.logger.error(f"Traceback: {traceback.format_exc()}")
            return None, f"Gemini transcription error: {str(e)}"
    
    @staticmethod
    def _transcribe_with_openai(audio_file_path):
        """Transcribe audio file using OpenAI Whisper API"""
        api_key = os.environ.get('OPENAI_API_KEY')
        
        try:
            current_app.logger.info("Using OpenAI API for transcription")
            
            # Debug: Check OpenAI library version
            current_app.logger.info(f"OpenAI library version: {openai.__version__}")
            
            # Debug: Check for any proxy-related environment variables
            proxy_vars = {k: v for k, v in os.environ.items() if 'proxy' in k.lower() or 'PROXY' in k}
            if proxy_vars:
                current_app.logger.warning(f"Proxy environment variables detected: {proxy_vars}")
            
            # Try to create client with minimal configuration
            try:
                client = openai.OpenAI(
                    api_key=api_key,
                    timeout=60.0
                )
                current_app.logger.info("OpenAI client created successfully with timeout")
            except TypeError as e:
                if 'proxies' in str(e):
                    # Fallback: create client without any additional parameters
                    current_app.logger.warning("Proxies parameter detected, creating client without additional config")
                    client = openai.OpenAI(api_key=api_key)
                else:
                    raise e
            
            with open(audio_file_path, 'rb') as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
                
            # Post-process OpenAI transcript to add paragraph breaks for readability
            formatted_transcript = TranscriptionService._format_transcript_for_readability(transcript)
            return formatted_transcript, None
            
        except openai.OpenAIError as e:
            current_app.logger.error(f"OpenAI API error: {str(e)}")
            return None, f"OpenAI API error: {str(e)}"
        except FileNotFoundError:
            current_app.logger.error(f"Audio file not found: {audio_file_path}")
            return None, "Audio file not found"
        except Exception as e:
            current_app.logger.error(f"Transcription error: {str(e)}")
            current_app.logger.error(f"Error type: {type(e)}")
            import traceback
            current_app.logger.error(f"Traceback: {traceback.format_exc()}")
            return None, f"Transcription error: {str(e)}"
    
    @staticmethod
    def generate_summary(transcript, user_ai_bio=None, user_writing_samples=None):
        """Generate summary from transcript using available API provider"""
        provider = TranscriptionService._get_api_provider()
        
        if not provider:
            return None, "No API key configured (neither OPENAI_API_KEY nor GEMINI_API_KEY)"
        
        if not transcript or len(transcript.strip()) < 50:
            return "Brief voice note", None
        
        if provider == 'gemini':
            return TranscriptionService._generate_summary_with_gemini(transcript, user_ai_bio, user_writing_samples)
        else:
            return TranscriptionService._generate_summary_with_openai(transcript, user_ai_bio, user_writing_samples)
    
    @staticmethod
    def _generate_summary_with_gemini(transcript, user_ai_bio=None, user_writing_samples=None):
        """Generate summary using Google Gemini API"""
        api_key = os.environ.get('GEMINI_API_KEY')
        
        try:
            current_app.logger.info("Using Google Gemini API for summary generation")
            
            # Determine if this should be a short or long post based on transcript length
            word_count = len(transcript.split())
            is_short_post = word_count < 100  # Roughly 30 seconds of speech
            
            # Build personalized context
            personal_context = ""
            if user_ai_bio:
                personal_context += f"\n\nPersonal Context: {user_ai_bio}"
            if user_writing_samples:
                personal_context += f"\n\nWriting Style Examples: {user_writing_samples}"
            
            if is_short_post:
                prompt = f"""SYSTEM: You are a content formatter. Your ONLY job is to take the provided transcript and format it into a readable blog post. DO NOT add any information, facts, examples, or content that is not explicitly stated in the transcript. Only use the exact words and ideas from the transcript.

Transcript: {transcript}

{personal_context}

TASK: Format this short transcript into a brief, readable blog post.

REQUIREMENTS:
- Write in FIRST PERSON using "I", "my", "me" throughout
- ONLY use content from the transcript - NO additional information
- Break the transcript into 2-3 key points
- Keep it brief and focused
- Format with HTML tags for readability
- Use the personal context ONLY for writing style guidance (tone, voice, style) - DO NOT include any of this context in the actual blog post content
- Output clean HTML without any markdown formatting or code block markers

RESTRICTIONS:
- NO adding examples not in the transcript
- NO adding facts not mentioned
- NO expanding on topics not discussed
- NO making up content to fill sections
- NO including any personal context information in the blog post
- The personal context is ONLY for teaching you how to write, not for content
- NO markdown formatting, code blocks, or ``` markers

Output: Clean HTML formatted blog post using ONLY the transcript content."""
            else:
                prompt = f"""SYSTEM: You are a content formatter. Your ONLY job is to take the provided transcript and format it into a structured blog post. DO NOT add any information, facts, examples, or content that is not explicitly stated in the transcript. Only use the exact words and ideas from the transcript.

Transcript: {transcript}

{personal_context}

TASK: Format this transcript into a structured, readable blog post.

REQUIREMENTS:
- Write in FIRST PERSON using "I", "my", "me" throughout
- ONLY use content from the transcript - NO additional information
- Intelligently break the transcript into logical sections based on the actual content
- Extract key points from what was actually said
- Format with proper HTML structure
- Use the personal context ONLY for writing style guidance (tone, voice, style) - DO NOT include any of this context in the actual blog post content
- Output clean HTML without any markdown formatting or code block markers

STRUCTURE GUIDELINES:
<h2>Description</h2>
<p>Start with a compelling hook that captures the reader's attention and briefly describes what this post is about. Use content from the transcript to create interest.</p>

<h2>Key Points</h2>
<ul>
<li>Extract 3-5 main points that were actually discussed</li>
</ul>

<h2>Main Content</h2>
- Create sections ONLY where the transcript naturally breaks into different topics
- Use descriptive headers that reflect the actual content (e.g., "Getting Started", "Core Ideas", "Key Insights", "Practical Steps", "Final Thoughts")
- If the transcript only has enough content for 1-2 sections, don't force more
- Each section should contain substantial content from the transcript

<h2>Summary</h2>
<p>Brief wrap-up using only transcript content</p>

RESTRICTIONS:
- NO adding examples not in the transcript
- NO adding facts not mentioned
- NO expanding on topics not discussed
- NO making up content to fill sections
- NO adding conclusions not stated
- NO including any personal context information in the blog post
- The personal context is ONLY for teaching you how to write, not for content
- NO creating sections just to match a template - only create sections where the content naturally supports them
- NO markdown formatting, code blocks, or ``` markers
- ONLY organize and format what was actually said

Output: Clean HTML formatted blog post using ONLY the transcript content."""
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 1,
                    "topP": 1,
                    "maxOutputTokens": 800
                }
            }
            
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            
            if 'candidates' in result and len(result['candidates']) > 0:
                summary = result['candidates'][0]['content']['parts'][0]['text']
                current_app.logger.info("Gemini summary generation successful")
                return summary.strip(), None
            else:
                current_app.logger.error("Gemini API returned no candidates for summary")
                return None, "Gemini API returned no summary result"
                
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Gemini API request error: {str(e)}")
            return None, f"Gemini API request error: {str(e)}"
        except Exception as e:
            current_app.logger.error(f"Gemini summary generation error: {str(e)}")
            return None, f"Gemini summary generation error: {str(e)}"
    
    @staticmethod
    def _generate_summary_with_openai(transcript, user_ai_bio=None, user_writing_samples=None):
        """Generate summary using OpenAI GPT"""
        api_key = os.environ.get('OPENAI_API_KEY')
        
        try:
            current_app.logger.info("Using OpenAI API for summary generation")
            
            # Try to create client with minimal configuration
            try:
                client = openai.OpenAI(
                    api_key=api_key,
                    timeout=60.0
                )
            except TypeError as e:
                if 'proxies' in str(e):
                    # Fallback: create client without any additional parameters
                    current_app.logger.warning("Proxies parameter detected in summary generation, creating client without additional config")
                    client = openai.OpenAI(api_key=api_key)
                else:
                    raise e
            
            # Determine if this should be a short or long post based on transcript length
            word_count = len(transcript.split())
            is_short_post = word_count < 100  # Roughly 30 seconds of speech
            
            # Build personalized context
            personal_context = ""
            if user_ai_bio:
                personal_context += f"\n\nPersonal Context: {user_ai_bio}"
            if user_writing_samples:
                personal_context += f"\n\nWriting Style Examples: {user_writing_samples}"
            
            if is_short_post:
                prompt = f"""SYSTEM: You are a content formatter. Your ONLY job is to take the provided transcript and format it into a readable blog post. DO NOT add any information, facts, examples, or content that is not explicitly stated in the transcript. Only use the exact words and ideas from the transcript.

Transcript: {transcript}

{personal_context}

TASK: Format this short transcript into a brief, readable blog post.

REQUIREMENTS:
- Write in FIRST PERSON using "I", "my", "me" throughout
- ONLY use content from the transcript - NO additional information
- Break the transcript into 2-3 key points
- Keep it brief and focused
- Format with HTML tags for readability
- Use the personal context ONLY for writing style guidance (tone, voice, style) - DO NOT include any of this context in the actual blog post content
- Output clean HTML without any markdown formatting or code block markers

RESTRICTIONS:
- NO adding examples not in the transcript
- NO adding facts not mentioned
- NO expanding on topics not discussed
- NO making up content to fill sections
- NO including any personal context information in the blog post
- The personal context is ONLY for teaching you how to write, not for content
- NO markdown formatting, code blocks, or ``` markers

Output: Clean HTML formatted blog post using ONLY the transcript content."""
            else:
                prompt = f"""SYSTEM: You are a content formatter. Your ONLY job is to take the provided transcript and format it into a structured blog post. DO NOT add any information, facts, examples, or content that is not explicitly stated in the transcript. Only use the exact words and ideas from the transcript.

Transcript: {transcript}

{personal_context}

TASK: Format this transcript into a structured, readable blog post.

REQUIREMENTS:
- Write in FIRST PERSON using "I", "my", "me" throughout
- ONLY use content from the transcript - NO additional information
- Intelligently break the transcript into logical sections based on the actual content
- Extract key points from what was actually said
- Format with proper HTML structure
- Use the personal context ONLY for writing style guidance (tone, voice, style) - DO NOT include any of this context in the actual blog post content
- Output clean HTML without any markdown formatting or code block markers

STRUCTURE GUIDELINES:
<h2>Description</h2>
<p>Start with a compelling hook that captures the reader's attention and briefly describes what this post is about. Use content from the transcript to create interest.</p>

<h2>Key Points</h2>
<ul>
<li>Extract 3-5 main points that were actually discussed</li>
</ul>

<h2>Main Content</h2>
- Create sections ONLY where the transcript naturally breaks into different topics
- Use descriptive headers that reflect the actual content (e.g., "Getting Started", "Core Ideas", "Key Insights", "Practical Steps", "Final Thoughts")
- If the transcript only has enough content for 1-2 sections, don't force more
- Each section should contain substantial content from the transcript

<h2>Summary</h2>
<p>Brief wrap-up using only transcript content</p>

RESTRICTIONS:
- NO adding examples not in the transcript
- NO adding facts not mentioned
- NO expanding on topics not discussed
- NO making up content to fill sections
- NO adding conclusions not stated
- NO including any personal context information in the blog post
- The personal context is ONLY for teaching you how to write, not for content
- NO creating sections just to match a template - only create sections where the content naturally supports them
- NO markdown formatting, code blocks, or ``` markers
- ONLY organize and format what was actually said

Output: Clean HTML formatted blog post using ONLY the transcript content."""
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
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
        """Generate a compelling title from transcript using available API provider"""
        provider = TranscriptionService._get_api_provider()
        
        if not provider:
            return "Voice Note", None
        
        if not transcript or len(transcript.strip()) < 20:
            return "Quick Voice Note", None
        
        if provider == 'gemini':
            return TranscriptionService._generate_title_with_gemini(transcript, max_length)
        else:
            return TranscriptionService._generate_title_with_openai(transcript, max_length)
    
    @staticmethod
    def _generate_title_with_gemini(transcript, max_length=60):
        """Generate title using Google Gemini API"""
        api_key = os.environ.get('GEMINI_API_KEY')
        
        try:
            current_app.logger.info("Using Google Gemini API for title generation")
            
            prompt = f"""Generate a single, compelling title for this voice note transcript.

Requirements:
- Maximum {max_length} characters
- Capture the main topic or insight
- Be engaging and clickable
- Avoid generic words like "Voice Note" unless necessary

Transcript:
{transcript}

Return only the title, nothing else:"""
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 1,
                    "topP": 1,
                    "maxOutputTokens": 30
                }
            }
            
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            
            if 'candidates' in result and len(result['candidates']) > 0:
                title = result['candidates'][0]['content']['parts'][0]['text']
                current_app.logger.info("Gemini title generation successful")
                
                # Clean up title
                title = title.strip()
                
                # Remove quotes if present
                if title.startswith('"') and title.endswith('"'):
                    title = title[1:-1]
                
                # Remove common prefixes that AI might add
                prefixes_to_remove = [
                    "Here are a few title options under 60 characters:",
                    "Title:",
                    "Suggested title:",
                    "Here's a title:",
                    "A good title would be:"
                ]
                
                for prefix in prefixes_to_remove:
                    if title.lower().startswith(prefix.lower()):
                        title = title[len(prefix):].strip()
                        break
                
                # Truncate if too long
                if len(title) > max_length:
                    title = title[:max_length-3] + "..."
                
                return title, None
            else:
                current_app.logger.error("Gemini API returned no candidates for title")
                return None, "Gemini API returned no title result"
                
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Gemini API request error: {str(e)}")
            return None, f"Gemini API request error: {str(e)}"
        except Exception as e:
            current_app.logger.error(f"Gemini title generation error: {str(e)}")
            return None, f"Gemini title generation error: {str(e)}"
    
    @staticmethod
    def _generate_title_with_openai(transcript, max_length=60):
        """Generate title using OpenAI GPT"""
        api_key = os.environ.get('OPENAI_API_KEY')
        
        try:
            current_app.logger.info("Using OpenAI API for title generation")
            
            # Try to create client with minimal configuration
            try:
                client = openai.OpenAI(
                    api_key=api_key,
                    timeout=60.0
                )
            except TypeError as e:
                if 'proxies' in str(e):
                    # Fallback: create client without any additional parameters
                    current_app.logger.warning("Proxies parameter detected in title generation, creating client without additional config")
                    client = openai.OpenAI(api_key=api_key)
                else:
                    raise e
            
            prompt = f"""Generate a single, compelling title for this voice note transcript.

Requirements:
- Maximum {max_length} characters
- Capture the main topic or insight
- Be engaging and clickable
- Avoid generic words like "Voice Note" unless necessary

Transcript:
{transcript}

Return only the title, nothing else:"""
            
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
            
            # Remove common prefixes that AI might add
            prefixes_to_remove = [
                "Here are a few title options under 60 characters:",
                "Title:",
                "Suggested title:",
                "Here's a title:",
                "A good title would be:"
            ]
            
            for prefix in prefixes_to_remove:
                if title.lower().startswith(prefix.lower()):
                    title = title[len(prefix):].strip()
                    break
            
            # Truncate if too long
            if len(title) > max_length:
                title = title[:max_length-3] + "..."
            
            return title, None
            
        except openai.OpenAIError as e:
            return None, f"Title generation error: {str(e)}"
        except Exception as e:
            return None, f"Title generation error: {str(e)}"

    @staticmethod
    def process_audio_complete(audio_file_path, user_ai_bio=None, user_writing_samples=None):
        """Complete processing: transcription, title, and summary"""
        # Get transcript
        transcript, error = TranscriptionService.transcribe_audio(audio_file_path)
        if error:
            return None, None, None, error
        
        # Generate title
        title, title_error = TranscriptionService.generate_title(transcript)
        if title_error:
            title = "Voice Note"  # Fallback title
        
        # Generate summary with user's AI training data
        summary, summary_error = TranscriptionService.generate_summary(transcript, user_ai_bio, user_writing_samples)
        if summary_error:
            summary = transcript[:200] + "..." if len(transcript) > 200 else transcript
        
        return transcript, title, summary, None
    
    @staticmethod
    def _format_transcript_for_readability(transcript):
        """Format transcript text into readable paragraphs with HTML tags"""
        if not transcript or not isinstance(transcript, str):
            return transcript
        
        # Split transcript into sentences
        import re
        sentences = re.split(r'(?<=[.!?])\s+', transcript.strip())
        
        # Group sentences into paragraphs
        paragraphs = []
        current_paragraph = []
        
        for sentence in sentences:
            current_paragraph.append(sentence)
            
            # Create a new paragraph every 3-4 sentences or when there's a natural break
            if (len(current_paragraph) >= 3 or 
                len(sentence) > 100 or 
                any(phrase in sentence for phrase in ['So,', 'Now,', 'Well,', 'Anyway,', 'First,', 'Second,', 'Finally,', 'In conclusion,'])):
                
                if current_paragraph:
                    paragraphs.append(' '.join(current_paragraph))
                    current_paragraph = []
        
        # Add any remaining sentences as the last paragraph
        if current_paragraph:
            paragraphs.append(' '.join(current_paragraph))
        
        # Format as HTML paragraphs
        formatted_transcript = ''.join([f'<p>{paragraph.strip()}</p>' for paragraph in paragraphs])
        
        return formatted_transcript