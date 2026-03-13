"""
Usage example for the Tech Assessment System

This demonstrates the complete workflow from starting an assessment
to receiving the final report with human approval at each step.
"""

import asyncio
import json
from schemas.config import EngagementConfig, Topic, Question


def create_sample_engagement() -> EngagementConfig:
    """Create a sample engagement configuration"""

    # Define questions for each topic area
    infrastructure_questions = [
        Question(id="inf_01", text="What is the current state of network infrastructure?"),
        Question(id="inf_02", text="Are there any performance or reliability issues?"),
        Question(id="inf_03", text="What is the age and condition of hardware?")
    ]

    security_questions = [
        Question(id="sec_01", text="What cybersecurity measures are currently in place?"),
        Question(id="sec_02", text="Have there been any security incidents or vulnerabilities?"),
        Question(id="sec_03", text="How is user access and authentication managed?")
    ]

    staffing_questions = [
        Question(id="staff_01", text="What is the current IT staffing structure?"),
        Question(id="staff_02", text="Are there identified skill gaps or training needs?"),
        Question(id="staff_03", text="How is IT support and maintenance handled?")
    ]

    # Define topic areas
    topics = [
        Topic(
            id="infrastructure",
            name="IT Infrastructure",
            questions=infrastructure_questions
        ),
        Topic(
            id="security",
            name="Cybersecurity",
            questions=security_questions
        ),
        Topic(
            id="staffing",
            name="IT Staffing & Skills",
            questions=staffing_questions
        )
    ]

    return EngagementConfig(
        engagement_id="demo_2024_001",
        organization_name="Demo Corporation",
        categories=topics
    )


async def demonstrate_api_workflow():
    """Demonstrate the complete API workflow"""

    print("🚀 Tech Assessment System - API Workflow Demo")
    print("=" * 60)

    # 1. Prepare configuration and files
    config = create_sample_engagement()
    transcript_files = [
        "data/transcripts/meeting_1.txt",
        "data/transcripts/meeting_2.txt",
        "data/transcripts/meeting_3.txt"
    ]

    print(f"📋 Assessment Configuration:")
    print(f"   Organization: {config.organization_name}")
    print(f"   Topics: {len(config.categories)}")
    print(f"   Total Questions: {sum(len(t.questions) for t in config.categories)}")
    print(f"   Transcript Files: {len(transcript_files)}")

    # 2. Start Assessment (POST /assessments/start)
    start_request = {
        "config": config.model_dump(),
        "transcript_files": transcript_files
    }

    print("\\n🔄 Starting assessment...")
    print("   This would be: POST /assessments/start")
    print(f"   Request body: {json.dumps(start_request, indent=2)[:200]}...")

    # Simulated response
    session_id = "demo-session-12345"
    print(f"\\n✅ Assessment started!")
    print(f"   Session ID: {session_id}")
    print(f"   Status: Processing transcripts...")

    # 3. Monitor Progress (GET /assessments/{session_id}/status)
    await asyncio.sleep(1)  # Simulate processing time
    print("\\n📊 Checking status...")
    print("   This would be: GET /assessments/demo-session-12345/status")

    status_response = {
        "session_id": session_id,
        "status": "waiting_approval",
        "pending_approval": True,
        "completed_topics": 0,
        "total_topics": 3,
        "completion_percentage": 0,
        "current_topic": "IT Infrastructure"
    }
    print(f"   Response: {json.dumps(status_response, indent=2)}")

    # 4. Review Current Topic (GET /assessments/{session_id}/review)
    print("\\n🔍 Topic ready for review!")
    print("   This would be: GET /assessments/demo-session-12345/review")

    # Simulate the human review process
    await simulate_topic_review("IT Infrastructure", 1, 3)

    # 5. Approve Topic (POST /assessments/{session_id}/approve)
    approval_request = {"action": "accept"}
    print("\\n✅ Approving topic...")
    print("   This would be: POST /assessments/demo-session-12345/approve")
    print(f"   Request body: {json.dumps(approval_request)}")

    # Simulate remaining topics
    for topic_num in [2, 3]:
        topic_names = ["Cybersecurity", "IT Staffing & Skills"]
        topic_name = topic_names[topic_num - 2]

        await asyncio.sleep(1)
        print(f"\\n🔄 Processing topic {topic_num}/3: {topic_name}")
        await simulate_topic_review(topic_name, topic_num, 3)

        if topic_num == 2:
            # Demonstrate revision workflow
            print("\\n🔄 Requesting revision for better cost estimates...")
            revision_request = {
                "action": "revise",
                "revision_instructions": "Please provide more detailed cost breakdowns for the security recommendations"
            }
            print(f"   Request: {json.dumps(revision_request, indent=2)}")

            await asyncio.sleep(2)
            print("   ✅ Revision completed and approved!")
        else:
            print("   ✅ Topic approved!")

    # 6. Get Final Report (GET /assessments/{session_id}/report)
    print("\\n🎉 Assessment completed! Generating final report...")
    print("   This would be: GET /assessments/demo-session-12345/report")

    final_summary = {
        "engagement_id": "demo_2024_001",
        "organization_name": "Demo Corporation",
        "total_recommendations": 8,
        "high_priority_items": 3,
        "year_one_roadmap_items": 5,
        "estimated_total_investment": "$75,000 - $150,000"
    }

    print(f"\\n📊 Final Report Summary:")
    for key, value in final_summary.items():
        print(f"   {key.replace('_', ' ').title()}: {value}")

    # 7. Export Options (GET /assessments/{session_id}/export/{format})
    print("\\n📄 Export options:")
    print("   JSON Report: GET /assessments/demo-session-12345/export/json")
    print("   Executive Summary: GET /assessments/demo-session-12345/export/summary")

    print("\\n🏁 Workflow complete!")


