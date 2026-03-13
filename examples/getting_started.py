#!/usr/bin/env python3
"""
Getting Started Example for Tech Assessment System

This example demonstrates how to set up and run a basic assessment.
"""

import asyncio
import json
from pathlib import Path

# Import your schemas
from schemas.config import EngagementConfig, Topic, Question


def create_sample_assessment_config():
    """Create a simple assessment configuration"""

    print("📋 Creating sample assessment configuration...")

    # Define assessment questions for each topic
    infrastructure_questions = [
        Question(
            id="inf_01",
            text="What is the current state of the IT infrastructure?"
        ),
        Question(
            id="inf_02",
            text="Are there any performance or reliability issues?"
        ),
        Question(
            id="inf_03",
            text="What are the current backup and disaster recovery procedures?"
        )
    ]

    security_questions = [
        Question(
            id="sec_01",
            text="What cybersecurity measures are currently in place?"
        ),
        Question(
            id="sec_02",
            text="Have there been any recent security incidents?"
        )
    ]

    # Define topic areas to assess
    topics = [
        Topic(
            id="infrastructure",
            name="IT Infrastructure & Operations",
            questions=infrastructure_questions
        ),
        Topic(
            id="security",
            name="Cybersecurity & Risk Management",
            questions=security_questions
        )
    ]

    # Create the engagement configuration
    config = EngagementConfig(
        engagement_id="demo_001",
        organization_name="Sample Organization",
        categories=topics
    )

    print(f"✅ Configuration created:")
    print(f"   - Organization: {config.organization_name}")
    print(f"   - Topics: {len(config.categories)}")
    print(f"   - Total Questions: {sum(len(t.questions) for t in config.categories)}")

    return config


def create_sample_transcripts():
    """Create sample transcript files for testing"""

    print("\n📝 Creating sample transcript files...")

    # Create data directory
    Path("data/transcripts").mkdir(parents=True, exist_ok=True)

    # Sample transcript content
    transcript1_content = """
Interviewer: Can you tell me about your current IT infrastructure?

IT Manager: We have about 12 servers in our main office, most of them are about 5 years old. We've been having some issues with our email server lately, it's been going down maybe once a week. Our network is mostly wired, though we do have WiFi in the break rooms.

We also have a small datacenter room, but it's not climate controlled very well. Sometimes it gets quite warm in there during summer.

Interviewer: What about your security measures?

IT Manager: We have antivirus on all the desktops, and we require passwords to be changed every 90 days. We don't really have a formal security policy though. Most of our data is stored on a shared drive that everyone can access.

We did have someone's email get compromised last year, they sent out spam to our whole contact list. That was embarrassing.
"""

    transcript2_content = """
Interviewer: How do you handle backups and disaster recovery?

IT Manager: We do backups to an external hard drive every night, well, when someone remembers to plug it in. It's not automated. We've never really tested restoring from backup.

If we lost our main server, I'm not sure how long it would take to get back up and running. We don't have any off-site backups.

Interviewer: What about your team structure?

IT Manager: It's just me full-time, and we have a part-time contractor who comes in when we have bigger projects. I handle everything from help desk tickets to server maintenance. It can get overwhelming when multiple things break at once.

We don't really have documented procedures for most tasks. If something happened to me, the organization would be in trouble.
"""

    # Write transcript files
    with open("data/transcripts/interview_1.txt", "w") as f:
        f.write(transcript1_content)

    with open("data/transcripts/interview_2.txt", "w") as f:
        f.write(transcript2_content)

    transcript_files = [
        "data/transcripts/interview_1.txt",
        "data/transcripts/interview_2.txt"
    ]

    print(f"✅ Created {len(transcript_files)} sample transcript files")

    return transcript_files


async def run_assessment_example():
    """Example of how to run an assessment via API calls"""

    print("\n🚀 Assessment API Example")
    print("=" * 50)

    # This would be done via HTTP requests in a real scenario
    print("1. 📤 Starting assessment (POST /assessments/start)")

    config = create_sample_assessment_config()
    transcript_files = create_sample_transcripts()

    # Simulate API request
    start_request = {
        "config": config.model_dump(),
        "transcript_files": transcript_files
    }

    print(f"   Request payload: {len(json.dumps(start_request))} characters")

    # Simulate response
    session_id = "example-session-123"
    print(f"   ✅ Session started: {session_id}")

    print("\n2. 📊 Monitoring progress (GET /assessments/{session_id}/status)")
    print("   Status: Processing transcripts and analyzing topics...")

    print("\n3. 🔍 First topic ready for review!")
    print("   Topic: IT Infrastructure & Operations")
    print("   Questions answered: 3")
    print("   Risks identified: 2")
    print("   Recommendations: 4")

    print("\n4. 👤 Human review process:")
    print("   - Review analysis quality")
    print("   - Accept: POST /approve {'action': 'accept'}")
    print("   - Revise: POST /approve {'action': 'revise', 'revision_instructions': '...'}")

    print("\n5. 🎉 Assessment completed!")
    print("   Final report available: GET /assessments/{session_id}/report")


def show_direct_usage_example():
    """Example of using components directly (without API)"""

    print("\n🔧 Direct Component Usage Example")
    print("=" * 50)

    print("Using the system components directly in Python:")

    example_code = '''
# 1. Load and process transcripts
from ingestion import TranscriptProcessor

processor = TranscriptProcessor()
content = await processor.load_transcript_file("meeting.txt")
processed = await processor.preprocess_transcripts([content])

# 2. Analyze a topic
from chains import TopicAnalyzer

analyzer = TopicAnalyzer()
topic_report = await analyzer.analyze_topic(
    topic=your_topic,
    transcripts=processed,
    revision_instructions=""  # Optional
)

# 3. Format for review
from export import ReportFormatter

formatter = ReportFormatter()
review_text = formatter.format_topic_for_review(topic_report)
print(review_text)

# 4. Generate final roadmap
from export import RoadmapGenerator

generator = RoadmapGenerator()
roadmap = await generator.create_roadmap([topic_report], config)
'''

    print(example_code)


if __name__ == "__main__":
    print("🎯 Tech Assessment System - Getting Started")
    print("=" * 60)

    # Show configuration example
    config = create_sample_assessment_config()

    # Show transcript setup
    transcript_files = create_sample_transcripts()

    # Show API workflow
    asyncio.run(run_assessment_example())

    # Show direct usage
    show_direct_usage_example()

    print("\n🚀 Next Steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Set up your LLM API key in .env")
    print("3. Start the server: python main.py")
    print("4. Open http://localhost:8000/docs for API documentation")
    print("5. Create your own assessment configuration")
    print("6. Upload your real transcript files")
    print("7. Start your first assessment!")

    print(f"\n📁 Sample files created in: {Path('data/transcripts').absolute()}")