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
        """Mock response for brainstorm ideas generation in JSON format."""
        import json
        ideas = []
        for i in range(num_ideas):
            ideas.append({
                "title": f"Test Novel Idea {i + 1}",
                "premise": "A brave hero embarks on a journey to save the world from darkness. The forces of evil threaten to destroy everything the hero holds dear.",
                "hook": "In a world where magic is forbidden, one person must master it to survive."
            })
        return json.dumps(ideas, indent=2)

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
        """Mock response for protagonist creation in JSON format."""
        import json
        protagonists = [{
            "name": "Aria Stormwind",
            "age": 24,
            "role": "protagonist",
            "background": "Raised in a small village by her grandmother after her parents disappeared mysteriously. Discovered her magical powers during a crisis.",
            "personality": "Brave, determined, sometimes impulsive but with a good heart",
            "goals": "Find out what happened to her parents and master her magical powers",
            "flaws": "Trusts too easily and fears losing loved ones",
            "arc": "Learns to trust herself and accept her destiny"
        }]
        return json.dumps(protagonists, indent=2)

    @staticmethod
    def antagonist_response():
        """Mock response for antagonist creation in JSON format."""
        import json
        antagonist = {
            "name": "Lord Malkor",
            "age": 45,
            "role": "antagonist",
            "background": "Once a noble wizard who turned to dark magic after losing everything. Believes he's bringing order through his actions.",
            "personality": "Calculating, ruthless, believes the end justifies the means",
            "goals": "Gain ultimate power and reshape the world according to his vision",
            "flaws": "Consumed by revenge and underestimates his opponents",
            "relationship_to_protagonist": "Represents what the protagonist could become if they succumb to darkness"
        }
        return json.dumps(antagonist, indent=2)

    @staticmethod
    def supporting_character_response(character_type="mentor"):
        """Mock response for supporting character creation in JSON array format."""
        import json
        characters = {
            "mentor": {
                "name": "Master Eldrin",
                "age": 67,
                "role": "mentor",
                "background": "An ancient wizard who has guided heroes for centuries",
                "personality": "Wise, patient, sometimes cryptic in his teachings",
                "relationship_to_protagonist": "Guide and teacher to the hero"
            },
            "sidekick": {
                "name": "Finn Quickfoot",
                "age": 22,
                "role": "sidekick",
                "background": "A clever rogue with a heart of gold",
                "personality": "Humorous, loyal, always ready with a quip",
                "relationship_to_protagonist": "Loyal companion and comic relief"
            },
            "love_interest": {
                "name": "Prince Kael",
                "age": 28,
                "role": "love_interest",
                "background": "A noble prince who fights alongside the hero",
                "personality": "Charming, brave, believes in justice",
                "relationship_to_protagonist": "Romantic interest and ally"
            }
        }

        char_data = characters.get(character_type, characters["sidekick"])
        # Return as array (even though it's single character for backwards compatibility)
        return json.dumps([char_data], indent=2)

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

    @staticmethod
    def poem_response():
        """Mock response for poem generation."""
        return """The autumn leaves fall gently down,
Like whispers from the trees,
A golden carpet on the ground,
Dancing in the breeze.

The seasons turn, the world moves on,
Yet memories remain,
Of summer days now long since gone,
And sun through falling rain."""

    @staticmethod
    def essay_response():
        """Mock response for essay generation."""
        return """The Impact of Technology on Modern Society

Introduction

Technology has fundamentally transformed the way we live, work, and interact with one another. From the invention of the printing press to the rise of artificial intelligence, each technological advancement has reshaped society in profound ways. This essay examines the multifaceted impact of technology on modern society, exploring both its benefits and challenges.

The Digital Revolution

The digital revolution has connected billions of people across the globe, enabling instant communication and unprecedented access to information. Social media platforms, video conferencing tools, and messaging apps have made it possible to maintain relationships across vast distances. However, this connectivity comes with concerns about privacy, mental health, and the quality of human interaction.

Education and Learning

Technology has democratized access to education, with online courses and digital libraries making knowledge available to anyone with an internet connection. Students can now learn at their own pace, access resources from world-class institutions, and collaborate with peers globally. Yet, the digital divide persists, leaving many without access to these opportunities.

Conclusion

While technology has brought remarkable benefits to modern society, it also presents significant challenges that we must address thoughtfully. As we continue to innovate and integrate new technologies into our lives, we must remain mindful of their impact on human connection, equality, and well-being. The future depends on our ability to harness technology's potential while mitigating its risks."""

    @staticmethod
    def sketch_response():
        """Mock response for sketch generation."""
        return """The Coffee Shop at Dawn

I push open the heavy glass door at 6:47 AM, and the smell hits me immediately—that rich, dark aroma of coffee beans being ground, mixed with something sweeter, maybe cinnamon rolls warming in the oven. The barista looks up and nods, recognizing me without really seeing me. She's already reaching for the medium cup.

There's only one other person here, an older man in the corner reading a newspaper—actual paper, not a screen. His hands are weathered, spotted with age, and they tremble slightly as he turns the pages. Every few minutes, he reaches for his coffee cup, takes a small sip, and returns to his reading without ever looking up.

The morning light is just starting to filter through the front windows, golden and tentative, illuminating dust motes that dance in the air. Outside, the street is empty except for a jogger passing by in bright yellow sneakers. Inside, the espresso machine hisses and steams, a familiar soundtrack to this quiet moment before the world fully wakes.

I find myself wondering about the man in the corner—does he come here every morning? Does he live alone? Is this newspaper his ritual, his anchor to routine? But I don't ask. We share this space in comfortable silence, two early risers seeking something in the aroma of coffee and the soft glow of dawn."""

    @staticmethod
    def article_response():
        """Mock response for article generation."""
        return """Local Community Garden Transforms Neighborhood

By Staff Writer
Published: Today

A once-vacant lot on Maple Street has been transformed into a thriving community garden, bringing together neighbors and revitalizing the local area.

The Garden Project, which broke ground six months ago, now boasts over 50 individual plots where residents grow vegetables, herbs, and flowers. The initiative, spearheaded by local resident Maria Chen, has become more than just a place to grow food—it's become a hub for community connection.

"I wanted to create a space where neighbors could come together," Chen explained during a recent visit to the garden. "In today's world, we often don't know the people living right next door. This garden changes that."

The project has attracted participants of all ages, from young families teaching their children about where food comes from to retirees sharing decades of gardening wisdom. Regular workshops on sustainable gardening practices and seasonal potlucks have further strengthened community bonds.

Local businesses have also gotten involved, with Harrison Hardware donating tools and supplies, and Riverside Nursery providing seedlings at reduced prices. The city council has taken notice, with Councilmember James Rodriguez calling it "a model for community-led urban improvement."

The garden has already yielded impressive results, with participants reporting hundreds of pounds of fresh produce harvested and shared among neighbors. Chen hopes to expand the project next spring, adding more plots and a community composting area.

"This started as an idea to make our neighborhood more beautiful," Chen said. "But it's become so much more—it's brought our community back to life."

For information about plot availability or volunteer opportunities, residents can visit the garden's community bulletin board or attend the monthly meetings held on the first Saturday of each month."""


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

    # Content type generation (check these first before other patterns)
    if 'poem' in prompt_lower and ('write' in prompt_lower or 'create' in prompt_lower or 'generate' in prompt_lower):
        return MockOpenAIResponses.poem_response()
    elif 'essay' in prompt_lower and ('write' in prompt_lower or 'create' in prompt_lower or 'generate' in prompt_lower):
        return MockOpenAIResponses.essay_response()
    elif 'sketch' in prompt_lower and ('write' in prompt_lower or 'create' in prompt_lower or 'generate' in prompt_lower):
        return MockOpenAIResponses.sketch_response()
    elif ('article' in prompt_lower or 'news' in prompt_lower) and ('write' in prompt_lower or 'create' in prompt_lower or 'generate' in prompt_lower):
        return MockOpenAIResponses.article_response()

    # Brainstorm/Ideas
    elif 'brainstorm' in prompt_lower or 'plot idea' in prompt_lower:
        return MockOpenAIResponses.brainstorm_response()

    # Plot creation
    elif 'plot structure' in prompt_lower or 'three-act' in prompt_lower:
        return MockOpenAIResponses.plot_response()

    # Characters - CHECK ANTAGONIST FIRST since antagonist prompts contain "protagonist" word
    elif 'antagonist' in prompt_lower:
        return MockOpenAIResponses.antagonist_response()
    elif 'protagonist' in prompt_lower:
        return MockOpenAIResponses.protagonist_response()
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
