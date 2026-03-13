"""
Roadmap generation from approved topic analyses
"""
import logging
from typing import List, Dict, Any
from collections import defaultdict

from schemas.config import EngagementConfig
from schemas.report import TopicReport, RoadmapItem, Recommendation

logger = logging.getLogger(__name__)


class RoadmapGenerator:
    """Generates prioritized roadmaps from approved topic analyses"""

    def __init__(self):
        self.priority_weights = {"High": 3, "Medium": 2, "Low": 1}
        self.timeline_weights = {"Y1": 3, "Y2": 2, "Y3": 1}

    async def create_roadmap(
        self,
        topic_reports: List[TopicReport],
        config: EngagementConfig
    ) -> List[RoadmapItem]:
        """Generate prioritized roadmap from all approved topic reports"""

        logger.info("Generating roadmap from approved topics")

        # Collect all recommendations
        all_recommendations = []
        for topic_report in topic_reports:
            for rec in topic_report.recommendations:
                all_recommendations.append({
                    "recommendation": rec,
                    "topic_name": topic_report.Topic_name,
                    "topic_id": topic_report.Topic_id
                })

        logger.info(f"Processing {len(all_recommendations)} total recommendations")

        # Score and prioritize recommendations
        scored_recs = []
        for rec_data in all_recommendations:
            score = self._calculate_recommendation_score(rec_data["recommendation"])
            scored_recs.append({
                **rec_data,
                "score": score
            })

        # Sort by score (highest first)
        scored_recs.sort(key=lambda x: x["score"], reverse=True)

        # Select top recommendations for Year 1 roadmap
        year_one_recs = [
            rec for rec in scored_recs
            if rec["recommendation"].timeline == "Y1"
        ]

        # Limit to top 10-15 items for manageable roadmap
        top_recommendations = year_one_recs[:12]

        logger.info(f"Selected {len(top_recommendations)} recommendations for roadmap")

        # Convert to roadmap items with quarter assignments
        roadmap_items = []
        for rec_data in top_recommendations:
            roadmap_item = await self._create_roadmap_item(
                rec_data["recommendation"],
                rec_data["topic_name"],
                rec_data["topic_id"]
            )
            roadmap_items.append(roadmap_item)

        # Assign quarters based on dependencies and priorities
        roadmap_items = self._assign_quarters(roadmap_items)

        return roadmap_items

    def _calculate_recommendation_score(self, recommendation: Recommendation) -> float:
        """Calculate priority score for recommendation"""

        score = 0.0

        # Priority weight (40% of score)
        priority_score = self.priority_weights.get(recommendation.priority, 1)
        score += priority_score * 40

        # Timeline weight (20% of score) - Y1 items get higher priority
        timeline_score = self.timeline_weights.get(recommendation.timeline, 1)
        score += timeline_score * 20

        # Risk mitigation weight (25% of score)
        risk_score = min(len(recommendation.addresses_risks) * 8, 25)
        score += risk_score

        # Cost efficiency weight (15% of score) - lower cost gets higher score
        cost_score = self._assess_cost_efficiency(
            recommendation.cost_estimate,
            len(recommendation.benefits)
        )
        score += cost_score

        return score

    def _assess_cost_efficiency(self, cost_estimate: str, benefit_count: int) -> float:
        """Assess cost efficiency (0-15 points)"""

        # Extract rough cost from estimate
        cost_value = self._extract_cost_value(cost_estimate)

        # Calculate benefit-to-cost ratio
        if cost_value == 0:
            return 15.0  # Unknown cost, assume efficient

        # Simple heuristic: more benefits per dollar = higher score
        if cost_value < 10000:  # Low cost
            return 15.0 if benefit_count >= 2 else 10.0
        elif cost_value < 50000:  # Medium cost
            return 12.0 if benefit_count >= 3 else 8.0
        else:  # High cost
            return 10.0 if benefit_count >= 4 else 5.0

    def _extract_cost_value(self, cost_estimate: str) -> float:
        """Extract numeric value from cost estimate string"""

        import re

        # Remove common prefixes and clean
        cost_clean = cost_estimate.lower().replace('$', '').replace(',', '')

        # Look for patterns like "10,000", "10k", "10,000 - 25,000"
        patterns = [
            r'(\\d+)\\s*k',  # 10k format
            r'(\\d+)\\s*-\\s*(\\d+)',  # range format, take average
            r'(\\d+)',  # simple number
        ]

        for pattern in patterns:
            match = re.search(pattern, cost_clean)
            if match:
                if len(match.groups()) == 2:  # Range
                    low = float(match.group(1))
                    high = float(match.group(2))
                    return (low + high) / 2
                else:  # Single value
                    value = float(match.group(1))
                    # If it was in 'k' format, multiply by 1000
                    if 'k' in cost_clean:
                        value *= 1000
                    return value

        return 0  # Unknown cost

    async def _create_roadmap_item(
        self,
        recommendation: Recommendation,
        topic_name: str,
        topic_id: str
    ) -> RoadmapItem:
        """Convert recommendation to roadmap item"""

        return RoadmapItem(
            recommendation_title=recommendation.title,
            Topic=topic_name,
            cost_estimate=recommendation.cost_estimate,
            cost_type=recommendation.cost_type,
            q1=False,  # Will be assigned in _assign_quarters
            q2=False,
            q3=False,
            q4=False
        )

    def _assign_quarters(self, roadmap_items: List[RoadmapItem]) -> List[RoadmapItem]:
        """Assign quarters to roadmap items based on priorities and dependencies"""

        # Group by cost type for logical sequencing
        cost_groups = defaultdict(list)
        for item in roadmap_items:
            cost_groups[item.cost_type].append(item)

        # Priority order for implementation
        implementation_order = ["Labor", "Software", "Hardware", "One-Time", "Ongoing", "Mixed"]

        assigned_items = []
        current_quarter_load = {"q1": 0, "q2": 0, "q3": 0, "q4": 0}
        max_items_per_quarter = 4

        for cost_type in implementation_order:
            if cost_type not in cost_groups:
                continue

            items = cost_groups[cost_type]

            for item in items:
                # Find the earliest quarter with capacity
                assigned = False

                for quarter in ["q1", "q2", "q3", "q4"]:
                    if current_quarter_load[quarter] < max_items_per_quarter:
                        setattr(item, quarter, True)
                        current_quarter_load[quarter] += 1
                        assigned = True
                        break

                # If all quarters full, assign to Q4 anyway
                if not assigned:
                    item.q4 = True

                assigned_items.append(item)

        # Ensure foundational items (Labor, Software) are in early quarters
        self._prioritize_foundational_items(assigned_items)

        return assigned_items

    def _prioritize_foundational_items(self, roadmap_items: List[RoadmapItem]) -> None:
        """Ensure foundational items (staffing, basic software) are scheduled early"""

        foundational_keywords = [
            "staff", "training", "hire", "skill", "security", "backup",
            "antivirus", "password", "access control"
        ]

        for item in roadmap_items:
            title_lower = item.recommendation_title.lower()

            # Check if this is a foundational item
            is_foundational = any(
                keyword in title_lower for keyword in foundational_keywords
            )

            if is_foundational:
                # Move to Q1 or Q2 if not already scheduled early
                if not (item.q1 or item.q2):
                    # Clear current assignment
                    item.q3 = False
                    item.q4 = False

                    # Assign to earliest available
                    item.q1 = True

    def generate_roadmap_summary(self, roadmap_items: List[RoadmapItem]) -> Dict[str, Any]:
        """Generate summary statistics for the roadmap"""

        summary = {
            "total_items": len(roadmap_items),
            "by_quarter": {
                "q1": sum(1 for item in roadmap_items if item.q1),
                "q2": sum(1 for item in roadmap_items if item.q2),
                "q3": sum(1 for item in roadmap_items if item.q3),
                "q4": sum(1 for item in roadmap_items if item.q4)
            },
            "by_cost_type": defaultdict(int),
            "by_topic": defaultdict(int),
            "estimated_total_cost": "TBD"
        }

        for item in roadmap_items:
            summary["by_cost_type"][item.cost_type] += 1
            summary["by_topic"][item.Topic] += 1

        # Convert defaultdicts to regular dicts for JSON serialization
        summary["by_cost_type"] = dict(summary["by_cost_type"])
        summary["by_topic"] = dict(summary["by_topic"])

        return summary