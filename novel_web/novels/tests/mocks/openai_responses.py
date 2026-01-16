"""
Mock OpenAI responses for integration testing.
All responses use hardcoded strings to avoid real API calls.
"""

import random
import string


def generate_random_text(words=50):
    """Generate random text with specified number of words."""
    word_list = ['the', 'a', 'an', 'and', 'but', 'or', 'for', 'nor', 'on', 'at', 'to', 'from',
                 'hero', 'journey', 'adventure', 'magic', 'sword', 'castle', 'dragon', 'quest',
                 'brave', 'dark', 'light', 'powerful', 'mysterious', 'ancient', 'forbidden',
                 'destiny', 'prophecy', 'battle', 'victory', 'defeat', 'challenge', 'triumph']

    return ' '.join(random.choice(word_list) for _ in range(words))


class MockOpenAIResponses:
    """Centralized mock responses for different OpenAI API calls."""

    @staticmethod
    def brainstorm_response(num_ideas=1):
        """Mock response for brainstorm ideas generation."""
        ideas = []
        for i in range(num_ideas):
            ideas.append(f"""
---
IDEA {i + 1}
Title: Test Novel Idea {i + 1}
Premise: A brave hero embarks on a journey to save the world from darkness.
Conflict: The forces of evil threaten to destroy everything the hero holds dear.
Hook: In a world where magic is forbidden, one person must master it to survive.
---
""")
        return '\n'.join(ideas)

    @staticmethod
    def plot_response():
        """Mock response for plot creation."""
        return """
{
  "title": "The Hero's Journey",
  "premise": "A young hero must save the world from an ancient evil",
  "main_conflict": "Good versus evil in an epic battle for survival",
  "setting_overview": "A fantasy world with magic and dragons",
  "act_one": {
    "description": "Introduction to the hero and their ordinary world",
    "key_events": ["Hero discovers their destiny", "Meets the mentor", "Receives the call to adventure"],
    "turning_point": "Hero accepts the quest and leaves home"
  },
  "act_two": {
    "description": "Hero faces challenges and grows stronger",
    "key_events": ["Faces first major challenge", "Learns new skills", "Encounters the antagonist"],
    "turning_point": "Hero suffers a major setback"
  },
  "act_three": {
    "description": "Final confrontation and resolution",
    "key_events": ["Hero overcomes final challenge", "Defeats the antagonist", "Returns home transformed"],
    "resolution": "The world is saved and peace is restored"
  },
  "themes": ["courage", "sacrifice", "redemption"],
  "pacing": "fast-paced with moments of reflection"
}
"""

    @staticmethod
    def protagonist_response():
        """Mock response for protagonist creation."""
        return """
---
PROTAGONIST 1
Name: Aria Stormwind
Age: 24
Background: Raised in a small village by her grandmother after her parents disappeared mysteriously
Personality: Brave, determined, sometimes impulsive but with a good heart
Motivation: Find out what happened to her parents and master her magical powers
Flaw: Trusts too easily and fears losing loved ones
Arc: Learns to trust herself and accept her destiny
Fit: Perfect protagonist for a fantasy adventure with magical elements
---
"""

    @staticmethod
    def antagonist_response():
        """Mock response for antagonist creation."""
        return """
---
ANTAGONIST
Name: Lord Malkor
Age: 45
Background: Once a noble wizard who turned to dark magic after losing everything
Personality: Calculating, ruthless, believes the end justifies the means
Motivation: Believes he's bringing order through his actions and gaining ultimate power
Flaw: Consumed by revenge and underestimates his opponents
Arc: Refuses to change and ultimately falls to his own darkness
Fit: Perfect antagonist who represents what the protagonist could become
---
"""

    @staticmethod
    def supporting_character_response(character_type="mentor"):
        """Mock response for supporting character creation."""
        characters = {
            "mentor": {
                "name": "Master Eldrin",
                "role": "supporting",
                "background": "An ancient wizard who has guided heroes for centuries",
                "personality": "Wise, patient, sometimes cryptic in his teachings"
            },
            "sidekick": {
                "name": "Finn Quickfoot",
                "role": "supporting",
                "background": "A clever rogue with a heart of gold",
                "personality": "Humorous, loyal, always ready with a quip"
            },
            "love_interest": {
                "name": "Prince Kael",
                "role": "supporting",
                "background": "A noble prince who fights alongside the hero",
                "personality": "Charming, brave, believes in justice"
            }
        }

        char_data = characters.get(character_type, characters["sidekick"])
        return f"""
{{
  "name": "{char_data['name']}",
  "role": "{char_data['role']}",
  "background": "{char_data['background']}",
  "personality": "{char_data['personality']}",
  "relationship_to_protagonist": "Important ally in the hero's journey"
}}
"""

    @staticmethod
    def chapter_outline_response(chapter_number=1, total_chapters=20):
        """Mock response for single chapter outline creation."""
        return f"""---
CHAPTER {chapter_number}: The Beginning
POV: Third person limited
Setting: The hero's village
Events: The hero goes about their normal life until something extraordinary happens that changes everything
Character Development: Hero is established as ordinary but with hidden potential
Pacing: medium
Story Beats: Introduces the inciting incident that starts the adventure
---"""

    @staticmethod
    def full_outline_response(num_chapters=3):
        """Mock response for complete outline generation."""
        chapters = []
        for i in range(1, num_chapters + 1):
            chapters.append(f"""---
CHAPTER {i}: Chapter {i} - The Journey Continues
POV: Third person
Setting: Various locations on the hero's path
Events: The hero faces challenge number {i} and overcomes it through courage and skill
Character Development: The hero learns an important lesson about themselves
Pacing: {'fast' if i % 2 == 0 else 'medium'}
Story Beats: Major plot point {i} occurs
---""")
        return '\n'.join(chapters)

    @staticmethod
    def chapter_content_response(chapter_number=1, word_count=100):
        """Mock response for chapter writing."""
        # Generate chapter content with approximate word count
        intro = f"Chapter {chapter_number}\n\n"

        paragraphs = []
        words_per_paragraph = max(30, word_count // 3)

        paragraphs.append(
            f"The sun rose over the horizon, casting golden light across the landscape. "
            f"{generate_random_text(words_per_paragraph)}"
        )

        paragraphs.append(
            f"As our hero continued their journey, they reflected on everything that had brought them to this moment. "
            f"{generate_random_text(words_per_paragraph)}"
        )

        paragraphs.append(
            f"The challenge ahead was daunting, but they knew there was no turning back now. "
            f"{generate_random_text(words_per_paragraph)}"
        )

        content = intro + '\n\n'.join(paragraphs)
        return content

    @staticmethod
    def setting_response():
        """Mock response for setting creation."""
        return """
{
  "name": "The Kingdom of Eldoria",
  "type": "Fantasy medieval kingdom",
  "description": "A vast kingdom with towering castles, dark forests, and ancient ruins",
  "atmosphere": "Mystical and dangerous, where magic lurks in every shadow",
  "key_locations": ["The Royal Castle", "The Forbidden Forest", "The Ancient Ruins"],
  "culture": "Noble houses compete for power while common folk struggle to survive",
  "rules": "Magic is forbidden by royal decree, but still practiced in secret"
}
"""

    @staticmethod
    def consistency_check_response():
        """Mock response for consistency checking."""
        return """
{
  "character_consistency": {
    "issues": [],
    "status": "pass"
  },
  "setting_consistency": {
    "issues": [],
    "status": "pass"
  },
  "plot_consistency": {
    "issues": [],
    "status": "pass"
  },
  "overall_status": "pass",
  "message": "No consistency issues detected"
}
"""

    @staticmethod
    def score_response():
        """Mock response for novel scoring."""
        return """
{
  "overall_score": 85,
  "categories": {
    "plot": 88,
    "characters": 90,
    "writing_style": 82,
    "pacing": 85,
    "world_building": 83
  },
  "strengths": ["Strong character development", "Engaging plot"],
  "weaknesses": ["Some pacing issues in middle chapters"],
  "recommendations": ["Tighten the middle act", "Add more world-building details"]
}
"""


def get_mock_response_for_prompt(prompt_text):
    """
    Determine which mock response to return based on prompt content.

    Args:
        prompt_text: The prompt text sent to the LLM

    Returns:
        str: Appropriate mock response
    """
    import re

    prompt_lower = prompt_text.lower()

    # Brainstorm/Ideas
    if 'brainstorm' in prompt_lower or 'plot idea' in prompt_lower:
        return MockOpenAIResponses.brainstorm_response()

    # Outlines - CHECK THESE FIRST before plot since they contain "chapter"
    elif 'outline for chapter' in prompt_lower or ('chapter' in prompt_lower and 'regenerate' in prompt_lower):
        # Single chapter outline - extract chapter number from prompt
        match = re.search(r'chapter\s+(\d+)', prompt_lower)
        chapter_number = int(match.group(1)) if match else 1
        return MockOpenAIResponses.chapter_outline_response(chapter_number=chapter_number)
    elif 'chapter-by-chapter' in prompt_lower or ('outline' in prompt_lower and 'chapter' in prompt_lower):
        # Full multi-chapter outline - extract num_chapters from prompt
        match = re.search(r'(\d+)-chapter outline', prompt_lower)
        if not match:
            # Try alternative patterns
            match = re.search(r'create.*?(\d+)\s+chapter', prompt_lower)
        num_chapters = int(match.group(1)) if match else 3
        return MockOpenAIResponses.full_outline_response(num_chapters=num_chapters)

    # Plot creation
    elif 'plot structure' in prompt_lower or 'three-act' in prompt_lower:
        return MockOpenAIResponses.plot_response()

    # Characters
    elif 'protagonist' in prompt_lower:
        return MockOpenAIResponses.protagonist_response()
    elif 'antagonist' in prompt_lower:
        return MockOpenAIResponses.antagonist_response()
    elif 'supporting character' in prompt_lower or 'sidekick' in prompt_lower:
        return MockOpenAIResponses.supporting_character_response('sidekick')
    elif 'mentor' in prompt_lower:
        return MockOpenAIResponses.supporting_character_response('mentor')

    # Chapter writing
    elif 'write chapter' in prompt_lower or 'chapter content' in prompt_lower:
        return MockOpenAIResponses.chapter_content_response()

    # Setting
    elif 'setting' in prompt_lower or 'world-building' in prompt_lower:
        return MockOpenAIResponses.setting_response()

    # Consistency
    elif 'consistency' in prompt_lower:
        return MockOpenAIResponses.consistency_check_response()

    # Scoring
    elif 'score' in prompt_lower or 'evaluate' in prompt_lower:
        return MockOpenAIResponses.score_response()

    # Default fallback
    else:
        return "This is a mock response for testing purposes. " + generate_random_text(20)
