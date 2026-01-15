"""Consistency checker module for maintaining story coherence."""
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from novel_agent.config import OPENAI_API_KEY, MODEL_NAME, TEMPERATURE
from novel_agent.memory.context_manager import ContextManager
from novel_agent.memory.long_term_memory import LongTermMemory


class ConsistencyChecker:
    """Checks and maintains consistency across character traits, settings, and timelines."""

    def __init__(self, context_manager: ContextManager, memory: LongTermMemory):
        """
        Initialize the consistency checker.

        Args:
            context_manager: ContextManager instance
            memory: LongTermMemory instance
        """
        self.context_manager = context_manager
        self.memory = memory
        self.llm = ChatOpenAI(
            model=MODEL_NAME,
            temperature=TEMPERATURE - 0.3,  # Lower for analytical tasks
            openai_api_key=OPENAI_API_KEY
        )

    def check_character_consistency(self, chapter_content: str) -> Dict[str, Any]:
        """
        Check character consistency in a chapter.

        Args:
            chapter_content: Chapter content to check

        Returns:
            Dictionary with consistency issues and recommendations
        """
        # Get all character profiles from memory
        characters = self.memory.get_all_characters()

        if not characters:
            return {'issues': [], 'warnings': ['No character profiles in memory to check against']}

        char_profiles = "\n\n".join([doc.page_content for doc in characters])

        system_message = """You are a continuity editor checking character consistency.
Identify any inconsistencies in:
- Physical descriptions (appearance, age, etc.)
- Personality traits and behavior
- Speech patterns and vocabulary
- Character knowledge and memories
- Relationships with other characters
- Character motivations and goals"""

        user_prompt = f"""Check this chapter for character consistency:

CHAPTER CONTENT:
{chapter_content[:3000]}

ESTABLISHED CHARACTER PROFILES:
{char_profiles[:2000]}

Identify any inconsistencies, contradictions, or out-of-character moments.

Format as:
ISSUES:
- Character: [name]
  Problem: [description]
  Evidence: [quote from chapter]
  Profile says: [what's established]

WARNINGS:
- [potential issues that may need attention]

APPROVED:
- [characters that are consistent]"""

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        return self._parse_consistency_report(response.content)

    def check_setting_consistency(self, chapter_content: str, chapter_setting: str) -> Dict[str, Any]:
        """
        Check setting and world-building consistency.

        Args:
            chapter_content: Chapter content to check
            chapter_setting: Declared chapter setting

        Returns:
            Dictionary with consistency issues
        """
        # Get setting information from memory
        settings = self.memory.retrieve_by_type("setting", k=5)

        if not settings:
            return {'issues': [], 'warnings': ['No setting information in memory to check against']}

        setting_info = "\n\n".join([doc.page_content for doc in settings])

        system_message = """You are checking setting and world-building consistency.
Identify inconsistencies in:
- Physical environment descriptions
- Technology or magic system usage
- Cultural elements (customs, language, beliefs)
- Geography and locations
- Time period indicators
- Weather and seasons
- Societal rules and norms"""

        user_prompt = f"""Check this chapter for setting consistency:

CHAPTER CONTENT:
{chapter_content[:3000]}

CHAPTER SETTING: {chapter_setting}

ESTABLISHED WORLD-BUILDING:
{setting_info[:2000]}

Identify any contradictions or inconsistencies with established world-building.

Format as:
ISSUES:
- Category: [what type of inconsistency]
  Problem: [description]
  Evidence: [quote from chapter]
  Established: [what was previously set]

WARNINGS:
- [potential issues]"""

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        return self._parse_consistency_report(response.content)

    def check_timeline_consistency(self, chapters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Check timeline consistency across multiple chapters.

        Args:
            chapters: List of chapter dictionaries with content

        Returns:
            Dictionary with timeline issues
        """
        system_message = """You are checking timeline and chronological consistency.
Identify issues with:
- Time passage (too fast, too slow, unclear)
- Event sequencing
- Character ages and growth
- Seasonal/weather changes
- References to past or future events
- Contradictory time references"""

        chapters_summary = "\n\n".join([
            f"CHAPTER {ch.get('chapter_number', i+1)}: {ch.get('title', 'Untitled')}\n{ch.get('content', '')[:500]}..."
            for i, ch in enumerate(chapters[:10])  # Limit to 10 chapters
        ])

        user_prompt = f"""Check timeline consistency across these chapters:

{chapters_summary}

Identify any timeline issues, contradictions, or unclear time passages.

Format as:
ISSUES:
- Chapters: [which chapters]
  Problem: [description]
  Evidence: [relevant quotes]

TIMELINE NOTES:
- [observations about time passage]

RECOMMENDATIONS:
- [suggestions for fixing issues]"""

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        return self._parse_timeline_report(response.content)

    def check_plot_consistency(self, chapter_content: str) -> Dict[str, Any]:
        """
        Check plot consistency against established plot points.

        Args:
            chapter_content: Chapter content to check

        Returns:
            Dictionary with plot consistency issues
        """
        # Get plot information from memory
        plot = self.memory.get_plot_summary()

        if not plot:
            return {'issues': [], 'warnings': ['No plot information in memory to check against']}

        system_message = """You are checking plot consistency.
Identify issues with:
- Contradictions to established plot points
- Forgotten plot threads
- Unresolved setups
- Logic gaps or plot holes
- Character motivations not matching actions"""

        user_prompt = f"""Check this chapter for plot consistency:

CHAPTER CONTENT:
{chapter_content[:3000]}

ESTABLISHED PLOT:
{plot.page_content[:2000]}

Identify any plot inconsistencies or contradictions.

Format as:
ISSUES:
- Problem: [description]
  Evidence: [quote]
  Conflicts with: [established plot point]

PLOT THREADS:
- Active: [ongoing plot threads in this chapter]
- Forgotten: [plot threads that seem dropped]

RECOMMENDATIONS:
- [suggestions]"""

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        return self._parse_consistency_report(response.content)

    def generate_consistency_report(self, novel_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a comprehensive consistency report for the entire novel.

        Args:
            novel_data: Dictionary with all novel data (chapters, characters, etc.)

        Returns:
            Comprehensive consistency report
        """
        report = {
            'character_issues': [],
            'setting_issues': [],
            'timeline_issues': [],
            'plot_issues': [],
            'overall_assessment': ''
        }

        chapters = novel_data.get('chapters', [])

        # Check each chapter
        for chapter in chapters[:5]:  # Sample first 5 chapters
            content = chapter.get('content', '')

            # Character consistency
            char_check = self.check_character_consistency(content)
            if char_check.get('issues'):
                report['character_issues'].extend(char_check['issues'])

            # Setting consistency
            setting_check = self.check_setting_consistency(
                content,
                chapter.get('setting', 'Unknown')
            )
            if setting_check.get('issues'):
                report['setting_issues'].extend(setting_check['issues'])

            # Plot consistency
            plot_check = self.check_plot_consistency(content)
            if plot_check.get('issues'):
                report['plot_issues'].extend(plot_check['issues'])

        # Timeline consistency across all chapters
        timeline_check = self.check_timeline_consistency(chapters)
        if timeline_check.get('issues'):
            report['timeline_issues'] = timeline_check['issues']

        # Generate overall assessment
        total_issues = (
            len(report['character_issues']) +
            len(report['setting_issues']) +
            len(report['plot_issues']) +
            len(report['timeline_issues'])
        )

        if total_issues == 0:
            report['overall_assessment'] = "Excellent consistency maintained throughout."
        elif total_issues < 5:
            report['overall_assessment'] = "Generally consistent with minor issues that should be addressed."
        elif total_issues < 10:
            report['overall_assessment'] = "Moderate consistency issues requiring attention."
        else:
            report['overall_assessment'] = "Significant consistency issues that need resolution."

        return report

    def suggest_fix(self, issue: Dict[str, str], context: str) -> str:
        """
        Suggest a fix for a consistency issue.

        Args:
            issue: Issue dictionary
            context: Relevant context

        Returns:
            Suggested fix
        """
        system_message = """You are suggesting fixes for consistency issues.
Provide a specific, actionable solution that maintains story quality."""

        user_prompt = f"""Suggest a fix for this consistency issue:

ISSUE: {issue.get('problem', '')}
EVIDENCE: {issue.get('evidence', '')}
CONTEXT: {context[:1000]}

Provide a specific fix that resolves the inconsistency."""

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        return response.content.strip()

    def _parse_consistency_report(self, response: str) -> Dict[str, Any]:
        """Parse consistency check response."""
        result = {'issues': [], 'warnings': [], 'approved': []}

        current_section = None
        current_issue = {}

        for line in response.split('\n'):
            line_stripped = line.strip()
            line_upper = line_stripped.upper()

            if line_upper.startswith('ISSUES:'):
                current_section = 'issues'
            elif line_upper.startswith('WARNINGS:'):
                current_section = 'warnings'
            elif line_upper.startswith('APPROVED:'):
                current_section = 'approved'
            elif line_stripped.startswith('- '):
                # New item
                if current_section == 'issues':
                    if current_issue:
                        result['issues'].append(current_issue)
                    current_issue = {'text': line_stripped[2:]}
                else:
                    if current_section:
                        result[current_section].append(line_stripped[2:])
            elif current_section == 'issues' and ':' in line_stripped and not line_stripped.startswith('-'):
                # Issue detail
                parts = line_stripped.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip().lower().replace(' ', '_')
                    current_issue[key] = parts[1].strip()

        if current_issue and current_section == 'issues':
            result['issues'].append(current_issue)

        return result

    def _parse_timeline_report(self, response: str) -> Dict[str, Any]:
        """Parse timeline consistency report."""
        result = {'issues': [], 'timeline_notes': [], 'recommendations': []}

        current_section = None

        for line in response.split('\n'):
            line_stripped = line.strip()
            line_upper = line_stripped.upper()

            if line_upper.startswith('ISSUES:'):
                current_section = 'issues'
            elif line_upper.startswith('TIMELINE NOTES:'):
                current_section = 'timeline_notes'
            elif line_upper.startswith('RECOMMENDATIONS:'):
                current_section = 'recommendations'
            elif line_stripped.startswith('- ') and current_section:
                result[current_section].append(line_stripped[2:])

        return result
