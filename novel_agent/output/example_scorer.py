"""Example scoring system for evaluating writing examples."""
import json
from typing import Dict, Any, Optional, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from novel_agent.config import OPENAI_API_KEY, MODEL_NAME


class ExampleScorer:
    """Scores writing examples across multiple quality dimensions."""

    def __init__(self):
        """Initialize the example scorer."""
        self.llm = ChatOpenAI(
            model=MODEL_NAME,
            temperature=0.3,  # Lower for consistent scoring
            openai_api_key=OPENAI_API_KEY
        )

    def score_example(
        self,
        content: str,
        categories: Dict[str, str],
        category_hint: Optional[str] = None
    ) -> tuple[Dict[str, float], Dict[str, int]]:
        """
        Score a writing example across multiple categories.

        Args:
            content: The writing example to evaluate
            categories: Dict mapping category names to descriptions
            category_hint: Optional hint about example type (dialogue, action, etc.)

        Returns:
            Tuple of (scores dict, token_usage dict)
            - scores: Dict mapping category names to scores (0-10)
            - token_usage: Dict with prompt_tokens, completion_tokens, total_tokens
        """
        # Build prompt
        system_message = "You are an expert writing evaluator. Respond only with valid JSON."

        prompt_parts = [
            "You are an expert writing evaluator. Analyze the following writing example and provide scores for each category.",
            "",
            "Writing Example:",
            '"""',
            content,
            '"""',
            ""
        ]

        if category_hint:
            prompt_parts.append(f"Category Context: This is a {category_hint} example.")
            prompt_parts.append("")

        prompt_parts.append("Evaluate this writing across the following dimensions (score 0-10, where 0 is poor and 10 is excellent):")
        prompt_parts.append("")

        for i, (cat_name, cat_desc) in enumerate(categories.items(), 1):
            prompt_parts.append(f"{i}. {cat_name}: {cat_desc}")

        prompt_parts.extend([
            "",
            "For each category, provide:",
            "- A numerical score from 0-10 (decimals allowed, e.g., 7.5)",
            "- Be objective and critical",
            "- Consider both strengths and weaknesses",
            "",
            "Respond ONLY with a valid JSON object in this exact format:",
            "{",
            '    "scores": [',
            '        {"category": "Story/Plot", "score": 7.5},',
            '        {"category": "Character Development", "score": 8.0}',
            "    ]",
            "}",
            "",
            "IMPORTANT:",
            "- Keep category names EXACTLY as listed above",
            "- Return ONLY valid JSON, no markdown formatting",
            "- Include all categories in your response"
        ])

        user_prompt = "\n".join(prompt_parts)

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        response_text = response.content.strip()

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

        # Parse JSON response
        # Handle markdown code blocks if present
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
            response_text = response_text.strip()

        try:
            result = json.loads(response_text)

            # Convert to simple dict
            scores = {}
            for score_data in result.get('scores', []):
                cat_name = score_data['category']
                score_value = float(score_data['score'])
                scores[cat_name] = score_value

            return scores, token_usage

        except json.JSONDecodeError as e:
            raise ValueError(f"AI returned invalid JSON format: {e}")
