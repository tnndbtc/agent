"""Brainstorming module for generating creative plot ideas."""
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from novel_agent.config import OPENAI_API_KEY, MODEL_NAME, TEMPERATURE
from novel_agent.memory.context_manager import ContextManager


class BrainstormingModule:
    """Generates creative plot ideas and story concepts."""

    def __init__(self, context_manager: ContextManager):
        """
        Initialize the brainstorming module.

        Args:
            context_manager: ContextManager instance
        """
        self.context_manager = context_manager
        self.llm = ChatOpenAI(
            model=MODEL_NAME,
            temperature=TEMPERATURE,
            openai_api_key=OPENAI_API_KEY
        )

    def generate_plot_ideas(
        self,
        genre: Optional[str] = None,
        theme: Optional[str] = None,
        num_ideas: int = 3,
        custom_prompt: Optional[str] = None,
        use_context: bool = False
    ) -> List[Dict[str, str]]:
        """
        Generate multiple plot ideas for the user to choose from.

        Args:
            genre: Desired genre (e.g., fantasy, sci-fi, romance)
            theme: Desired theme (e.g., redemption, revenge, love)
            num_ideas: Number of ideas to generate
            custom_prompt: Optional custom prompt from user
            use_context: Whether to retrieve existing context from memory (default: False for speed)

        Returns:
            List of plot idea dictionaries
        """
        # Build context from memory (optional for performance)
        context = None
        if use_context:
            context = self.context_manager.build_context_for_task("brainstorm", "plot ideas")

        # Create the prompt
        system_message = """You are a creative writing assistant specializing in generating unique and engaging plot ideas.
Generate diverse, original story ideas that are compelling and suitable for a full-length novel.
Each idea should include:
1. A catchy title
2. A brief premise (2-3 sentences)
3. Main conflict
4. Unique hook or twist

Make each idea distinctly different from the others."""

        user_prompt_parts = []

        if custom_prompt:
            user_prompt_parts.append(f"User's request: {custom_prompt}")

        if genre:
            user_prompt_parts.append(f"Genre: {genre}")

        if theme:
            user_prompt_parts.append(f"Theme: {theme}")

        user_prompt_parts.append(f"\nGenerate {num_ideas} distinct plot ideas.")

        if context:
            user_prompt_parts.append(f"\n\nExisting context (avoid duplicating):\n{context}")

        user_prompt_parts.append(f"\n\nFormat each idea as:\n---\nIDEA [number]\nTitle: [title]\nPremise: [premise]\nConflict: [conflict]\nHook: [unique hook]\n---")

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content="\n".join(user_prompt_parts))
        ]

        response = self.llm.invoke(messages)
        ideas = self._parse_plot_ideas(response.content)

        return ideas

    def refine_plot_idea(self, plot_idea: Dict[str, str], user_feedback: str) -> Dict[str, str]:
        """
        Refine a plot idea based on user feedback.

        Args:
            plot_idea: The plot idea to refine
            user_feedback: User's feedback or modification requests

        Returns:
            Refined plot idea dictionary
        """
        system_message = """You are a creative writing assistant helping to refine plot ideas.
Take the user's feedback and improve the plot idea accordingly while maintaining its core essence."""

        user_prompt = f"""Original plot idea:
Title: {plot_idea.get('title', 'Untitled')}
Premise: {plot_idea.get('premise', '')}
Conflict: {plot_idea.get('conflict', '')}
Hook: {plot_idea.get('hook', '')}

User feedback: {user_feedback}

Please refine this plot idea based on the feedback. Provide the refined version in the same format:
Title: [title]
Premise: [premise]
Conflict: [conflict]
Hook: [hook]"""

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        refined_ideas = self._parse_plot_ideas(response.content)

        return refined_ideas[0] if refined_ideas else plot_idea

    def expand_plot_idea(self, plot_idea: Dict[str, str]) -> Dict[str, Any]:
        """
        Expand a plot idea into more detailed elements.

        Args:
            plot_idea: The plot idea to expand

        Returns:
            Expanded plot dictionary with additional details
        """
        system_message = """You are a creative writing assistant helping to expand plot ideas into detailed story structures.
Provide comprehensive details that will serve as the foundation for a full novel."""

        user_prompt = f"""Plot idea:
Title: {plot_idea.get('title', 'Untitled')}
Premise: {plot_idea.get('premise', '')}
Conflict: {plot_idea.get('conflict', '')}
Hook: {plot_idea.get('hook', '')}

Expand this into a detailed plot structure including:
1. Genre and subgenre
2. Extended premise (one paragraph)
3. Main themes (2-3)
4. Story arc overview (beginning, middle, end)
5. Target audience
6. Tone and atmosphere

Format your response as:
Genre: [genre]
Premise: [extended premise paragraph]
Themes: [theme 1, theme 2, theme 3]
Story Arc: [arc overview]
Target Audience: [audience]
Tone: [tone and atmosphere]"""

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        expanded = self._parse_expanded_plot(response.content, plot_idea)

        return expanded

    def brainstorm_with_constraints(
        self,
        must_have: List[str],
        must_avoid: List[str],
        num_ideas: int = 3
    ) -> List[Dict[str, str]]:
        """
        Generate plot ideas with specific constraints.

        Args:
            must_have: Elements that must be included
            must_avoid: Elements to avoid
            num_ideas: Number of ideas to generate

        Returns:
            List of plot idea dictionaries
        """
        system_message = """You are a creative writing assistant generating plot ideas with specific constraints.
Be creative while adhering to the requirements."""

        user_prompt = f"""Generate {num_ideas} plot ideas with the following constraints:

MUST INCLUDE:
{chr(10).join(f'- {item}' for item in must_have)}

MUST AVOID:
{chr(10).join(f'- {item}' for item in must_avoid)}

Format each idea as:
---
IDEA [number]
Title: [title]
Premise: [premise]
Conflict: [conflict]
Hook: [unique hook]
---"""

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        ideas = self._parse_plot_ideas(response.content)

        return ideas

    def _parse_plot_ideas(self, response_text: str) -> List[Dict[str, str]]:
        """Parse LLM response into structured plot ideas."""
        ideas = []
        current_idea = {}

        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()

            if line.startswith('Title:'):
                if current_idea:
                    ideas.append(current_idea)
                current_idea = {'title': line.replace('Title:', '').strip()}
            elif line.startswith('Premise:'):
                current_idea['premise'] = line.replace('Premise:', '').strip()
            elif line.startswith('Conflict:'):
                current_idea['conflict'] = line.replace('Conflict:', '').strip()
            elif line.startswith('Hook:'):
                current_idea['hook'] = line.replace('Hook:', '').strip()
            elif 'premise' in current_idea and not line.startswith(('Title:', 'Conflict:', 'Hook:', 'IDEA', '---', '')):
                # Continue multi-line premise
                current_idea['premise'] += ' ' + line

        if current_idea:
            ideas.append(current_idea)

        return ideas

    def _parse_expanded_plot(self, response_text: str, original_idea: Dict[str, str]) -> Dict[str, Any]:
        """Parse expanded plot response into structured format."""
        expanded = {
            'title': original_idea.get('title', 'Untitled'),
            'original_premise': original_idea.get('premise', ''),
            'conflict': original_idea.get('conflict', ''),
            'hook': original_idea.get('hook', '')
        }

        lines = response_text.split('\n')
        current_key = None

        for line in lines:
            line = line.strip()

            if line.startswith('Genre:'):
                expanded['genre'] = line.replace('Genre:', '').strip()
                current_key = 'genre'
            elif line.startswith('Premise:'):
                expanded['premise'] = line.replace('Premise:', '').strip()
                current_key = 'premise'
            elif line.startswith('Themes:'):
                expanded['themes'] = line.replace('Themes:', '').strip()
                current_key = 'themes'
            elif line.startswith('Story Arc:'):
                expanded['arc'] = line.replace('Story Arc:', '').strip()
                current_key = 'arc'
            elif line.startswith('Target Audience:'):
                expanded['audience'] = line.replace('Target Audience:', '').strip()
                current_key = 'audience'
            elif line.startswith('Tone:'):
                expanded['tone'] = line.replace('Tone:', '').strip()
                current_key = 'tone'
            elif current_key and line and not line.startswith(('Genre:', 'Premise:', 'Themes:', 'Story Arc:', 'Target Audience:', 'Tone:')):
                # Continue multi-line content
                expanded[current_key] += ' ' + line

        return expanded
