"""
Basic functionality tests for the Tech Assessment System
"""

import pytest
from pathlib import Path
import tempfile
import asyncio

from schemas.config import EngagementConfig, Topic, Question
from schemas.report import TopicReport, QuestionResponse, Risk, Recommendation
from ingestion.transcript_processor import TranscriptProcessor
from export.report_formatter import ReportFormatter
from utils.session_manager import SessionManager


class TestSchemas:
    """Test that our schemas work correctly"""

    def test_engagement_config_creation(self):
        """Test creating an engagement configuration"""

        question = Question(id="test_01", text="Test question?")
        topic = Topic(id="test_topic", name="Test Topic", questions=[question])

        config = EngagementConfig(
            engagement_id="test_001",
            organization_name="Test Org",
            categories=[topic]
        )

        assert config.engagement_id == "test_001"
        assert config.organization_name == "Test Org"
        assert len(config.categories) == 1
        assert config.categories[0].name == "Test Topic"

    def test_topic_report_creation(self):
        """Test creating a topic report"""

        qr = QuestionResponse(
            question_id="q1",
            question_text="Test question?",
            answer="Test answer",
            source_chunks=["Test chunk"]
        )

        risk = Risk(
            description="Test risk",
            supporting_quote="Test quote",
            source_document="test.txt"
        )

        rec = Recommendation(
            title="Test Recommendation",
            description="Test description",
            timeline="Y1",
            priority="High",
            cost_estimate="$10,000",
            cost_type="Labor",
            next_steps=["Step 1"],
            benefits=["Benefit 1"],
            addresses_risks=["Test risk"]
        )

        report = TopicReport(
            Topic_id="test_topic",
            Topic_name="Test Topic",
            question_responses=[qr],
            risks=[risk],
            recommendations=[rec]
        )

        assert report.Topic_name == "Test Topic"
        assert len(report.question_responses) == 1
        assert len(report.risks) == 1
        assert len(report.recommendations) == 1


class TestTranscriptProcessor:
    """Test transcript processing functionality"""

    @pytest.mark.asyncio
    async def test_load_text_file(self):
        """Test loading a text file"""

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test transcript content\nSpeaker 1: Hello\nSpeaker 2: Hi there")
            temp_path = f.name

        try:
            processor = TranscriptProcessor()
            content = await processor.load_transcript_file(temp_path)

            assert "Test transcript content" in content
            assert "Speaker 1: Hello" in content

        finally:
            Path(temp_path).unlink()

    @pytest.mark.asyncio
    async def test_preprocess_transcripts(self):
        """Test transcript preprocessing"""

        processor = TranscriptProcessor()
        raw_transcripts = [
            "This is transcript 1\nSpeaker A: Content here",
            "This is transcript 2\nSpeaker B: More content"
        ]

        processed = await processor.preprocess_transcripts(raw_transcripts)

        assert "TRANSCRIPT 1" in processed
        assert "TRANSCRIPT 2" in processed
        assert "Speaker A:" in processed
        assert "Speaker B:" in processed

    def test_extract_speakers(self):
        """Test speaker extraction"""

        processor = TranscriptProcessor()
        content = "John: Hello there\nJane: Hi John\nSpeaker 1: General comment"

        speakers = processor.extract_speakers(content)

        assert "John" in speakers
        assert "Jane" in speakers
        assert "Speaker 1" in speakers

    def test_get_transcript_stats(self):
        """Test transcript statistics"""

        processor = TranscriptProcessor()
        content = "John: This is a test transcript.\nJane: Yes it is.\nJohn: Great!"

        stats = processor.get_transcript_stats(content)

        assert stats["total_words"] > 0
        assert stats["total_lines"] > 0
        assert stats["unique_speakers"] == 2
        assert "John" in stats["speaker_names"]
        assert "Jane" in stats["speaker_names"]


