"""
Tech Assessment System - Main Entry Point

A human-in-the-loop system for analyzing meeting transcripts and generating
technology assessment reports with recommendations and roadmaps.
"""

import logging
import uvicorn
from pathlib import Path
from api.assessment_api import create_assessment_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('assessment.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def setup_environment():
    """Setup required directories and configuration"""

    # Create necessary directories
    directories = [
        "data/transcripts",
        "data/reports",
        "data/checkpoints",
        "logs"
    ]

    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

    logger.info("Environment setup complete")


def main():
    """Main entry point for the application"""

    logger.info("Starting Tech Assessment System")

    # Setup environment
    setup_environment()

    # Create FastAPI application
    app = create_assessment_app()

    # Add startup message
    @app.on_event("startup")
    async def startup_event():
        logger.info("🚀 Tech Assessment System is ready!")
        logger.info("📋 API Documentation: http://localhost:8000/docs")
        logger.info("🔍 Health Check: http://localhost:8000/assessments/active")

    # Add shutdown cleanup
    @app.on_event("shutdown")
    async def shutdown_event():
        from utils.session_manager import session_manager
        cleanup_count = session_manager.cleanup_expired_sessions()
        logger.info(f"🧹 Cleaned up {cleanup_count} expired sessions on shutdown")

    return app


# Create app instance for deployment
app = main()


if __name__ == "__main__":
    """Run the server directly"""

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )