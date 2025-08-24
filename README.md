# Voice Log

Transform your voice into listenable blog posts with automatic transcription, AI-powered summaries, and instant publishing.

## Features

🎙️ **Record Anywhere** - Upload audio from any device  
📝 **Auto Transcription** - AI-powered speech-to-text using OpenAI Whisper  
🤖 **Smart Summaries** - Generate compelling summaries automatically  
🔗 **Instant Publishing** - Get public permalinks immediately  
🔒 **Privacy Controls** - Public, unlisted, or private posts  
📱 **Mobile Optimized** - Perfect for recording on your phone  

## Quick Start

### Using Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd voice_log
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration (especially OPENAI_API_KEY for AI features)
   ```

3. **Start the application**
   ```bash
   make build
   make up
   ```

4. **Visit the application**
   ```
   http://localhost:5010
   ```

### Native Development

1. **Set up development environment**
   ```bash
   make native-init
   source venv/bin/activate
   ```

2. **Configure environment**
   ```bash
   # Edit .env file with your settings
   nano .env
   ```

3. **Initialize database**
   ```bash
   make init-db
   ```

4. **Run the application**
   ```bash
   make native-run
   ```

## Configuration

### Required Environment Variables

```bash
# OpenAI API Key (for transcription and summaries)
OPENAI_API_KEY=your-openai-api-key-here

# Flask secret key (change in production)
SECRET_KEY=your-secret-key-here
```

### Optional Environment Variables

```bash
# Server configuration
HOST=0.0.0.0
PORT=5010
FLASK_DEBUG=False

# File storage
UPLOAD_FOLDER=uploads
DATABASE_PATH=data/voice_log.db
```

## Available Commands

### Docker Management
```bash
make build       # Build Docker image
make up          # Start application
make down        # Stop application
make restart     # Restart application
make logs        # View logs
make shell       # Open container shell
make status      # Show container status
make clean       # Remove containers and images
```

### Database Operations
```bash
make init-db     # Initialize database
make backup      # Create backup
```

### Development
```bash
make native-init # Set up native development
make native-run  # Run natively
make dev         # Quick start for development
make reset       # Reset everything
```

## Architecture

### Flask Blueprint Structure
```
app/
├── __init__.py          # Application factory
├── extensions.py        # Flask extensions
├── blueprints/         # Route organization
│   ├── main.py         # Homepage and dashboard
│   ├── auth.py         # Authentication
│   ├── posts.py        # Voice post management
│   └── api.py          # REST API
├── models/             # Data models
│   ├── user.py         # User model
│   └── voice_post.py   # Voice post model
└── services/           # Business logic
    ├── database.py     # Database operations
    ├── audio_service.py # Audio processing
    └── transcription_service.py # AI services
```

### Database Schema

**Users Table**
- id, username, email, password_hash
- is_admin, is_active, timestamps

**Voice Posts Table**
- id, user_id, title, slug, audio_filename
- transcript, summary, duration_seconds
- privacy_level (public/unlisted/private)
- is_published, timestamps

**Post Analytics Table**
- post_id, view_count, play_count, last_viewed

## API Endpoints

### Public API
```
GET  /api/posts           # List public posts
GET  /api/posts/{slug}    # Get single post
GET  /api/stats           # Platform statistics
GET  /api/user/{username}/posts # User's public posts
```

### Authenticated API
```
GET  /api/my-posts        # User's posts
POST /posts/upload-quick  # Quick upload
POST /posts/process/{slug} # Process post
```

## Audio Processing

### Supported Formats
- MP3, WAV, FLAC, M4A, AAC, OGG, WEBM
- Maximum file size: 50MB
- Automatic web optimization (converts to MP3)

### AI Processing
- **Transcription**: OpenAI Whisper API
- **Title Generation**: GPT-3.5 Turbo
- **Summary Generation**: GPT-3.5 Turbo

## Privacy Levels

- **Public**: Discoverable, anyone can access
- **Unlisted**: Only accessible via direct link
- **Private**: Only accessible by the author

## Development

### Requirements
- Python 3.11+
- SQLite (included)
- FFmpeg (optional, for audio conversion)
- OpenAI API key (for AI features)

### Running Tests
```bash
make test
```

### Code Structure
- Follow Flask blueprint patterns
- Use service layer for business logic
- SQLite with custom models (no ORM)
- Responsive design with Bootstrap 5
- Progressive Web App features

## Deployment

### Docker Production
```bash
# Build production image
docker build -t voice-log .

# Run with production settings
docker run -d \
  --name voice-log \
  -p 5010:5010 \
  -v ./data:/app/data \
  -v ./uploads:/app/uploads \
  -e OPENAI_API_KEY=your-key \
  voice-log
```

### Environment Setup
1. Set strong `SECRET_KEY`
2. Configure `OPENAI_API_KEY` for AI features
3. Set up proper volume mounts for data persistence
4. Use reverse proxy (nginx) for production
5. Enable HTTPS for secure cookies

## Troubleshooting

### Common Issues

**Database not found**
```bash
make init-db
```

**Audio processing fails**
- Check OpenAI API key configuration
- Verify file format is supported
- Check file size (max 50MB)

**Container won't start**
```bash
make logs  # Check container logs
make status # Check container status
```

### Health Check
```bash
make health  # Check if application is responding
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source and available under the [MIT License](LICENSE).

## Support

- Create an issue for bug reports
- Check existing issues for solutions
- Review the troubleshooting section

---

**Voice Log** - Transform your voice into engaging content 🎙️✨