class TestReportFormatter:
    """Test report formatting functionality"""

    def test_format_topic_for_review(self):
        """Test formatting a topic for human review"""

        # Create sample topic report
        qr = QuestionResponse(
            question_id="q1",
            question_text="What is the current infrastructure?",
            answer="The infrastructure consists of 10 servers...",
            source_chunks=["Quote from meeting: 'We have 10 servers'"]
        )

        risk = Risk(
            description="Server hardware is aging and may fail",
            supporting_quote="We've had 3 disk failures this month",
            source_document="meeting_1.txt"
        )

        rec = Recommendation(
            title="Upgrade Server Infrastructure",
            description="Replace aging servers with modern hardware",
            timeline="Y1",
            priority="High",
            cost_estimate="$50,000 - $75,000",
            cost_type="Hardware",
            next_steps=["Get quotes", "Plan migration"],
            benefits=["Improved reliability", "Better performance"],
            addresses_risks=["Server hardware is aging"]
        )

        topic_report = TopicReport(
            Topic_id="infrastructure",
            Topic_name="IT Infrastructure",
            question_responses=[qr],
            risks=[risk],
            recommendations=[rec]
        )

        formatter = ReportFormatter()
        review_text = formatter.format_topic_for_review(topic_report)

        # Check that all sections are present
        assert "IT Infrastructure" in review_text
        assert "QUESTION RESPONSES" in review_text
        assert "IDENTIFIED RISKS" in review_text
        assert "RECOMMENDATIONS" in review_text
        assert "REVIEW OPTIONS" in review_text

    def test_format_topic_for_web_review(self):
        """Test formatting topic for web UI"""

        qr = QuestionResponse(
            question_id="q1",
            question_text="Test question?",
            answer="Test answer",
            source_chunks=["Test chunk"]
        )

        topic_report = TopicReport(
            Topic_id="test",
            Topic_name="Test Topic",
            question_responses=[qr],
            risks=[],
            recommendations=[]
        )

        formatter = ReportFormatter()
        web_format = formatter.format_topic_for_web_review(topic_report)

        assert web_format["topic_name"] == "Test Topic"
        assert web_format["summary"]["questions_answered"] == 1
        assert len(web_format["sections"]["questions"]) == 1


class TestSessionManager:
    """Test session management functionality"""

    def test_create_session(self):
        """Test creating a new session"""

        manager = SessionManager()

        question = Question(id="q1", text="Test?")
        topic = Topic(id="t1", name="Test", questions=[question])
        config = EngagementConfig(
            engagement_id="test_001",
            organization_name="Test Org",
            categories=[topic]
        )

        session_id = manager.create_session(config)

        assert session_id is not None
        assert len(session_id) > 0

        # Check session exists
        session = manager.get_session(session_id)
        assert session is not None
        assert session.config.organization_name == "Test Org"

    def test_session_progress_tracking(self):
        """Test session progress tracking"""

        manager = SessionManager()

        question = Question(id="q1", text="Test?")
        topic = Topic(id="t1", name="Test", questions=[question])
        config = EngagementConfig(
            engagement_id="test_001",
            organization_name="Test Org",
            categories=[topic]
        )

        session_id = manager.create_session(config)

        # Get progress
        progress = manager.get_session_progress(session_id)

        assert progress["total_topics"] == 1
        assert progress["completed_topics"] == 0
        assert progress["status"] == "running"

    def test_session_cleanup(self):
        """Test session cleanup"""

        manager = SessionManager()

        question = Question(id="q1", text="Test?")
        topic = Topic(id="t1", name="Test", questions=[question])
        config = EngagementConfig(
            engagement_id="test_001",
            organization_name="Test Org",
            categories=[topic]
        )

        session_id = manager.create_session(config)

        # Verify session exists
        assert manager.get_session(session_id) is not None

        # Clean up session
        success = manager.cleanup_session(session_id)
        assert success is True

        # Verify session is gone
        assert manager.get_session(session_id) is None


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])