#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from app import create_app

# Load environment variables
load_dotenv()

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5010))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    app.run(host=host, port=port, debug=debug)