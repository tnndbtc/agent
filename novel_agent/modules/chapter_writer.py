"""Chapter writing module for generating novel content paragraph by paragraph."""
from typing import Dict, Any, Optional, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from novel_agent.config import OPENAI_API_KEY, MODEL_NAME, TEMPERATURE, MAX_TOKENS
from novel_agent.memory.context_manager import ContextManager
from novel_agent.memory.long_term_memory import LongTermMemory
from novel_agent.data.example_manager import ExampleManager


class ChapterWriter:
    """Generates novel chapters paragraph by paragraph."""

    def __init__(
        self,
        context_manager: ContextManager,
        memory: LongTermMemory,
        example_manager: ExampleManager
    ):
        """
        Initialize the chapter writer.

        Args:
            context_manager: ContextManager instance
            memory: LongTermMemory instance
            example_manager: ExampleManager instance
        """
        self.context_manager = context_manager
        self.memory = memory
        self.example_manager = example_manager
        self.llm = ChatOpenAI(
            model=MODEL_NAME,
            temperature=TEMPERATURE + 0.2,  # Higher for creative writing
            max_tokens=MAX_TOKENS,
            openai_api_key=OPENAI_API_KEY
        )

    def write_chapter(
        self,
        chapter_outline: Dict[str, Any],
        writing_style: str = "literary",
        language: str = "English",
        target_word_count: int = 3000,
        example_metadata: Optional[Dict[str, Any]] = None,
        iteration: int = 1,
        previous_scores: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Write a complete chapter based on the outline with optional quality targeting.

        Args:
            chapter_outline: Chapter outline dictionary
            writing_style: Style preference (literary, commercial, minimalist, etc.)
            language: Target language
            target_word_count: Target word count for the chapter (default: 3000)
            example_metadata: Optional dict with 'category', 'genre', 'total_score', 'scores' (NO content!)
            iteration: Current iteration number (1 for first attempt)
            previous_scores: Previous iteration scores for gap analysis

        Returns:
            Complete chapter dictionary with content
        """
        # Get relevant context
        context = self.context_manager.build_context_for_task(
            "writing",
            f"Chapter {chapter_outline.get('number', 1)}"
        )

        # Use example metadata if provided (metadata only, NO content!)
        example_context = ""
        if example_metadata:
            example_context = self._prepare_example_context(
                example_metadata,
                iteration=iteration,
                previous_scores=previous_scores
            )
        else:
            # Fallback to file-based examples (old behavior)
            good_examples = self.example_manager.get_good_examples(category="writing", limit=2)
            if good_examples:
                example_context = "\n\nGood writing examples to emulate:\n"
                for ex in good_examples:
                    example_context += f"\n{ex['content'][:500]}...\n"

        # Generate the chapter in sections
        scenes = self._generate_scene_breakdown(chapter_outline)
        chapter_content = []

        # Initialize token usage accumulator
        total_tokens_used = {
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0
        }

        # Calculate words per scene to meet target word count
        num_scenes = len(scenes)
        words_per_scene = target_word_count // num_scenes if num_scenes > 0 else target_word_count

        for i, scene in enumerate(scenes):
            scene_content, scene_tokens = self._write_scene(
                scene,
                chapter_outline,
                context,
                example_context,
                writing_style,
                language,
                target_words=words_per_scene,
                is_first=i == 0,
                is_last=i == len(scenes) - 1
            )
            chapter_content.append(scene_content)

            # Accumulate scene tokens
            if scene_tokens:
                total_tokens_used['prompt_tokens'] += scene_tokens.get('prompt_tokens', 0)
                total_tokens_used['completion_tokens'] += scene_tokens.get('completion_tokens', 0)
                total_tokens_used['total_tokens'] += scene_tokens.get('total_tokens', 0)

        full_content = "\n\n".join(chapter_content)

        # Generate chapter summary and accumulate its tokens
        summary, summary_tokens = self._generate_chapter_summary(full_content)
        if summary_tokens:
            total_tokens_used['prompt_tokens'] += summary_tokens.get('prompt_tokens', 0)
            total_tokens_used['completion_tokens'] += summary_tokens.get('completion_tokens', 0)
            total_tokens_used['total_tokens'] += summary_tokens.get('total_tokens', 0)

        chapter = {
            'chapter_number': chapter_outline.get('number', 1),
            'title': chapter_outline.get('title', 'Untitled'),
            'content': full_content,
            'summary': summary,
            'word_count': len(full_content.split()),
            'language': language
        }

        # Store in memory
        self.memory.store_chapter(chapter)

        return chapter, total_tokens_used

    def write_paragraph(
        self,
        scene_context: str,
        previous_paragraph: Optional[str] = None,
        writing_style: str = "literary",
        language: str = "English"
    ) -> str:
        """
        Write a single paragraph.

        Args:
            scene_context: Context for the scene
            previous_paragraph: Previous paragraph for continuity
            writing_style: Writing style
            language: Target language

        Returns:
            Generated paragraph
        """
        system_message = f"""You are a skilled novelist writing in {language}.
Your writing style is {writing_style}.
Write vivid, engaging prose that shows rather than tells.
Use strong verbs, sensory details, and varied sentence structure."""

        user_prompt = f"""Scene context: {scene_context}

{f'Previous paragraph: {previous_paragraph}' if previous_paragraph else ''}

Write the next paragraph (3-5 sentences) that continues the scene naturally."""

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        return response.content.strip()

    def write_dialogue(
        self,
        characters: List[str],
        context: str,
        purpose: str,
        language: str = "English"
    ) -> str:
        """
        Write a dialogue scene between characters.

        Args:
            characters: List of character names in the dialogue
            context: Scene context
            purpose: Purpose of the dialogue
            language: Target language

        Returns:
            Dialogue text
        """
        # Get character information from memory
        char_context = []
        for char_name in characters:
            char_docs = self.memory.retrieve_context(char_name, k=1, filter_type="character")
            if char_docs:
                char_context.append(char_docs[0].page_content)

        system_message = f"""You are writing dialogue in {language}.
Create natural, character-specific dialogue that reveals personality.
Use proper dialogue formatting with speech tags and action beats.
Each character should have a distinct voice."""

        user_prompt = f"""Write a dialogue scene between: {', '.join(characters)}

Character information:
{chr(10).join(char_context)}

Scene context: {context}
Dialogue purpose: {purpose}

Write 5-10 exchanges that accomplish the purpose while revealing character."""

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        return response.content.strip()

    def write_description(
        self,
        subject: str,
        description_type: str,
        mood: str,
        language: str = "English"
    ) -> str:
        """
        Write a descriptive passage.

        Args:
            subject: What to describe (setting, character, object, etc.)
            description_type: Type (setting, character appearance, action, etc.)
            mood: Desired mood/atmosphere
            language: Target language

        Returns:
            Descriptive text
        """
        system_message = f"""You are writing descriptive prose in {language}.
Create vivid, immersive descriptions using sensory details.
Match the {mood} mood through word choice and imagery."""

        # Get relevant setting/character info from memory
        context_docs = self.memory.retrieve_context(subject, k=1)
        context_info = context_docs[0].page_content if context_docs else ""

        user_prompt = f"""Write a description of: {subject}
Type: {description_type}
Mood: {mood}

{f'Reference information: {context_info}' if context_info else ''}

Write 2-3 paragraphs of evocative description."""

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        return response.content.strip()

    def _prepare_example_context(
        self,
        example_metadata: Dict[str, Any],
        iteration: int = 1,
        previous_scores: Optional[Dict] = None
    ) -> str:
        """
        Prepare example context using ONLY metadata (no content).

        Args:
            example_metadata: Dict with 'category', 'genre', 'total_score', 'scores' (list of dicts)
            iteration: Current iteration number (1 for first attempt)
            previous_scores: Previous iteration scores for gap analysis

        Returns:
            Formatted context string with metadata only
        """
        if not example_metadata:
            return ""

        context_parts = ["\n\nQuality Target from Example:"]

        # Add basic metadata
        if example_metadata.get('category'):
            context_parts.append(f"Category: {example_metadata['category']}")
        if example_metadata.get('genre'):
            context_parts.append(f"Genre: {example_metadata['genre']}")

        # Add total score target
        total_score = example_metadata.get('total_score', 0)
        context_parts.append(f"Target Total Score: {total_score:.1f}/10")

        # Show individual category scores
        scores = example_metadata.get('scores', [])
        if scores:
            context_parts.append("\nScore Targets by Category:")
            for score in scores:
                category_name = score.get('category_name', 'Unknown')
                score_value = score.get('score', 0)
                weight = score.get('weight', 0)
                context_parts.append(
                    f"- {category_name}: {score_value:.1f}/10 (weight: {weight}%)"
                )

        # Add gap analysis for iterations after the first
        if iteration > 1 and previous_scores:
            context_parts.append(f"\n\nYour Previous Attempt (Iteration {iteration - 1}):")
            context_parts.append(f"Score Achieved: {previous_scores.get('total', 0):.1f}/10")
            context_parts.append(f"Target Score: {total_score:.1f}/10")
            gap = total_score - previous_scores.get('total', 0)
            context_parts.append(f"Gap to Close: {gap:.1f} points")

            # Show category-level gaps if available
            if previous_scores.get('by_category'):
                context_parts.append("\nGaps by Category:")
                for cat_score in previous_scores['by_category']:
                    cat_name = cat_score.get('category_name', 'Unknown')
                    achieved = cat_score.get('score', 0)
                    # Find target for this category
                    target_score = next(
                        (s['score'] for s in scores if s.get('category_name') == cat_name),
                        0
                    )
                    cat_gap = target_score - achieved
                    if cat_gap > 0:
                        context_parts.append(f"- {cat_name}: Need +{cat_gap:.1f} points")

        return "\n".join(context_parts)

    def _generate_scene_breakdown(self, chapter_outline: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate basic scene breakdown if not provided."""
        events = chapter_outline.get('events', '')

        system_message = """Break down chapter events into 3-5 distinct scenes.
Each scene should have a clear beginning, middle, and end."""

        user_prompt = f"""Chapter {chapter_outline.get('number', 1)}: {chapter_outline.get('title', '')}
Events: {events}
Setting: {chapter_outline.get('setting', '')}
POV: {chapter_outline.get('pov', '')}

Break this into 3-5 scenes. For each provide:
SCENE [number]: [brief description]"""

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)

        # Simple parsing - just split into scenes
        scenes = []
        lines = response.content.split('\n')
        for line in lines:
            if line.strip().startswith('SCENE'):
                scenes.append({
                    'description': line.strip(),
                    'setting': chapter_outline.get('setting', ''),
                    'pov': chapter_outline.get('pov', '')
                })

        return scenes if scenes else [{'description': events, 'setting': chapter_outline.get('setting', ''), 'pov': chapter_outline.get('pov', '')}]

    def _write_scene(
        self,
        scene: Dict[str, str],
        chapter_outline: Dict[str, Any],
        story_context: str,
        example_context: str,
        writing_style: str,
        language: str,
        target_words: int = 600,
        is_first: bool = False,
        is_last: bool = False
    ) -> str:
        """Write a complete scene."""
        system_message = f"""You are a skilled novelist writing in {language}.
Your style is {writing_style}.
Write engaging, vivid prose with:
- Strong sensory details
- Active voice
- Varied sentence structure
- Character-driven narrative
- Natural pacing

Show, don't tell. Make the reader feel present in the scene.

CRITICAL: You MUST write EXACTLY around {target_words} words. Not more, not less.
Count your words carefully and stop when you reach approximately {target_words} words."""

        user_prompt = f"""Write this scene:

{scene.get('description', '')}

Chapter context:
- Chapter {chapter_outline.get('number', 1)}: {chapter_outline.get('title', '')}
- POV: {scene.get('pov', 'Third person')}
- Setting: {scene.get('setting', '')}
- Character development: {chapter_outline.get('character_development', '')}

Story context:
{story_context[:1500]}

{example_context[:500] if example_context else ''}

{'This is the opening scene of the chapter. Create a strong hook.' if is_first else ''}
{'This is the closing scene of the chapter. End with impact or a cliffhanger.' if is_last else ''}

WORD COUNT REQUIREMENT: Write EXACTLY {target_words} words (±10 words tolerance).
This is NOT a suggestion - it is a strict requirement.
After writing, count your words and adjust if needed to meet this target.

Write polished prose that meets the {target_words}-word target."""

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)

        # Extract token usage
        token_usage = {}
        if hasattr(response, 'response_metadata') and 'token_usage' in response.response_metadata:
            usage = response.response_metadata['token_usage']
            token_usage = {
                'prompt_tokens': usage.get('prompt_tokens', 0),
                'completion_tokens': usage.get('completion_tokens', 0),
                'total_tokens': usage.get('total_tokens', 0)
            }
        elif hasattr(response, 'usage_metadata'):
            token_usage = {
                'prompt_tokens': getattr(response.usage_metadata, 'input_tokens', 0),
                'completion_tokens': getattr(response.usage_metadata, 'output_tokens', 0),
                'total_tokens': getattr(response.usage_metadata, 'total_tokens', 0)
            }

        return response.content.strip(), token_usage

    def _generate_chapter_summary(self, content: str) -> str:
        """Generate a summary of the chapter content."""
        system_message = """You are summarizing a chapter.
Provide a concise summary of key events and character development."""

        user_prompt = f"""Summarize this chapter in 2-3 sentences:

{content[:2000]}...

Focus on plot progression and character changes."""

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)

        # Extract token usage
        token_usage = {}
        if hasattr(response, 'response_metadata') and 'token_usage' in response.response_metadata:
            usage = response.response_metadata['token_usage']
            token_usage = {
                'prompt_tokens': usage.get('prompt_tokens', 0),
                'completion_tokens': usage.get('completion_tokens', 0),
                'total_tokens': usage.get('total_tokens', 0)
            }
        elif hasattr(response, 'usage_metadata'):
            token_usage = {
                'prompt_tokens': getattr(response.usage_metadata, 'input_tokens', 0),
                'completion_tokens': getattr(response.usage_metadata, 'output_tokens', 0),
                'total_tokens': getattr(response.usage_metadata, 'total_tokens', 0)
            }

        return response.content.strip(), token_usage

    def continue_from_draft(
        self,
        existing_content: str,
        chapter_outline: Dict[str, Any],
        language: str = "English"
    ) -> str:
        """
        Continue writing from an existing draft.

        Args:
            existing_content: Existing chapter content
            chapter_outline: Chapter outline
            language: Target language

        Returns:
            Additional content
        """
        context = self.context_manager.build_context_for_task(
            "writing",
            chapter_outline.get('title', '')
        )

        system_message = f"""You are continuing a chapter draft in {language}.
Maintain consistency with the existing style and continue the narrative smoothly."""

        user_prompt = f"""Existing content:
{existing_content[-1000:]}

Chapter outline:
Events: {chapter_outline.get('events', '')}
Setting: {chapter_outline.get('setting', '')}

Story context:
{context[:1000]}

Continue writing the chapter. Add 3-5 paragraphs."""

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        return response.content.strip()
