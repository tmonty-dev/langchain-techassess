"""
Session management for human-in-the-loop workflows
"""
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from dataclasses import dataclass, field

from schemas.config import EngagementConfig
from schemas.report import TopicReport, AssessmentReport

logger = logging.getLogger(__name__)


@dataclass
class SessionInfo:
    """Information about an active assessment session"""
    session_id: str
    config: EngagementConfig
    status: str = "running"  # running, waiting_approval, completed, error
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    # Current state
    current_topic_id: Optional[str] = None
    current_topic_report: Optional[TopicReport] = None
    pending_approval: bool = False

    # Progress tracking
    completed_topics: list[str] = field(default_factory=list)
    total_topics: int = 0
    errors: list[str] = field(default_factory=list)

    # Final results
    final_report: Optional[AssessmentReport] = None


class SessionManager:
    """Manages active assessment sessions"""

    def __init__(self):
        self.active_sessions: Dict[str, SessionInfo] = {}
        self.session_timeout_hours = 24  # Sessions expire after 24 hours

    def create_session(self, config: EngagementConfig) -> str:
        """Create a new assessment session"""

        session_id = str(uuid.uuid4())

        session_info = SessionInfo(
            session_id=session_id,
            config=config,
            total_topics=len(config.categories)
        )

        self.active_sessions[session_id] = session_info

        logger.info(f"Created new session: {session_id} for {config.organization_name}")

        return session_id

    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """Get session information"""

        if session_id not in self.active_sessions:
            return None

        session = self.active_sessions[session_id]

        # Check if session has expired
        if self._is_session_expired(session):
            logger.warning(f"Session {session_id} has expired")
            self.cleanup_session(session_id)
            return None

        return session

    def update_session_status(
        self,
        session_id: str,
        status: str,
        **kwargs
    ) -> bool:
        """Update session status and optional fields"""

        session = self.get_session(session_id)
        if not session:
            return False

        session.status = status
        session.last_updated = datetime.now()

        # Update optional fields
        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)

        logger.info(f"Updated session {session_id} status to: {status}")

        return True

    def set_pending_approval(
        self,
        session_id: str,
        topic_report: TopicReport
    ) -> bool:
        """Mark session as waiting for topic approval"""

        session = self.get_session(session_id)
        if not session:
            return False

        session.status = "waiting_approval"
        session.pending_approval = True
        session.current_topic_id = topic_report.Topic_id
        session.current_topic_report = topic_report
        session.last_updated = datetime.now()

        logger.info(f"Session {session_id} waiting for approval of topic: {topic_report.Topic_name}")

        return True

    def approve_topic(self, session_id: str) -> bool:
        """Approve current topic and mark as completed"""

        session = self.get_session(session_id)
        if not session or not session.pending_approval:
            return False

        # Mark topic as completed
        if session.current_topic_report:
            topic_name = session.current_topic_report.Topic_name
            session.completed_topics.append(topic_name)

        # Clear approval state
        session.pending_approval = False
        session.current_topic_id = None
        session.current_topic_report = None
        session.status = "running"
        session.last_updated = datetime.now()

        logger.info(f"Session {session_id} approved topic, progress: {len(session.completed_topics)}/{session.total_topics}")

        return True

    def request_revision(self, session_id: str, revision_instructions: str) -> bool:
        """Request revision for current topic"""

        session = self.get_session(session_id)
        if not session or not session.pending_approval:
            return False

        session.pending_approval = False
        session.status = "running"
        session.last_updated = datetime.now()

        logger.info(f"Session {session_id} requested revision: {revision_instructions[:50]}...")

        return True

    def complete_session(self, session_id: str, final_report: AssessmentReport) -> bool:
        """Mark session as completed with final report"""

        session = self.get_session(session_id)
        if not session:
            return False

        session.status = "completed"
        session.pending_approval = False
        session.final_report = final_report
        session.last_updated = datetime.now()

        logger.info(f"Session {session_id} completed successfully")

        return True

    def add_session_error(self, session_id: str, error: str) -> bool:
        """Add error to session"""

        session = self.get_session(session_id)
        if not session:
            return False

        session.errors.append(error)
        session.status = "error"
        session.last_updated = datetime.now()

        logger.error(f"Session {session_id} error: {error}")

        return True

    def get_session_progress(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed progress information"""

        session = self.get_session(session_id)
        if not session:
            return None

        completion_percentage = (
            len(session.completed_topics) / session.total_topics * 100
            if session.total_topics > 0 else 0
        )

        return {
            "session_id": session_id,
            "status": session.status,
            "pending_approval": session.pending_approval,
            "current_topic": session.current_topic_report.Topic_name if session.current_topic_report else None,
            "completed_topics": len(session.completed_topics),
            "total_topics": session.total_topics,
            "completion_percentage": completion_percentage,
            "errors": len(session.errors),
            "created_at": session.created_at.isoformat(),
            "last_updated": session.last_updated.isoformat()
        }

    def list_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """List all active sessions with summary info"""

        active = {}

        for session_id, session in self.active_sessions.items():
            if not self._is_session_expired(session):
                active[session_id] = {
                    "organization": session.config.organization_name,
                    "status": session.status,
                    "progress": f"{len(session.completed_topics)}/{session.total_topics}",
                    "created": session.created_at.isoformat(),
                    "last_updated": session.last_updated.isoformat()
                }

        return active

    def cleanup_session(self, session_id: str) -> bool:
        """Remove session from active sessions"""

        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.info(f"Cleaned up session: {session_id}")
            return True

        return False

    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions and return count cleaned up"""

        expired_sessions = []

        for session_id, session in self.active_sessions.items():
            if self._is_session_expired(session):
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            self.cleanup_session(session_id)

        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

        return len(expired_sessions)

    def _is_session_expired(self, session: SessionInfo) -> bool:
        """Check if session has expired"""

        expiry_time = session.last_updated + timedelta(hours=self.session_timeout_hours)
        return datetime.now() > expiry_time


# Global session manager instance
session_manager = SessionManager()