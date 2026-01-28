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