async def simulate_topic_review(topic_name: str, current: int, total: int):
    """Simulate the topic review process"""

    print(f"\\n" + "="*50)
    print(f"🔍 TOPIC ANALYSIS COMPLETE: {topic_name}")
    print(f"Progress: {current}/{total}")
    print("="*50)

    print("\\n📋 QUESTION RESPONSES (3):")
    print("   ✓ All questions answered with supporting evidence")
    print("   ✓ Source excerpts identified and cited")

    print("\\n⚠️  IDENTIFIED RISKS (2-3):")
    print("   • Specific operational risks identified")
    print("   • Business impact assessments provided")
    print("   • Supporting quotes from transcripts")

    print("\\n💡 RECOMMENDATIONS (2-4):")
    print("   • High/Medium/Low priority assignments")
    print("   • Year 1-3 timeline estimates")
    print("   • Cost estimates and implementation steps")

    print("\\n🔄 REVIEW OPTIONS:")
    print("   • Type 'accept' to approve this analysis")
    print("   • Type 'revise: [instructions]' for changes")

    # Simulate human decision time
    await asyncio.sleep(0.5)


def demonstrate_local_usage():
    """Show how to use the system components directly"""

    print("\\n🔧 Direct Component Usage")
    print("="*40)

    print("\\n1. Transcript Processing:")
    print("   from ingestion import TranscriptProcessor")
    print("   processor = TranscriptProcessor()")
    print("   content = await processor.load_transcript_file('meeting.txt')")

    print("\\n2. Topic Analysis:")
    print("   from chains import TopicAnalyzer")
    print("   analyzer = TopicAnalyzer()")
    print("   report = await analyzer.analyze_topic(topic, transcripts)")

    print("\\n3. Report Generation:")
    print("   from export import ReportFormatter")
    print("   formatter = ReportFormatter()")
    print("   formatted = formatter.format_topic_for_review(report)")

    print("\\n4. Session Management:")
    print("   from utils import session_manager")
    print("   session_id = session_manager.create_session(config)")
    print("   progress = session_manager.get_session_progress(session_id)")


if __name__ == "__main__":
    print("Tech Assessment System - Complete Usage Demo")
    print("="*60)

    # Run API workflow demonstration
    asyncio.run(demonstrate_api_workflow())

    # Show direct usage patterns
    demonstrate_local_usage()

    print("\\n📚 Next Steps:")
    print("   1. Install dependencies: pip install -r requirements.txt")
    print("   2. Start the server: python main.py")
    print("   3. Open browser: http://localhost:8000/docs")
    print("   4. Upload transcripts and start your first assessment!")