"""
Routing logic for the assessment workflow
"""
import logging
from chains.assessment_workflow import AssessmentState

logger = logging.getLogger(__name__)


def route_topic_selection(state: AssessmentState) -> str:
    """Route based on topic processing status"""

    if state["current_topic_id"]:
        return "analyze"

    # Check if all topics are approved
    all_approved = all(
        status == "approved"
        for status in state["topic_approval_status"].values()
    )

    return "synthesize" if all_approved else "analyze"


def route_human_decision(state: AssessmentState) -> str:
    """Process human input and determine next action"""

    # This function will be called with human input from the API layer
    # For now, it's a placeholder that returns "waiting" to pause the graph

    topic_id = state["current_topic_id"]

    # Check if we have human input stored in state (from API)
    if "human_input" in state:
        human_input = state["human_input"].lower().strip()

        if human_input == "accept":
            # Mark as approved
            state["topic_approval_status"][topic_id] = "approved"
            logger.info(f"Topic {topic_id} approved")
            return "approved"

        elif human_input.startswith("revise:"):
            # Extract revision instructions
            revision_instructions = state["human_input"][7:].strip()
            state["revision_requests"][topic_id] = revision_instructions
            state["topic_approval_status"][topic_id] = "needs_revision"
            logger.info(f"Revision requested for topic {topic_id}")
            return "needs_revision"

    # Default: waiting for human input
    return "waiting"


def get_next_unprocessed_topic(state: AssessmentState):
    """Helper to find next topic needing processing"""

    # Check for revision requests first
    for topic_id, status in state["topic_approval_status"].items():
        if status == "needs_revision":
            return topic_id

    # Then check for unprocessed topics
    processed_ids = {tr.Topic_id for tr in state["topic_reports"]}
    for topic in state["config"].categories:
        if topic.id not in processed_ids:
            return topic.id

    return None


def is_assessment_complete(state: AssessmentState) -> bool:
    """Check if all topics are approved and ready for synthesis"""

    return all(
        status == "approved"
        for status in state["topic_approval_status"].values()
    )


def get_completion_progress(state: AssessmentState) -> dict:
    """Get progress statistics for the assessment"""

    total_topics = len(state["config"].categories)
    approved_topics = sum(
        1 for status in state["topic_approval_status"].values()
        if status == "approved"
    )
    pending_topics = sum(
        1 for status in state["topic_approval_status"].values()
        if status == "pending"
    )
    revision_topics = sum(
        1 for status in state["topic_approval_status"].values()
        if status == "needs_revision"
    )

    return {
        "total_topics": total_topics,
        "approved": approved_topics,
        "pending": pending_topics,
        "needs_revision": revision_topics,
        "completion_percentage": (approved_topics / total_topics) * 100
    }