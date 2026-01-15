"""Context manager for managing conversation context and memory retrieval."""
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document

from .long_term_memory import LongTermMemory


class ContextManager:
    """Manages context window and retrieves relevant information from long-term memory."""

    def __init__(self, memory: LongTermMemory):
        """
        Initialize the context manager.

        Args:
            memory: LongTermMemory instance
        """
        self.memory = memory
        self.current_context = {
            "characters": [],
            "plot": None,
            "settings": [],
            "current_chapter": None,
            "outline": None
        }

    def build_context_for_task(self, task_type: str, query: str, k: int = 5) -> str:
        """
        Build relevant context for a specific task.

        Args:
            task_type: Type of task (brainstorm, character, plot, writing, etc.)
            query: Specific query or focus
            k: Number of relevant documents to retrieve

        Returns:
            Formatted context string
        """
        context_parts = []

        if task_type == "brainstorm":
            # For brainstorming, retrieve any existing plot ideas
            docs = self.memory.retrieve_context(query, k=3, filter_type="plot")
            if docs:
                context_parts.append("=== Existing Plot Ideas ===")
                for doc in docs:
                    context_parts.append(doc.page_content)

        elif task_type == "character":
            # Retrieve existing characters for consistency
            docs = self.memory.get_all_characters()
            if docs:
                context_parts.append("=== Existing Characters ===")
                for doc in docs:
                    context_parts.append(doc.page_content)

        elif task_type == "writing":
            # Retrieve all relevant context for writing
            # 1. Plot summary
            plot = self.memory.get_plot_summary()
            if plot:
                context_parts.append("=== Plot Summary ===")
                context_parts.append(plot.page_content)

            # 2. Characters
            characters = self.memory.get_all_characters()
            if characters:
                context_parts.append("\n=== Characters ===")
                for char in characters[:5]:  # Limit to 5 most relevant
                    context_parts.append(char.page_content)

            # 3. Settings
            settings = self.memory.retrieve_by_type("setting", k=3)
            if settings:
                context_parts.append("\n=== Settings ===")
                for setting in settings:
                    context_parts.append(setting.page_content)

            # 4. Recent chapters for context
            recent_chapters = self.memory.retrieve_context(query, k=2, filter_type="chapter")
            if recent_chapters:
                context_parts.append("\n=== Recent Context ===")
                for chapter in recent_chapters:
                    context_parts.append(chapter.page_content[:500] + "...")

        elif task_type == "editing":
            # Retrieve the specific content being edited
            docs = self.memory.retrieve_context(query, k=3)
            if docs:
                context_parts.append("=== Content to Edit ===")
                for doc in docs:
                    context_parts.append(doc.page_content)

        elif task_type == "consistency":
            # Retrieve all relevant story elements
            characters = self.memory.get_all_characters()
            settings = self.memory.retrieve_by_type("setting", k=5)
            plot = self.memory.get_plot_summary()

            if plot:
                context_parts.append("=== Plot ===")
                context_parts.append(plot.page_content)

            if characters:
                context_parts.append("\n=== Characters ===")
                for char in characters:
                    context_parts.append(char.page_content)

            if settings:
                context_parts.append("\n=== Settings ===")
                for setting in settings:
                    context_parts.append(setting.page_content)

        return "\n\n".join(context_parts) if context_parts else "No relevant context found."

    def update_current_context(self, key: str, value: Any):
        """
        Update the current working context.

        Args:
            key: Context key (characters, plot, settings, etc.)
            value: Value to set
        """
        if key in self.current_context:
            self.current_context[key] = value

    def get_current_context(self, key: str) -> Any:
        """
        Get current context value.

        Args:
            key: Context key

        Returns:
            Context value
        """
        return self.current_context.get(key)

    def get_full_story_context(self) -> Dict[str, Any]:
        """
        Get complete story context including all stored information.

        Returns:
            Dictionary with all story elements
        """
        return {
            "plot": self.memory.get_plot_summary(),
            "characters": self.memory.get_all_characters(),
            "settings": self.memory.retrieve_by_type("setting", k=10),
            "outline": self.memory.retrieve_by_type("outline", k=1),
            "chapters": self.memory.get_all_chapters()
        }

    def format_context_summary(self) -> str:
        """
        Format a human-readable summary of the current story context.

        Returns:
            Formatted summary string
        """
        story_context = self.get_full_story_context()
        summary_parts = []

        # Plot
        if story_context["plot"]:
            summary_parts.append("=== PLOT ===")
            summary_parts.append(story_context["plot"].page_content)

        # Characters
        if story_context["characters"]:
            summary_parts.append("\n=== CHARACTERS ===")
            for i, char in enumerate(story_context["characters"], 1):
                summary_parts.append(f"\n{i}. {char.page_content.split(':')[1].split('Age')[0].strip() if ':' in char.page_content else 'Unknown'}")

        # Settings
        if story_context["settings"]:
            summary_parts.append("\n=== SETTINGS ===")
            for i, setting in enumerate(story_context["settings"], 1):
                summary_parts.append(f"\n{i}. {setting.page_content.split(':')[1].split('Time')[0].strip() if ':' in setting.page_content else 'Unknown'}")

        # Outline
        if story_context["outline"]:
            summary_parts.append("\n=== OUTLINE ===")
            summary_parts.append(story_context["outline"][0].page_content if story_context["outline"] else "")

        # Chapters
        if story_context["chapters"]:
            summary_parts.append(f"\n=== CHAPTERS ({len(story_context['chapters'])}) ===")

        return "\n".join(summary_parts) if summary_parts else "No story context available yet."
