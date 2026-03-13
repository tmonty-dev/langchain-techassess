"""
Report formatting for human review and export
"""
import json
from datetime import datetime
from typing import Dict, Any

from schemas.report import TopicReport, AssessmentReport, QuestionResponse, Risk, Recommendation


class ReportFormatter:
    """Handles formatting reports for various outputs"""

    def format_topic_for_review(self, topic_report: TopicReport) -> str:
        """Format a topic report for human review during approval process"""

        lines = []
        lines.append(f"\\n🔍 TOPIC ANALYSIS COMPLETE: {topic_report.Topic_name}")
        lines.append("=" * 60)

        # Question Responses Section
        lines.append("\\n📋 QUESTION RESPONSES:")
        for i, qr in enumerate(topic_report.question_responses, 1):
            lines.append(f"\\n{i}. {qr.question_text}")
            lines.append(f"   📝 Answer: {qr.answer}")
            lines.append(f"   📊 Sources: {len(qr.source_chunks)} supporting excerpts")

            # Show first source excerpt as preview
            if qr.source_chunks:
                preview = qr.source_chunks[0][:150]
                lines.append(f"   💭 Preview: \"{preview}...\"")

        # Risks Section
        lines.append(f"\\n⚠️  IDENTIFIED RISKS ({len(topic_report.risks)}):")
        for i, risk in enumerate(topic_report.risks, 1):
            lines.append(f"\\n{i}. {risk.description}")
            lines.append(f"   📄 Source: {risk.source_document}")
            quote_preview = risk.supporting_quote[:100] + "..." if len(risk.supporting_quote) > 100 else risk.supporting_quote
            lines.append(f"   💬 Quote: \"{quote_preview}\"")

        # Recommendations Section
        lines.append(f"\\n💡 RECOMMENDATIONS ({len(topic_report.recommendations)}):")
        for i, rec in enumerate(topic_report.recommendations, 1):
            lines.append(f"\\n{i}. {rec.title}")
            lines.append(f"   🎯 Priority: {rec.priority} | ⏰ Timeline: {rec.timeline}")
            lines.append(f"   💰 Cost: {rec.cost_estimate} ({rec.cost_type})")
            lines.append(f"   📝 Description: {rec.description[:150]}...")

            if rec.benefits:
                lines.append(f"   ✅ Key Benefits: {', '.join(rec.benefits[:2])}")

            if rec.next_steps:
                lines.append(f"   🚀 Next Steps: {rec.next_steps[0]}")

        # Review Instructions
        lines.append("\\n" + "=" * 60)
        lines.append("🔄 REVIEW OPTIONS:")
        lines.append("• Type 'accept' to approve this analysis")
        lines.append("• Type 'revise: [instructions]' to request changes")
        lines.append("\\n💡 REVISION EXAMPLES:")
        lines.append("  - 'revise: Add more detail to recommendation 2'")
        lines.append("  - 'revise: The risk analysis needs more specific business impact'")
        lines.append("  - 'revise: Question 1 answer needs better supporting evidence'")
        lines.append("  - 'revise: Include cost breakdown for staff training'")

        return "\\n".join(lines)

    def format_topic_for_web_review(self, topic_report: TopicReport) -> Dict[str, Any]:
        """Format topic report for web UI display"""

        return {
            "topic_id": topic_report.Topic_id,
            "topic_name": topic_report.Topic_name,
            "summary": {
                "questions_answered": len(topic_report.question_responses),
                "risks_identified": len(topic_report.risks),
                "recommendations_made": len(topic_report.recommendations),
                "high_priority_recs": sum(1 for r in topic_report.recommendations if r.priority == "High"),
                "year_one_recs": sum(1 for r in topic_report.recommendations if r.timeline == "Y1")
            },
            "sections": {
                "questions": [
                    {
                        "id": qr.question_id,
                        "question": qr.question_text,
                        "answer": qr.answer,
                        "source_count": len(qr.source_chunks),
                        "sources_preview": [
                            chunk[:200] + "..." if len(chunk) > 200 else chunk
                            for chunk in qr.source_chunks[:2]
                        ]
                    }
                    for qr in topic_report.question_responses
                ],
                "risks": [
                    {
                        "description": risk.description,
                        "source_document": risk.source_document,
                        "supporting_quote": risk.supporting_quote,
                        "severity": self._assess_risk_severity(risk.description)
                    }
                    for risk in topic_report.risks
                ],
                "recommendations": [
                    {
                        "title": rec.title,
                        "description": rec.description,
                        "priority": rec.priority,
                        "timeline": rec.timeline,
                        "cost_estimate": rec.cost_estimate,
                        "cost_type": rec.cost_type,
                        "benefits": rec.benefits,
                        "next_steps": rec.next_steps,
                        "addresses_risks": rec.addresses_risks,
                        "urgency_score": self._calculate_urgency_score(rec)
                    }
                    for rec in topic_report.recommendations
                ]
            }
        }

    def export_final_report_json(self, report: AssessmentReport) -> str:
        """Export final report as formatted JSON"""

        report_dict = report.model_dump()

        # Add metadata
        report_dict["export_metadata"] = {
            "export_date": datetime.now().isoformat(),
            "format_version": "1.0",
            "total_topics": len(report.categories),
            "total_recommendations": sum(len(cat.recommendations) for cat in report.categories),
            "total_risks": sum(len(cat.risks) for cat in report.categories)
        }

        return json.dumps(report_dict, indent=2, ensure_ascii=False)

    def export_executive_summary(self, report: AssessmentReport) -> str:
        """Generate executive summary text"""

        lines = []
        lines.append(f"# Technology Assessment Executive Summary")
        lines.append(f"**Organization:** {report.organization_name}")
        lines.append(f"**Assessment Date:** {datetime.now().strftime('%B %d, %Y')}")
        lines.append("")

        # Overall Statistics
        total_recs = sum(len(cat.recommendations) for cat in report.categories)
        high_priority = sum(
            len([r for r in cat.recommendations if r.priority == "High"])
            for cat in report.categories
        )
        total_risks = sum(len(cat.risks) for cat in report.categories)

        lines.append("## Key Findings")
        lines.append(f"- **{len(report.categories)}** areas assessed")
        lines.append(f"- **{total_recs}** recommendations identified")
        lines.append(f"- **{high_priority}** high-priority items")
        lines.append(f"- **{total_risks}** risks identified")
        lines.append("")

        # Year One Roadmap
        if report.year_one_roadmap:
            lines.append("## Year One Priorities")
            for item in report.year_one_roadmap:
                lines.append(f"- **{item.recommendation_title}** ({item.Topic})")
                lines.append(f"  - Cost: {item.cost_estimate}")
                quarters = []
                if item.q1: quarters.append("Q1")
                if item.q2: quarters.append("Q2")
                if item.q3: quarters.append("Q3")
                if item.q4: quarters.append("Q4")
                lines.append(f"  - Timeline: {', '.join(quarters)}")
            lines.append("")

        # Topic Summaries
        lines.append("## Assessment Areas")
        for category in report.categories:
            lines.append(f"### {category.Topic_name}")
            lines.append(f"- {len(category.recommendations)} recommendations")
            lines.append(f"- {len(category.risks)} risks identified")

            # Top recommendation
            if category.recommendations:
                top_rec = next(
                    (r for r in category.recommendations if r.priority == "High"),
                    category.recommendations[0]
                )
                lines.append(f"- **Key Priority:** {top_rec.title}")
            lines.append("")

        return "\\n".join(lines)

    def _assess_risk_severity(self, risk_description: str) -> str:
        """Assess risk severity based on description keywords"""

        high_keywords = ["critical", "severe", "major", "failure", "outage", "security", "data loss"]
        medium_keywords = ["moderate", "concern", "issue", "problem", "delay"]

        risk_lower = risk_description.lower()

        if any(keyword in risk_lower for keyword in high_keywords):
            return "High"
        elif any(keyword in risk_lower for keyword in medium_keywords):
            return "Medium"
        else:
            return "Low"

    def _calculate_urgency_score(self, recommendation: Recommendation) -> int:
        """Calculate urgency score for recommendations (0-100)"""

        score = 0

        # Priority weight
        priority_weights = {"High": 50, "Medium": 30, "Low": 10}
        score += priority_weights.get(recommendation.priority, 10)

        # Timeline weight (sooner = more urgent)
        timeline_weights = {"Y1": 30, "Y2": 20, "Y3": 10}
        score += timeline_weights.get(recommendation.timeline, 10)

        # Risk addressing weight
        score += min(len(recommendation.addresses_risks) * 5, 20)

        return min(score, 100)