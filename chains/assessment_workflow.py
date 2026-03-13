"""
LangGraph workflow for tech assessment with human-in-the-loop approval
"""
from typing import TypedDict, Annotated, Literal
from operator import add
from langraph.graph import StateGraph, END
from langraph.checkpoint.sqlite import SqliteSaver

from schemas.config import EngagementConfig, Topic
from schemas.report import AssessmentReport, TopicReport


class AssessmentState(TypedDict):
    """State model for the assessment workflow"""
    # Input data
    config: EngagementConfig
    transcript_files: list[str]
    raw_transcripts: list[str]

    # Processing state
    processed_transcripts: str
    current_topic_id: str | None

    # Topic approval tracking
    topic_reports: Annotated[list[TopicReport], add]
    topic_approval_status: dict[str, Literal["pending", "approved", "needs_revision"]]
    revision_requests: dict[str, str]  # topic_id -> revision instructions

    # Final outputs
    year_one_roadmap: list | None
    final_report: AssessmentReport | None
    errors: Annotated[list[str], add]


def create_assessment_graph():
    """Create the LangGraph workflow with human approval checkpoints"""

    workflow = StateGraph(AssessmentState)

    # Import node functions
    from chains.nodes import (
        load_transcripts_node,
        preprocess_transcripts_node,
        select_next_topic_node,
        analyze_topic_node,
        present_for_approval_node,
        handle_revision_node,
        generate_roadmap_node,
        finalize_report_node
    )

    from chains.routing import (
        route_topic_selection,
        route_human_decision
    )

    # Add nodes
    workflow.add_node("load_transcripts", load_transcripts_node)
    workflow.add_node("preprocess_text", preprocess_transcripts_node)
    workflow.add_node("select_next_topic", select_next_topic_node)
    workflow.add_node("analyze_topic", analyze_topic_node)
    workflow.add_node("present_for_approval", present_for_approval_node)
    workflow.add_node("handle_revision", handle_revision_node)
    workflow.add_node("generate_roadmap", generate_roadmap_node)
    workflow.add_node("finalize_report", finalize_report_node)

    # Define flow
    workflow.set_entry_point("load_transcripts")
    workflow.add_edge("load_transcripts", "preprocess_text")
    workflow.add_edge("preprocess_text", "select_next_topic")

    # Topic processing loop
    workflow.add_conditional_edges(
        "select_next_topic",
        route_topic_selection,
        {
            "analyze": "analyze_topic",
            "synthesize": "generate_roadmap"
        }
    )

    workflow.add_edge("analyze_topic", "present_for_approval")

    # Human approval routing
    workflow.add_conditional_edges(
        "present_for_approval",
        route_human_decision,
        {
            "approved": "select_next_topic",
            "needs_revision": "handle_revision",
            "waiting": "present_for_approval"
        }
    )

    workflow.add_edge("handle_revision", "analyze_topic")

    # Final synthesis
    workflow.add_edge("generate_roadmap", "finalize_report")
    workflow.add_edge("finalize_report", END)

    return workflow


def compile_assessment_graph(checkpoint_path: str = "checkpoints.db"):
    """Compile the graph with persistence"""

    checkpointer = SqliteSaver.from_conn_string(checkpoint_path)
    graph = create_assessment_graph()

    return graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["present_for_approval"]  # Human approval checkpoints
    )