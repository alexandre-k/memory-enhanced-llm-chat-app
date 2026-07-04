# Memory-Enhanced LLM Chat Application

A Python-based chat application that integrates long-term memory capabilities with large language models (LLMs). This system allows for contextual conversations by extracting, storing, and recalling user-specific memories to enhance LLM responses.

## Features

- **Memory Extraction**: Automatically extracts memorable facts from conversations and classifies them into categories (preferences, personal facts, settings, goals, relationships, events)
- **Semantic Search**: Uses sentence transformers for embedding-based memory retrieval
- **Streaming Responses**: Real-time response streaming with visual feedback
- **Conflict Resolution**: Automatically manages conflicting memories by favoring newer information
- **Supabase Integration**: Persistent storage of memories using vector databases

## Architecture

### Client (`src/client/`)
- Interactive CLI interface for chatting with the LLM
- Configurable via environment variables or command-line arguments
- Rich text output with markdown rendering
- Streaming response support with spinner feedback

### Server (`src/server/`)
- FastAPI-based backend with memory-enhanced chat endpoints
- Memory extraction and storage pipeline
- Supabase vector database integration
- Asynchronous processing for non-blocking operations

## Setup

### Prerequisites
- Python 3.10+
- Supabase account and project
- Hugging Face access for embedding models

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd qwen-hackathon

# Install dependencies
pip install -e .

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

### Environment Variables
```bash
# LLM Configuration
LLM_API_KEY=your_api_key
LLM_MODEL=qwen-plus
LLM_TEMPERATURE=0.7
LLM_TIMEOUT_S=60

# Memory Configuration
MEMORY_GENERATOR_MODEL=your_embedding_model

# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

### Running the Application

#### Server
```bash
# Start the server
python -m src.server
```

#### Client
```bash
# Start the CLI client
python -m src.client

# Or with custom parameters
python -m src.client --url http://localhost:8000/v1/api --model gpt-4o-mini
```

## Usage

### Client Commands
- Type any message to chat with the LLM
- `/quit` or `/exit` to exit the application
- Ctrl+C to interrupt a response
- Ctrl+D to exit

### Memory Categories
The system automatically categorizes memories into:
- **Setting**: User preferences and configurations
- **Preference**: Explicit and implicit user preferences
- **Personal Fact**: Personal information about the user
- **Goal**: User objectives and intentions
- **Relationship**: Information about relationships
- **Event**: Specific events and experiences

## API Endpoints

### Health Check
```
GET /v1/api/health
```

### Chat Endpoint
```
POST /v1/api/chat
Content-Type: application/json

{
  "content": "Your message here",
  "user_id": "unique_user_identifier"
}
```

## Development

### Project Structure
```
.
├── src/
│   ├── client/          # CLI client implementation
│   └── server/          # FastAPI server implementation
├── models/              # Downloaded embedding models
├── tests/               # Unit tests
└── templates/           # HTML templates (if needed)
```

### Testing
```bash
# Run unit tests
python -m pytest tests/
```

## Configuration

### Client Configuration
The client can be configured via:
- Command-line arguments
- Environment variables
- Default values

Key configurable parameters include:
- API endpoint URL
- API key
- Model name
- System prompt
- Temperature setting
- Request timeout

### Memory Configuration
Memory behavior can be adjusted through:
- Confidence thresholds for memory extraction
- Similarity thresholds for memory recall
- Category-specific handling rules

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Uses Qwen models for language processing
- Sentence Transformers for embedding generation
- Supabase for vector database storage
- Rich library for enhanced CLI interface
