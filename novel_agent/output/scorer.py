"""Novel scoring system with adjustable weights and categories."""
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from novel_agent.config import OPENAI_API_KEY, MODEL_NAME, TEMPERATURE, SCORING_CATEGORIES


class NovelScorer:
    """Scores novels based on multiple criteria with adjustable weights."""

    def __init__(self, custom_categories: Optional[Dict[str, int]] = None):
        """
        Initialize the scorer.

        Args:
            custom_categories: Optional custom scoring categories with weights (percentages)
        """
        self.categories = custom_categories or SCORING_CATEGORIES.copy()
        self._validate_weights()

        self.llm = ChatOpenAI(
            model=MODEL_NAME,
            temperature=TEMPERATURE - 0.3,  # Lower for more consistent scoring
            openai_api_key=OPENAI_API_KEY
        )

    def _validate_weights(self):
        """Ensure weights sum to 100."""
        total = sum(self.categories.values())
        if total != 100:
            # Normalize to 100
            factor = 100 / total
            self.categories = {k: int(v * factor) for k, v in self.categories.items()}

    def score_novel(self, novel_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score a complete novel.

        Args:
            novel_data: Dictionary containing novel data

        Returns:
            Comprehensive scoring report
        """
        scores = {}
        weighted_scores = {}
        feedback = {}

        # Score each category
        for category, weight in self.categories.items():
            score, category_feedback = self._score_category(novel_data, category)
            scores[category] = score
            weighted_scores[category] = round(score * weight / 10, 2)
            feedback[category] = category_feedback

        # Calculate total score
        total_score = sum(weighted_scores.values())

        return {
            'categories': self.categories,
            'scores': scores,
            'weighted_scores': weighted_scores,
            'total_score': round(total_score, 2),
            'grade': self._get_grade(total_score),
            'feedback': feedback,
            'summary': self._generate_summary(scores, feedback, total_score)
        }

    def score_chapter(self, chapter_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score a single chapter.

        Args:
            chapter_data: Chapter dictionary

        Returns:
            Chapter scoring report
        """
        # Simplified scoring for chapters
        chapter_categories = {
            'Writing Quality': 40,
            'Pacing': 30,
            'Character Development': 20,
            'Engagement': 10
        }

        scores = {}
        weighted_scores = {}

        for category, weight in chapter_categories.items():
            score, feedback = self._score_chapter_category(chapter_data, category)
            scores[category] = score
            weighted_scores[category] = round(score * weight / 10, 2)

        total_score = sum(weighted_scores.values())

        return {
            'categories': chapter_categories,
            'scores': scores,
            'weighted_scores': weighted_scores,
            'total_score': round(total_score, 2),
            'grade': self._get_grade(total_score)
        }

    def update_weights(self, new_weights: Dict[str, int]):
        """
        Update scoring category weights.

        Args:
            new_weights: Dictionary of category names to weights
        """
        self.categories.update(new_weights)
        self._validate_weights()

    def add_category(self, category_name: str, weight: int):
        """
        Add a new scoring category.

        Args:
            category_name: Name of the category
            weight: Weight percentage
        """
        self.categories[category_name] = weight
        self._validate_weights()

    def remove_category(self, category_name: str):
        """
        Remove a scoring category.

        Args:
            category_name: Name of the category to remove
        """
        if category_name in self.categories:
            del self.categories[category_name]
            self._validate_weights()

    def _score_category(self, novel_data: Dict[str, Any], category: str) -> tuple[float, str]:
        """Score a specific category."""
        system_message = f"""You are a professional book critic scoring novels.
Rate the {category} aspect of this novel on a scale of 0-10.
Be objective and provide specific reasoning."""

        # Prepare novel summary for scoring
        novel_summary = self._prepare_novel_summary(novel_data)

        # Category-specific prompts
        category_prompts = {
            'Story/Plot': 'Evaluate plot structure, pacing, conflict, resolution, and overall narrative arc.',
            'Character Development': 'Assess character depth, growth, motivations, and believability.',
            'World-Building / Setting': 'Evaluate setting details, atmosphere, and world consistency.',
            'Writing Style / Language': 'Assess prose quality, voice, sentence variety, and technical skill.',
            'Dialogue & Interactions': 'Evaluate dialogue naturalness, character voice distinctiveness, and effectiveness.',
            'Emotional Impact / Engagement': 'Assess reader engagement, emotional resonance, and memorability.'
        }

        prompt_guidance = category_prompts.get(category, f'Evaluate the {category} aspect.')

        user_prompt = f"""Score this novel's {category}:

{novel_summary}

{prompt_guidance}

Provide:
1. Score (0-10)
2. Brief explanation (2-3 sentences)

Format as:
SCORE: [0-10]
FEEDBACK: [explanation]"""

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        return self._parse_score_response(response.content)

    def _score_chapter_category(self, chapter_data: Dict[str, Any], category: str) -> tuple[float, str]:
        """Score a chapter category."""
        system_message = f"""You are scoring a chapter's {category}.
Rate on a scale of 0-10 with specific reasoning."""

        content = chapter_data.get('content', '')[:2000]  # First 2000 chars

        user_prompt = f"""Score this chapter's {category}:

Chapter {chapter_data.get('chapter_number', '?')}: {chapter_data.get('title', 'Untitled')}

{content}...

Provide:
SCORE: [0-10]
FEEDBACK: [brief explanation]"""

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        return self._parse_score_response(response.content)

    def _prepare_novel_summary(self, novel_data: Dict[str, Any]) -> str:
        """Prepare a summary of the novel for scoring."""
        summary_parts = []

        if novel_data.get('title'):
            summary_parts.append(f"Title: {novel_data['title']}")

        if novel_data.get('genre'):
            summary_parts.append(f"Genre: {novel_data['genre']}")

        if novel_data.get('premise'):
            summary_parts.append(f"\nPremise: {novel_data['premise']}")

        # Sample chapters
        chapters = novel_data.get('chapters', [])
        if chapters:
            summary_parts.append(f"\nChapters: {len(chapters)}")
            summary_parts.append("\nSample content:")

            # Include first chapter
            if len(chapters) > 0:
                summary_parts.append(f"\nChapter 1: {chapters[0].get('content', '')[:1000]}...")

            # Include a middle chapter
            if len(chapters) > 5:
                mid_chapter = chapters[len(chapters) // 2]
                summary_parts.append(f"\nChapter {mid_chapter.get('chapter_number', '?')}: {mid_chapter.get('content', '')[:1000]}...")

        # Characters
        if novel_data.get('characters'):
            summary_parts.append(f"\nCharacters: {len(novel_data['characters'])}")

        return "\n".join(summary_parts)

    def _parse_score_response(self, response: str) -> tuple[float, str]:
        """Parse scoring response."""
        score = 5.0  # Default
        feedback = ""

        for line in response.split('\n'):
            line_stripped = line.strip()
            if line_stripped.startswith('SCORE:'):
                try:
                    score_str = line_stripped.replace('SCORE:', '').strip()
                    score = float(score_str)
                    score = max(0, min(10, score))  # Clamp to 0-10
                except ValueError:
                    pass
            elif line_stripped.startswith('FEEDBACK:'):
                feedback = line_stripped.replace('FEEDBACK:', '').strip()
            elif feedback and not line_stripped.startswith('SCORE:'):
                # Continue multi-line feedback
                feedback += ' ' + line_stripped

        return score, feedback

    def _get_grade(self, total_score: float) -> str:
        """Convert score to letter grade."""
        if total_score >= 9.0:
            return 'A+'
        elif total_score >= 8.5:
            return 'A'
        elif total_score >= 8.0:
            return 'A-'
        elif total_score >= 7.5:
            return 'B+'
        elif total_score >= 7.0:
            return 'B'
        elif total_score >= 6.5:
            return 'B-'
        elif total_score >= 6.0:
            return 'C+'
        elif total_score >= 5.5:
            return 'C'
        elif total_score >= 5.0:
            return 'C-'
        elif total_score >= 4.0:
            return 'D'
        else:
            return 'F'

    def _generate_summary(
        self,
        scores: Dict[str, float],
        feedback: Dict[str, str],
        total_score: float
    ) -> str:
        """Generate overall summary of the scoring."""
        summary_parts = [f"Overall Score: {total_score:.2f}/10.0 ({self._get_grade(total_score)})"]
        summary_parts.append("\nStrengths:")

        # Find top 2 categories
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        for category, score in sorted_scores[:2]:
            if score >= 7.0:
                summary_parts.append(f"- {category}: {score}/10")

        summary_parts.append("\nAreas for Improvement:")

        # Find bottom 2 categories
        for category, score in sorted_scores[-2:]:
            if score < 7.0:
                summary_parts.append(f"- {category}: {score}/10")
                if category in feedback and feedback[category]:
                    summary_parts.append(f"  {feedback[category][:100]}...")

        return "\n".join(summary_parts)

    def format_score_table(self, score_report: Dict[str, Any]) -> str:
        """
        Format the score report as a readable table.

        Args:
            score_report: Score report dictionary

        Returns:
            Formatted table string
        """
        lines = []

        lines.append("=" * 80)
        lines.append("NOVEL SCORING REPORT".center(80))
        lines.append("=" * 80)
        lines.append("")

        # Header
        lines.append(f"{'Category':<30} {'Weight':<10} {'Score (0-10)':<15} {'Weighted Score':<15}")
        lines.append("-" * 80)

        # Categories
        for category in score_report['categories'].keys():
            weight = score_report['categories'][category]
            score = score_report['scores'][category]
            weighted = score_report['weighted_scores'][category]

            lines.append(f"{category:<30} {weight}%{'':<6} {score:<15.1f} {weighted:<15.2f}")

        lines.append("-" * 80)

        # Total
        total = score_report['total_score']
        grade = score_report['grade']
        lines.append(f"{'TOTAL SCORE':<30} {'100%':<10} {'':<15} {total:<15.2f}")
        lines.append(f"{'GRADE':<30} {'':<10} {'':<15} {grade:<15}")

        lines.append("=" * 80)
        lines.append("")

        # Summary
        lines.append(score_report['summary'])

        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)
