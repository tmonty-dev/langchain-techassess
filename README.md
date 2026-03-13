# Tech Assessment System

A human-in-the-loop system for analyzing meeting transcripts and generating comprehensive technology assessment reports with prioritized recommendations and roadmaps.

## 🎯 Overview

This system takes meeting transcripts from technology assessment interviews and uses AI to generate structured reports with:

- **Question & Answer Analysis** - Synthesizes responses to assessment questions with supporting evidence
- **Risk Identification** - Identifies operational and strategic risks with business impact
- **Recommendations** - Generates prioritized, costed recommendations with implementation timelines
- **Executive Roadmap** - Creates a Year 1 implementation roadmap with quarterly scheduling

The key differentiator is **human-in-the-loop approval** - each topic analysis pauses for expert review and revision before proceeding to final synthesis.

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Transcripts   │───▶│   LangGraph      │───▶│  Final Report   │
│   (.txt, .pdf)  │    │   Workflow       │    │  (JSON, MD)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Human Approval   │
                    │ Checkpoints      │
                    └──────────────────┘
```

### Core Components

- **🔗 chains/** - LangGraph workflow with human approval nodes
- **📥 ingestion/** - Transcript loading and preprocessing
- **📤 export/** - Report formatting and roadmap generation
- **🌐 api/** - RESTful API for web interface
- **⚙️ utils/** - Session management for long-running workflows
- **📋 schemas/** - Pydantic models for configuration and reports

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- OpenAI API key (or other LLM provider)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/langchain-techassess
   cd langchain-techassess
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Start the server**
   ```bash
   python main.py
   ```

5. **Open the API documentation**
   ```
   http://localhost:8000/docs
   ```

## 📖 Usage Guide

### Basic Workflow

1. **Prepare Your Assessment**
   - Define topics and questions in your engagement config
   - Upload meeting transcript files

2. **Start Assessment**
   ```bash
   POST /assessments/start
   {
     "config": {...},
     "transcript_files": ["meeting1.txt", "meeting2.txt"]
   }
   ```

3. **Monitor Progress**
   ```bash
   GET /assessments/{session_id}/status
   ```

4. **Review Each Topic**
   - System analyzes one topic at a time
   - Pauses for human review at each completion
   - Review via: `GET /assessments/{session_id}/review`

5. **Approve or Request Revisions**
   ```bash
   POST /assessments/{session_id}/approve
   {
     "action": "accept"  # or "revise"
     "revision_instructions": "Add more cost detail"
   }
   ```

6. **Get Final Report**
   ```bash
   GET /assessments/{session_id}/report
   ```

### Example Configuration

```python
from schemas import EngagementConfig, Topic, Question

config = EngagementConfig(
    engagement_id="assessment_2024_001",
    organization_name="Acme Corporation",
    categories=[
        Topic(
            id="infrastructure",
            name="IT Infrastructure",
            questions=[
                Question(
                    id="inf_01",
                    text="What is the current state of server infrastructure?"
                ),
                Question(
                    id="inf_02",
                    text="Are there any reliability or performance issues?"
                )
            ]
        ),
        Topic(
            id="security",
            name="Cybersecurity",
            questions=[
                Question(
                    id="sec_01",
                    text="What security measures are currently in place?"
                )
            ]
        )
    ]
)
```

## 🔄 Human-in-the-Loop Process

The system implements approval checkpoints at each topic completion:

### Topic Review Format

When a topic analysis completes, you'll see:

```
🔍 TOPIC ANALYSIS COMPLETE: IT Infrastructure
============================================================

📋 QUESTION RESPONSES:
1. What is the current state of server infrastructure?
   📝 Answer: The organization operates 15 physical servers...
   📊 Sources: 3 supporting excerpts
   💭 Preview: "We've had three disk failures this month..."

⚠️  IDENTIFIED RISKS (2):
1. Server hardware approaching end-of-life may cause unexpected downtime
   📄 Source: transcript_1.txt
   💬 Quote: "We've had three disk failures this month alone..."

💡 RECOMMENDATIONS (3):
1. Server Infrastructure Modernization (Priority: High)
   ⏰ Timeline: Y1
   💰 Cost: $75,000 - $125,000 (Hardware)
   📝 Description: Replace aging server infrastructure...

