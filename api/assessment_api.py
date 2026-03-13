"""
Clean API endpoints for the assessment system
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
import logging

from schemas.config import EngagementConfig
from schemas.report import AssessmentReport
from utils.session_manager import session_manager
from chains.assessment_workflow import compile_assessment_graph, AssessmentState
from export.report_formatter import ReportFormatter

logger = logging.getLogger(__name__)

# Initialize the assessment graph
assessment_graph = compile_assessment_graph()
report_formatter = ReportFormatter()


class AssessmentAPI:
    """Main API class for assessment operations"""

    def __init__(self, app: FastAPI):
        self.app = app
        self.setup_routes()

    def setup_routes(self):
        """Setup API routes"""

        @self.app.post("/assessments/start", response_model=dict)
        async def start_assessment(
            request: dict,
            background_tasks: BackgroundTasks
        ):
            """Start a new assessment with human-in-the-loop approval"""

            try:
                config = EngagementConfig(**request["config"])
                transcript_files = request["transcript_files"]

                # Create session
                session_id = session_manager.create_session(config)

                # Start processing in background
                background_tasks.add_task(
                    self._run_assessment_workflow,
                    session_id,
                    config,
                    transcript_files
                )

                return {
                    "session_id": session_id,
                    "message": "Assessment started. You'll be notified when topics are ready for review.",
                    "total_topics": len(config.categories),
                    "organization": config.organization_name
                }

            except Exception as e:
                logger.error(f"Failed to start assessment: {str(e)}")
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get("/assessments/{session_id}/status")
        async def get_assessment_status(session_id: str):
            """Get current status of an assessment"""

            progress = session_manager.get_session_progress(session_id)
            if not progress:
                raise HTTPException(status_code=404, detail="Session not found")

            return progress

        @self.app.get("/assessments/{session_id}/review")
        async def get_current_review(session_id: str):
            """Get the current topic awaiting review"""

            session = session_manager.get_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")

            if not session.pending_approval or not session.current_topic_report:
                raise HTTPException(status_code=400, detail="No topic pending approval")

            # Format for review
            formatted_review = report_formatter.format_topic_for_web_review(
                session.current_topic_report
            )

            return {
                "session_id": session_id,
                "topic_analysis": formatted_review,
                "review_text": report_formatter.format_topic_for_review(
                    session.current_topic_report
                ),
                "instructions": {
                    "approve": f"POST /assessments/{session_id}/approve with action: 'accept'",
                    "revise": f"POST /assessments/{session_id}/approve with action: 'revise' and revision_instructions"
                }
            }

        @self.app.post("/assessments/{session_id}/approve")
        async def handle_topic_approval(
            session_id: str,
            request: dict,
            background_tasks: BackgroundTasks
        ):
            """Handle topic approval or revision request"""

            session = session_manager.get_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")

            if not session.pending_approval:
                raise HTTPException(status_code=400, detail="No approval pending")

            action = request.get("action")

            if action == "accept":
                # Approve and continue
                success = session_manager.approve_topic(session_id)
                if not success:
                    raise HTTPException(status_code=500, detail="Failed to approve topic")

                # Resume workflow
                background_tasks.add_task(
                    self._resume_workflow_with_input,
                    session_id,
                    "accept"
                )

                return {
                    "status": "approved",
                    "message": f"Topic '{session.current_topic_report.Topic_name}' approved",
                    "progress": f"{len(session.completed_topics) + 1}/{session.total_topics}"
                }

            elif action == "revise":
                revision_instructions = request.get("revision_instructions", "")
                if not revision_instructions:
                    raise HTTPException(
                        status_code=400,
                        detail="revision_instructions required for revise action"
                    )

                # Request revision
                success = session_manager.request_revision(session_id, revision_instructions)
                if not success:
                    raise HTTPException(status_code=500, detail="Failed to request revision")

                # Resume workflow with revision instructions
                background_tasks.add_task(
                    self._resume_workflow_with_input,
                    session_id,
                    f"revise: {revision_instructions}"
                )

                return {
                    "status": "revision_requested",
                    "message": f"Revision requested for '{session.current_topic_report.Topic_name}'",
                    "revision_instructions": revision_instructions
                }

            else:
                raise HTTPException(
                    status_code=400,
                    detail="Action must be 'accept' or 'revise'"
                )

        @self.app.get("/assessments/{session_id}/report", response_model=AssessmentReport)
        async def get_final_report(session_id: str):
            """Get the completed assessment report"""

            session = session_manager.get_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")

            if session.status != "completed" or not session.final_report:
                raise HTTPException(status_code=400, detail="Assessment not yet completed")

            return session.final_report

        @self.app.get("/assessments/{session_id}/export/{format_type}")
        async def export_report(session_id: str, format_type: str):
            """Export report in various formats"""

            session = session_manager.get_session(session_id)
            if not session or not session.final_report:
                raise HTTPException(status_code=404, detail="Report not found")

            if format_type == "json":
                content = report_formatter.export_final_report_json(session.final_report)
                return JSONResponse(
                    content=content,
                    headers={"Content-Disposition": f"attachment; filename=assessment_{session_id}.json"}
                )

            elif format_type == "summary":
                content = report_formatter.export_executive_summary(session.final_report)
                return JSONResponse(
                    content={"summary": content},
                    headers={"Content-Disposition": f"attachment; filename=summary_{session_id}.md"}
                )

            else:
                raise HTTPException(status_code=400, detail="Supported formats: json, summary")

        @self.app.get("/assessments/active")
        async def list_active_assessments():
            """List all active assessment sessions"""

            return {
                "active_sessions": session_manager.list_active_sessions(),
                "cleanup_count": session_manager.cleanup_expired_sessions()
            }

        @self.app.delete("/assessments/{session_id}")
        async def cleanup_assessment(session_id: str):
            """Clean up a completed or abandoned assessment"""

            success = session_manager.cleanup_session(session_id)
            if not success:
                raise HTTPException(status_code=404, detail="Session not found")

            return {"message": f"Session {session_id} cleaned up"}

    async def _run_assessment_workflow(
        self,
        session_id: str,
        config: EngagementConfig,
        transcript_files: List[str]
    ):
        """Run the assessment workflow until first approval checkpoint"""

        try:
            # Initialize state
            initial_state = AssessmentState(
                config=config,
                transcript_files=transcript_files,
                raw_transcripts=[],
                processed_transcripts="",
                current_topic_id=None,
                topic_reports=[],
                topic_approval_status={},
                revision_requests={},
                year_one_roadmap=None,
                final_report=None,
                errors=[]
            )

            thread_config = {"configurable": {"thread_id": session_id}}

            # Run until interrupt (topic ready for approval)
            async for event in assessment_graph.astream(
                initial_state,
                config=thread_config
            ):
                # Check for approval checkpoint
                if self._is_approval_checkpoint(event):
                    # Extract topic report and set up for approval
                    await self._handle_approval_checkpoint(session_id, event)
                    break

                # Check for completion
                elif self._is_workflow_complete(event):
                    await self._handle_workflow_completion(session_id, event)
                    break

        except Exception as e:
            error_msg = f"Assessment workflow failed: {str(e)}"
            logger.error(error_msg)
            session_manager.add_session_error(session_id, error_msg)

    async def _resume_workflow_with_input(self, session_id: str, human_input: str):
        """Resume workflow with human input"""

        try:
            thread_config = {"configurable": {"thread_id": session_id}}

            # Resume with human input
            async for event in assessment_graph.astream(
                {"human_input": human_input},
                config=thread_config
            ):
                # Check for next approval or completion
                if self._is_approval_checkpoint(event):
                    await self._handle_approval_checkpoint(session_id, event)
                    break
                elif self._is_workflow_complete(event):
                    await self._handle_workflow_completion(session_id, event)
                    break

        except Exception as e:
            error_msg = f"Workflow resume failed: {str(e)}"
            logger.error(error_msg)
            session_manager.add_session_error(session_id, error_msg)

    def _is_approval_checkpoint(self, event: Dict[str, Any]) -> bool:
        """Check if event indicates approval checkpoint"""
        return "present_for_approval" in event

    def _is_workflow_complete(self, event: Dict[str, Any]) -> bool:
        """Check if workflow is complete"""
        return "final_report" in event and event.get("final_report") is not None

    async def _handle_approval_checkpoint(self, session_id: str, event: Dict[str, Any]):
        """Handle when a topic is ready for approval"""

        state = event.get("present_for_approval", {})
        current_topic_id = state.get("current_topic_id")
        topic_reports = state.get("topic_reports", [])

        # Find current topic report
        current_report = next(
            (tr for tr in topic_reports if tr.Topic_id == current_topic_id),
            None
        )

        if current_report:
            session_manager.set_pending_approval(session_id, current_report)
            logger.info(f"Session {session_id}: Topic '{current_report.Topic_name}' ready for review")

    async def _handle_workflow_completion(self, session_id: str, event: Dict[str, Any]):
        """Handle workflow completion"""

        final_report = event.get("final_report")
        if final_report:
            session_manager.complete_session(session_id, final_report)
            logger.info(f"Assessment completed for session {session_id}")


def create_assessment_app() -> FastAPI:
    """Create and configure the FastAPI application"""

    app = FastAPI(
        title="Tech Assessment API",
        description="Human-in-the-loop technology assessment system",
        version="1.0.0"
    )

    # Initialize API
    AssessmentAPI(app)

    return app