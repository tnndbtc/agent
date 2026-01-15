"""Editing and refinement module for improving novel content."""
from typing import Dict, Any, Optional, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from novel_agent.config import OPENAI_API_KEY, MODEL_NAME, TEMPERATURE
from novel_agent.data.example_manager import ExampleManager


class EditorModule:
    """Provides editing and refinement suggestions for novel content."""

    def __init__(self, example_manager: ExampleManager):
        """
        Initialize the editor module.

        Args:
            example_manager: ExampleManager instance
        """
        self.example_manager = example_manager
        self.llm = ChatOpenAI(
            model=MODEL_NAME,
            temperature=TEMPERATURE - 0.2,  # Lower for more focused editing
            openai_api_key=OPENAI_API_KEY
        )

    def edit_for_style(self, content: str, target_style: str = "literary") -> Dict[str, Any]:
        """
        Suggest style improvements.

        Args:
            content: Content to edit
            target_style: Target writing style

        Returns:
            Dictionary with suggestions and revised content
        """
        # Get good examples for reference
        good_examples = self.example_manager.get_good_examples(category="writing", limit=1)
        bad_examples = self.example_manager.get_bad_examples(category="writing", limit=1)

        example_context = ""
        if good_examples:
            example_context += f"\nGood example:\n{good_examples[0]['content'][:300]}\n"
        if bad_examples:
            example_context += f"\nBad example (avoid this):\n{bad_examples[0]['content'][:300]}\n"

        system_message = f"""You are an expert editor specializing in {target_style} fiction.
Analyze the text for style improvements focusing on:
- Word choice and vocabulary
- Sentence variety and rhythm
- Show vs tell
- Voice consistency
- Clichés and overused phrases"""

        user_prompt = f"""Edit this text for style:

{content}

{example_context}

Provide:
1. Specific issues found (with examples)
2. Suggested improvements
3. A revised version of the text

Format as:
ISSUES:
[list of issues with line references]

SUGGESTIONS:
[specific recommendations]

REVISED VERSION:
[improved text]"""

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        return self._parse_edit_response(response.content, content)

    def edit_for_pacing(self, content: str, chapter_context: Optional[str] = None) -> Dict[str, Any]:
        """
        Suggest pacing improvements.

        Args:
            content: Content to edit
            chapter_context: Optional context about where this fits in the story

        Returns:
            Dictionary with pacing analysis and suggestions
        """
        system_message = """You are an expert editor focusing on story pacing.
Analyze the text for pacing issues:
- Too much exposition/description slowing action
- Important moments rushed
- Uneven scene length
- Lack of variation between fast and slow sections"""

        user_prompt = f"""Analyze pacing in this text:

{content}

{f'Chapter context: {chapter_context}' if chapter_context else ''}

Provide:
1. Pacing assessment (slow/medium/fast/uneven)
2. Specific pacing problems
3. Recommendations for improvement
4. Optional: revised version if major changes needed

Format as:
PACING: [assessment]
PROBLEMS:
[list of issues]

RECOMMENDATIONS:
[suggestions]

{f'REVISED VERSION:{chr(10)}[improved text]' if len(content) < 1000 else ''}"""

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        return self._parse_pacing_response(response.content)

    def edit_for_grammar(self, content: str) -> Dict[str, Any]:
        """
        Check and correct grammar and mechanics.

        Args:
            content: Content to edit

        Returns:
            Dictionary with grammar corrections
        """
        system_message = """You are a copy editor checking for grammar and mechanics:
- Spelling errors
- Grammar mistakes
- Punctuation issues
- Sentence fragments or run-ons
- Subject-verb agreement
- Tense consistency"""

        user_prompt = f"""Check this text for grammar and mechanical errors:

{content}

Provide:
1. List of errors found (with specific examples)
2. Corrected version

Format as:
ERRORS FOUND:
[list with examples]

CORRECTED VERSION:
[corrected text]"""

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        return self._parse_grammar_response(response.content, content)

    def improve_dialogue(self, dialogue: str, character_names: List[str]) -> Dict[str, Any]:
        """
        Improve dialogue writing.

        Args:
            dialogue: Dialogue text to improve
            character_names: Names of characters in the dialogue

        Returns:
            Dictionary with dialogue improvements
        """
        system_message = """You are an expert at writing natural, engaging dialogue.
Improve dialogue by:
- Making it sound natural and conversational
- Giving each character a distinct voice
- Removing unnecessary dialogue tags
- Adding action beats
- Cutting exposition dumps
- Enhancing subtext"""

        user_prompt = f"""Improve this dialogue between {', '.join(character_names)}:

{dialogue}

Provide:
1. Issues with current dialogue
2. Improved version

Format as:
ISSUES:
[list of problems]

IMPROVED DIALOGUE:
[revised dialogue]"""

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        return self._parse_dialogue_response(response.content)

    def strengthen_opening(self, opening: str, genre: str) -> Dict[str, Any]:
        """
        Improve a chapter or story opening.

        Args:
            opening: Opening text
            genre: Story genre

        Returns:
            Dictionary with improvements
        """
        system_message = f"""You are an expert at crafting compelling openings for {genre} fiction.
A strong opening should:
- Hook the reader immediately
- Establish voice and tone
- Ground the reader in place/character
- Create questions that demand answers
- Avoid common pitfalls (weather, waking up, prologues with no connection)"""

        user_prompt = f"""Improve this opening:

{opening}

Provide:
1. Current strengths
2. Current weaknesses
3. Specific suggestions
4. Revised opening

Format as:
STRENGTHS:
[what works]

WEAKNESSES:
[what needs improvement]

SUGGESTIONS:
[recommendations]

REVISED OPENING:
[improved version]"""

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        return self._parse_opening_response(response.content)

    def compress_text(self, content: str, target_reduction: str = "10-20%") -> Dict[str, Any]:
        """
        Suggest ways to tighten and compress prose.

        Args:
            content: Content to compress
            target_reduction: Target reduction percentage

        Returns:
            Dictionary with compressed version
        """
        system_message = """You are an expert at tightening prose.
Cut unnecessary words while preserving meaning and style:
- Remove redundancies
- Strengthen weak verbs
- Cut filter words (saw, heard, felt, seemed)
- Eliminate unnecessary qualifiers (very, really, quite)
- Replace weak constructions (there is/was, it is/was)"""

        user_prompt = f"""Tighten this text by {target_reduction}:

{content}

Provide:
1. Specific cuts made
2. Compressed version
3. Word count comparison

Format as:
CUTS MADE:
[what was removed/changed and why]

COMPRESSED VERSION:
[tightened text]

WORD COUNT:
Original: [count]
Revised: [count]
Reduction: [percentage]"""

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        return self._parse_compression_response(response.content, content)

    def _parse_edit_response(self, response: str, original: str) -> Dict[str, Any]:
        """Parse style editing response."""
        result = {'original': original, 'issues': [], 'suggestions': [], 'revised': ''}

        current_section = None
        sections = {'issues': [], 'suggestions': [], 'revised': []}

        for line in response.split('\n'):
            line_upper = line.strip().upper()
            if line_upper.startswith('ISSUES:'):
                current_section = 'issues'
            elif line_upper.startswith('SUGGESTIONS:'):
                current_section = 'suggestions'
            elif line_upper.startswith('REVISED VERSION:'):
                current_section = 'revised'
            elif current_section and line.strip():
                sections[current_section].append(line.strip())

        result['issues'] = sections['issues']
        result['suggestions'] = sections['suggestions']
        result['revised'] = '\n'.join(sections['revised'])

        return result

    def _parse_pacing_response(self, response: str) -> Dict[str, Any]:
        """Parse pacing analysis response."""
        result = {'pacing': '', 'problems': [], 'recommendations': [], 'revised': ''}

        current_section = None
        sections = {'problems': [], 'recommendations': [], 'revised': []}

        for line in response.split('\n'):
            line_upper = line.strip().upper()
            if line_upper.startswith('PACING:'):
                result['pacing'] = line.split(':', 1)[1].strip() if ':' in line else ''
            elif line_upper.startswith('PROBLEMS:'):
                current_section = 'problems'
            elif line_upper.startswith('RECOMMENDATIONS:'):
                current_section = 'recommendations'
            elif line_upper.startswith('REVISED VERSION:'):
                current_section = 'revised'
            elif current_section and line.strip():
                sections[current_section].append(line.strip())

        result['problems'] = sections['problems']
        result['recommendations'] = sections['recommendations']
        result['revised'] = '\n'.join(sections['revised'])

        return result

    def _parse_grammar_response(self, response: str, original: str) -> Dict[str, Any]:
        """Parse grammar check response."""
        result = {'original': original, 'errors': [], 'corrected': ''}

        current_section = None
        sections = {'errors': [], 'corrected': []}

        for line in response.split('\n'):
            line_upper = line.strip().upper()
            if 'ERRORS FOUND:' in line_upper or 'ERRORS:' in line_upper:
                current_section = 'errors'
            elif 'CORRECTED VERSION:' in line_upper or 'CORRECTED:' in line_upper:
                current_section = 'corrected'
            elif current_section and line.strip():
                sections[current_section].append(line.strip())

        result['errors'] = sections['errors']
        result['corrected'] = '\n'.join(sections['corrected'])

        return result

    def _parse_dialogue_response(self, response: str) -> Dict[str, Any]:
        """Parse dialogue improvement response."""
        result = {'issues': [], 'improved': ''}

        current_section = None
        sections = {'issues': [], 'improved': []}

        for line in response.split('\n'):
            line_upper = line.strip().upper()
            if 'ISSUES:' in line_upper:
                current_section = 'issues'
            elif 'IMPROVED DIALOGUE:' in line_upper or 'IMPROVED:' in line_upper:
                current_section = 'improved'
            elif current_section and line.strip():
                sections[current_section].append(line.strip())

        result['issues'] = sections['issues']
        result['improved'] = '\n'.join(sections['improved'])

        return result

    def _parse_opening_response(self, response: str) -> Dict[str, Any]:
        """Parse opening improvement response."""
        result = {'strengths': [], 'weaknesses': [], 'suggestions': [], 'revised': ''}

        current_section = None
        sections = {'strengths': [], 'weaknesses': [], 'suggestions': [], 'revised': []}

        for line in response.split('\n'):
            line_upper = line.strip().upper()
            if 'STRENGTHS:' in line_upper:
                current_section = 'strengths'
            elif 'WEAKNESSES:' in line_upper:
                current_section = 'weaknesses'
            elif 'SUGGESTIONS:' in line_upper:
                current_section = 'suggestions'
            elif 'REVISED OPENING:' in line_upper or 'REVISED:' in line_upper:
                current_section = 'revised'
            elif current_section and line.strip():
                sections[current_section].append(line.strip())

        for key in sections:
            if key == 'revised':
                result[key] = '\n'.join(sections[key])
            else:
                result[key] = sections[key]

        return result

    def _parse_compression_response(self, response: str, original: str) -> Dict[str, Any]:
        """Parse text compression response."""
        result = {'original': original, 'cuts': [], 'compressed': '', 'word_count': {}}

        current_section = None
        sections = {'cuts': [], 'compressed': []}

        for line in response.split('\n'):
            line_upper = line.strip().upper()
            if 'CUTS MADE:' in line_upper or 'CUTS:' in line_upper:
                current_section = 'cuts'
            elif 'COMPRESSED VERSION:' in line_upper or 'COMPRESSED:' in line_upper:
                current_section = 'compressed'
            elif 'WORD COUNT:' in line_upper:
                current_section = None
            elif line.strip().startswith('Original:'):
                result['word_count']['original'] = line.split(':', 1)[1].strip()
            elif line.strip().startswith('Revised:'):
                result['word_count']['revised'] = line.split(':', 1)[1].strip()
            elif line.strip().startswith('Reduction:'):
                result['word_count']['reduction'] = line.split(':', 1)[1].strip()
            elif current_section and line.strip():
                sections[current_section].append(line.strip())

        result['cuts'] = sections['cuts']
        result['compressed'] = '\n'.join(sections['compressed'])

        return result