============================================================
🔄 REVIEW OPTIONS:
• Type 'accept' to approve this analysis
• Type 'revise: [instructions]' to request changes
```

### Revision Examples

The system handles natural language revision requests:

- **"revise: Add more detailed cost breakdowns for hardware recommendations"**
- **"revise: The risk analysis seems too generic, be more specific about business impact"**
- **"revise: Question 2 needs better supporting evidence from the transcripts"**
- **"revise: Include a recommendation about backup and disaster recovery"**

## 📊 API Reference

### Start Assessment

**POST** `/assessments/start`

```json
{
  "config": {
    "engagement_id": "string",
    "organization_name": "string",
    "categories": [...]
  },
  "transcript_files": ["path1.txt", "path2.pdf"]
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "message": "Assessment started...",
  "total_topics": 3,
  "organization": "Acme Corp"
}
```

### Check Status

**GET** `/assessments/{session_id}/status`

**Response:**
```json
{
  "session_id": "uuid",
  "status": "waiting_approval",
  "pending_approval": true,
  "current_topic": "IT Infrastructure",
  "completed_topics": 1,
  "total_topics": 3,
  "completion_percentage": 33.3
}
```

### Review Current Topic

**GET** `/assessments/{session_id}/review`

Returns formatted topic analysis for human review.

### Submit Approval/Revision

**POST** `/assessments/{session_id}/approve`

```json
{
  "action": "accept"
}
```

OR

```json
{
  "action": "revise",
  "revision_instructions": "Add more cost detail to recommendations"
}
```

### Get Final Report

**GET** `/assessments/{session_id}/report`

Returns the complete `AssessmentReport` with all approved topics and roadmap.

### Export Report

**GET** `/assessments/{session_id}/export/{format}`

Formats: `json`, `summary`

## 🏭 Production Deployment

### Environment Variables

```bash
# LLM Configuration
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Database
DATABASE_URL=sqlite:///assessments.db

# Security
SECRET_KEY=your_secret_key
ALLOWED_HOSTS=localhost,yourdomain.com

# Logging
LOG_LEVEL=INFO
LOG_FILE=assessment.log
```

### Docker Deployment

Create a `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "main.py"]
```

Build and run:
```bash
docker build -t tech-assessment .
docker run -p 8000:8000 tech-assessment
```

### Scaling Considerations

- **Database**: Move from SQLite to PostgreSQL for production
- **File Storage**: Use S3/GCS for transcript files
- **Caching**: Add Redis for session state
- **Queue**: Use Celery for background processing
- **Monitoring**: Add logging, metrics, and health checks

## 🔧 Development

### Project Structure

```
├── main.py                     # Application entry point
├── api/
│   └── assessment_api.py       # FastAPI routes and handlers
├── chains/
│   ├── assessment_workflow.py  # LangGraph workflow definition
│   ├── nodes.py               # Processing nodes
│   ├── routing.py             # Decision logic
│   └── topic_analyzer.py      # LLM analysis functions
├── ingestion/
│   └── transcript_processor.py # File loading and cleaning
├── export/
│   ├── report_formatter.py    # Output formatting
│   └── roadmap_generator.py   # Roadmap synthesis
├── schemas/
│   ├── config.py              # Input configuration models
│   └── report.py              # Output report models
└── utils/
    └── session_manager.py     # Session state management
```

### Adding New LLM Providers

1. **Install provider SDK**
   ```bash
   pip install langchain-google-vertexai
   ```

2. **Update topic_analyzer.py**
   ```python
   from langchain_google_vertexai import ChatVertexAI

   class TopicAnalyzer:
       def __init__(self, model_name: str = "gemini-pro"):
           self.llm = ChatVertexAI(model_name=model_name)
   ```

### Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=. tests/

# Test specific module
pytest tests/test_topic_analyzer.py -v
```

## 🐛 Troubleshooting

### Common Issues

**"Session not found" errors**
- Sessions expire after 24 hours
- Check session ID spelling
- Use `GET /assessments/active` to list sessions

**LLM API failures**
- Verify API keys in environment
- Check rate limits and quotas
- Review model availability in your region

**File processing errors**
- Ensure transcript files exist and are readable
- Check supported formats: .txt, .md, .docx, .pdf
- Verify file encoding (UTF-8 recommended)

**Memory issues with large files**
- Split large transcripts into smaller chunks
- Increase system memory allocation
- Consider streaming processing for very large datasets

### Logs and Debugging

```bash
# View application logs
tail -f assessment.log

# Enable debug logging
export LOG_LEVEL=DEBUG
python main.py

# Check LangGraph execution
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=your_langchain_key
```

### Performance Optimization

For large assessments:
- Use `haiku` model for faster processing
- Process topics in parallel when possible
- Optimize transcript preprocessing
- Use caching for repeated analyses

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/langchain-techassess
cd langchain-techassess

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install -e .
```

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For questions and support:
- 📚 **Documentation**: Check this README and code comments
- 🐛 **Issues**: Use GitHub Issues for bug reports
- 💬 **Discussions**: Use GitHub Discussions for questions
- 📧 **Contact**: Reach out to the development team

## 🙏 Acknowledgments

- Built with [LangChain](https://langchain.com/) and [LangGraph](https://langchain-ai.github.io/langgraph/)
- Powered by [FastAPI](https://fastapi.tiangolo.com/)
- Uses [Pydantic](https://pydantic.dev/) for data validation
- Inspired by human-centered AI design principles

---

**Ready to transform your technology assessments? Start your first assessment today!** 🚀