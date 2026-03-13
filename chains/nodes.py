"""
Node implementations for the assessment workflow
"""
import logging
from chains.assessment_workflow import AssessmentState
from ingestion.transcript_processor import TranscriptProcessor
from chains.topic_analyzer import TopicAnalyzer
from export.report_formatter import ReportFormatter

logger = logging.getLogger(__name__)


async def load_transcripts_node(state: AssessmentState) -> AssessmentState:
    """Load and validate transcript files"""
    logger.info("Loading transcript files...")

    processor = TranscriptProcessor()
    raw_transcripts = []

    try:
        for file_path in state["transcript_files"]:
            content = await processor.load_transcript_file(file_path)
            raw_transcripts.append(content)

        # Initialize approval tracking
        approval_status = {
            topic.id: "pending"
            for topic in state["config"].categories
        }

        return {
            **state,
            "raw_transcripts": raw_transcripts,
            "topic_approval_status": approval_status,
            "revision_requests": {}
        }

    except Exception as e:
        error_msg = f"Failed to load transcripts: {str(e)}"
        logger.error(error_msg)
        return {
            **state,
            "errors": state.get("errors", []) + [error_msg]
        }


async def preprocess_transcripts_node(state: AssessmentState) -> AssessmentState:
    """Clean and combine transcript content"""
    logger.info("Preprocessing transcripts...")

    processor = TranscriptProcessor()

    try:
        processed = await processor.preprocess_transcripts(state["raw_transcripts"])

        return {
            **state,
            "processed_transcripts": processed
        }

    except Exception as e:
        error_msg = f"Failed to preprocess transcripts: {str(e)}"
        logger.error(error_msg)
        return {
            **state,
            "errors": state.get("errors", []) + [error_msg]
        }


async def select_next_topic_node(state: AssessmentState) -> AssessmentState:
    """Select the next topic that needs processing"""

    # Priority 1: Topics needing revision
    for topic_id, status in state["topic_approval_status"].items():
        if status == "needs_revision":
            logger.info(f"Selected topic for revision: {topic_id}")
            return {**state, "current_topic_id": topic_id}

    # Priority 2: Unprocessed topics
    processed_topic_ids = {tr.Topic_id for tr in state["topic_reports"]}
    for topic in state["config"].categories:
        if topic.id not in processed_topic_ids:
            logger.info(f"Selected topic for analysis: {topic.id}")
            return {**state, "current_topic_id": topic.id}

    # All topics processed
    logger.info("All topics processed, ready for synthesis")
    return {**state, "current_topic_id": None}


async def analyze_topic_node(state: AssessmentState) -> AssessmentState:
    """Analyze a single topic with optional revision context"""

    topic_id = state["current_topic_id"]
    topic = next(t for t in state["config"].categories if t.id == topic_id)

    logger.info(f"Analyzing topic: {topic.name}")

    # Get revision context if applicable
    revision_context = state["revision_requests"].get(topic_id, "")

    # Remove existing report for this topic (for revisions)
    topic_reports = [tr for tr in state["topic_reports"] if tr.Topic_id != topic_id]

    try:
        analyzer = TopicAnalyzer()
        topic_report = await analyzer.analyze_topic(
            topic=topic,
            transcripts=state["processed_transcripts"],
            revision_instructions=revision_context
        )

        # Add the new/revised report
        topic_reports.append(topic_report)

        return {
            **state,
            "topic_reports": topic_reports
        }

    except Exception as e:
        error_msg = f"Failed to analyze topic {topic.name}: {str(e)}"
        logger.error(error_msg)
        return {
            **state,
            "errors": state.get("errors", []) + [error_msg]
        }


async def present_for_approval_node(state: AssessmentState) -> AssessmentState:
    """Present completed topic analysis for human review"""

    topic_id = state["current_topic_id"]
    topic_report = next(tr for tr in state["topic_reports"] if tr.Topic_id == topic_id)

    formatter = ReportFormatter()
    review_text = formatter.format_topic_for_review(topic_report)

    # This output will be captured by the API layer
    logger.info(f"Topic analysis ready for review: {topic_report.Topic_name}")

    # The graph will pause here for human input
    return state


async def handle_revision_node(state: AssessmentState) -> AssessmentState:
    """Log revision request and prepare for re-analysis"""

    topic_id = state["current_topic_id"]
    revision_request = state["revision_requests"].get(topic_id, "")

    logger.info(f"Processing revision for topic {topic_id}: {revision_request}")

    return state


async def generate_roadmap_node(state: AssessmentState) -> AssessmentState:
    """Generate prioritized roadmap from approved topics"""

    logger.info("Generating final roadmap...")

    try:
        from export.roadmap_generator import RoadmapGenerator

        generator = RoadmapGenerator()
        roadmap_items = await generator.create_roadmap(
            topic_reports=state["topic_reports"],
            config=state["config"]
        )

        return {
            **state,
            "year_one_roadmap": roadmap_items
        }

    except Exception as e:
        error_msg = f"Failed to generate roadmap: {str(e)}"
        logger.error(error_msg)
        return {
            **state,
            "errors": state.get("errors", []) + [error_msg]
        }


async def finalize_report_node(state: AssessmentState) -> AssessmentState:
    """Assemble the final assessment report"""

    logger.info("Finalizing assessment report...")

    try:
        final_report = AssessmentReport(
            engagement_id=state["config"].engagement_id,
            organization_name=state["config"].organization_name,
            year_one_roadmap=state["year_one_roadmap"],
            categories=state["topic_reports"]
        )

        logger.info(f"Assessment completed for {state['config'].organization_name}")

        return {
            **state,
            "final_report": final_report
        }

    except Exception as e:
        error_msg = f"Failed to finalize report: {str(e)}"
        logger.error(error_msg)
        return {
            **state,
            "errors": state.get("errors", []) + [error_msg]
        }