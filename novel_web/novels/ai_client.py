"""AI Client wrapper with comprehensive logging for OpenAI API calls."""
import logging
from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)


class LoggingOpenAIClient:
    """
    OpenAI client wrapper that logs all prompts and responses at INFO level.
    """

    def __init__(self):
        """Initialize the OpenAI client with API key from settings."""
        api_key = settings.NOVEL_AGENT.get('OPENAI_API_KEY', '')
        if not api_key:
            logger.warning("OpenAI API key not configured in settings")
        self.client = OpenAI(api_key=api_key)
        self.model = settings.NOVEL_AGENT.get('MODEL_NAME', 'gpt-4o-mini')
        self.temperature = settings.NOVEL_AGENT.get('TEMPERATURE', 0.7)

    def chat_completion(self, messages, model=None, temperature=None, top_p=None, max_tokens=None, **kwargs):
        """
        Create a chat completion with logging.

        Args:
            messages: List of message dictionaries
            model: Model name (optional, uses default if not provided)
            temperature: Temperature setting (optional, uses default if not provided)
            top_p: Top_p setting for nucleus sampling (optional, defaults to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional arguments to pass to the API

        Returns:
            OpenAI API response
        """
        model = model or self.model
        temperature = temperature if temperature is not None else self.temperature
        top_p = top_p if top_p is not None else 1.0

        # Log the prompt
        import json
        logger.info("=" * 80)
        logger.info("OpenAI API Call - Chat Completion")
        logger.info(f"Model: {model}, Temperature: {temperature}, Top_p: {top_p}, Max Tokens: {max_tokens}")
        logger.info("Messages:")
        logger.info(json.dumps({"messages": messages}, indent=2, ensure_ascii=False))
        logger.info("-" * 80)

        try:
            # Build API call parameters
            api_params = {
                'model': model,
                'messages': messages,
                'temperature': temperature,
                'top_p': top_p,
                **kwargs
            }

            # Only include max_tokens/max_completion_tokens if it's not None
            # When omitted, OpenAI API uses default behavior (unlimited within model limits)
            # GPT-5+ models use max_completion_tokens instead of max_tokens
            if max_tokens is not None:
                if model.startswith('gpt-5'):
                    api_params['max_completion_tokens'] = max_tokens
                else:
                    api_params['max_tokens'] = max_tokens

            # Make the API call
            response = self.client.chat.completions.create(**api_params)

            # Log the response
            response_text = response.choices[0].message.content if response.choices else ""
            logger.info("OpenAI API Response:")
            logger.info(f"  Response: {response_text}")
            logger.info(f"  Usage: {response.usage.total_tokens if response.usage else 'N/A'} tokens")
            logger.info("=" * 80)

            return response

        except Exception as e:
            logger.error(f"OpenAI API Error: {str(e)}")
            logger.info("=" * 80)
            raise

    def _extract_tokens(self, response):
        """
        Extract token usage from OpenAI API response.

        Args:
            response: OpenAI API response object

        Returns:
            dict: Token usage with prompt_tokens, completion_tokens, total_tokens
        """
        if hasattr(response, 'usage') and response.usage:
            return {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
        return {
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0
        }

    def _parse_json(self, content):
        """
        Parse JSON from response content, handling markdown code blocks.

        Args:
            content: Response content string

        Returns:
            dict or list: Parsed JSON object or array

        Raises:
            json.JSONDecodeError: If content is not valid JSON
        """
        import json
        import re

        content = content.strip()

        # Try to parse as JSON directly
        if content.startswith('{') or content.startswith('['):
            return json.loads(content)

        # Extract from markdown code block (handles both objects and arrays)
        json_match = re.search(r'```(?:json)?\s*([\{\[].*?[\}\]])\s*```', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))

        # If no JSON found, raise error
        raise json.JSONDecodeError(f"No valid JSON found in content", content, 0)

    def chat_completion_with_json(self, messages, model=None, temperature=None, max_tokens=None, **kwargs):
        """
        Create a chat completion and parse JSON response with token tracking.

        Args:
            messages: List of message dictionaries
            model: Model name (optional, uses default if not provided)
            temperature: Temperature setting (optional, uses default if not provided)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional arguments to pass to the API

        Returns:
            tuple: (parsed_json_dict, token_usage_dict)

        Raises:
            json.JSONDecodeError: If response is not valid JSON
        """
        response = self.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

        # Extract content and tokens
        content = response.choices[0].message.content if response.choices else ""
        token_usage = self._extract_tokens(response)

        # Parse JSON
        parsed_json = self._parse_json(content)

        return parsed_json, token_usage

    def analyze_writing_sample(self, sample_text, max_tokens=800):
        """
        Analyze a writing sample to detect language and extract style characteristics.

        Args:
            sample_text: Text sample (ideally ≤100 words)
            max_tokens: Maximum tokens for response (default: 800)

        Returns:
            tuple: (analysis_dict, token_usage_dict) where analysis_dict contains:
                - detected_locale: Language code (e.g., 'en', 'zh-hans', 'ja')
                - detected_language: Human-readable language name
                - pacing: 'slow', 'medium', or 'fast'
                - tone: Descriptive tone (e.g., 'formal', 'conversational')
                - paragraph_length: 'short', 'medium', or 'long'
                - dialogue_ratio: 'low', 'medium', or 'high'
                - instructions: Detailed writing style instructions for AI
        """
        logger.info(f"Analyzing writing sample ({len(sample_text)} chars)")

        prompt = f"""Analyze the following writing sample and extract its stylistic characteristics.

Writing Sample:
{sample_text}

Perform the following analysis:
1. Detect the language and provide the language code (e.g., 'en', 'zh-hans', 'zh-hant', 'ja', 'ko', 'fr', 'de', 'es', etc.)
2. Analyze the pacing: slow (deliberate, detailed), medium (balanced), or fast (rapid, action-driven)
3. Identify the tone (e.g., formal, conversational, poetic, journalistic, humorous, dramatic)
4. Assess paragraph length: short (1-3 sentences), medium (4-6 sentences), or long (7+ sentences)
5. Estimate dialogue ratio: low (<20% dialogue), medium (20-50%), or high (>50%)
6. Generate detailed writing style instructions that capture:
   - Sentence structure patterns
   - Vocabulary level and word choice
   - Narrative voice and perspective
   - Rhythm and flow
   - Any distinctive stylistic features

Return a JSON object with this structure:
{{
    "detected_locale": "language_code",
    "detected_language": "Human readable language name",
    "pacing": "slow|medium|fast",
    "tone": "descriptive tone",
    "paragraph_length": "short|medium|long",
    "dialogue_ratio": "low|medium|high",
    "instructions": "Detailed multi-sentence writing style instructions"
}}

Return ONLY the JSON object, no additional text."""

        messages = [
            {"role": "system", "content": "You are an expert literary analyst skilled at identifying writing styles and linguistic patterns."},
            {"role": "user", "content": prompt}
        ]

        try:
            data, token_usage = self.chat_completion_with_json(
                messages=messages,
                temperature=0.3,  # Lower temperature for more consistent analysis
                max_tokens=max_tokens
            )

            logger.info(f"Writing sample analysis complete: {data.get('detected_language', 'Unknown')} language detected")
            return data, token_usage

        except Exception as e:
            logger.error(f"Failed to analyze writing sample: {str(e)}")
            raise

    def analyze_simple_style(self, sample_text, max_tokens=800):
        """
        Simplified analysis: extract first 100 words and generate style definition and agent role.

        Args:
            sample_text: Full text sample
            max_tokens: Maximum tokens for response (default: 800)

        Returns:
            tuple: (analysis_dict, token_usage_dict) where analysis_dict contains:
                - style_name: Short descriptive name for the style
                - style_instruction: Detailed writing style instructions
                - agent_role_name: Short name for the AI agent role
                - agent_role_instruction: Agent role definition/instructions
                - language_code: Language code (e.g., 'en', 'zh-hans')
                - temperature: Suggested temperature value (0.0-1.2)
                - top_p: Suggested top_p value (0.0-1.0)
                - first_100_words: The extracted sample (first 100 words)
        """
        logger.info(f"Simple style analysis ({len(sample_text)} chars)")

        # Extract first 100 words
        words = sample_text.split()
        first_100_words = ' '.join(words[:100])

        logger.info(f"Extracted first {len(words[:100])} words from sample")

        # Fetch prompt template from database
        from .models import PromptTemplate

        try:
            # Try to get model-specific template first
            template = PromptTemplate.objects.filter(
                name_key='analyze_simple_style',
                is_active=True,
                model_name=self.model
            ).first()

            # Fallback to default template (model_name=None)
            if not template:
                template = PromptTemplate.objects.filter(
                    name_key='analyze_simple_style',
                    is_active=True,
                    model_name__isnull=True
                ).first()

            if not template:
                raise ValueError("No active 'analyze_simple_style' template found in database")

            # Build messages array with 3-part structure (system/developer/user)
            messages = [
                {"role": "system", "content": template.system_message}
            ]

            # Add developer message if present
            if template.developer_message:
                messages.append({"role": "developer", "content": template.developer_message})

            # Format user message template with sample text
            user_content = template.user_message_template.format(
                first_100_words=first_100_words
            )
            messages.append({"role": "user", "content": user_content})

        except Exception as e:
            logger.error(f"Failed to load prompt template from database: {str(e)}")
            logger.warning("Falling back to hardcoded prompt")

            # Fallback to hardcoded prompt if database template not found
            prompt = f"""Analyze the following text sample and generate a custom writing style definition and agent role definition.

Text Sample:
{first_100_words}

Based on this sample, generate:
1. **style_name**: A short, descriptive name for this writing style (e.g., "Poetic Narrative", "Technical Academic", "Conversational Storytelling")
2. **style_instruction**: Detailed instructions for an AI to replicate this writing style. Include specifics about:
   - Sentence structure and rhythm
   - Vocabulary level and word choice
   - Tone and voice
   - Any distinctive stylistic features
3. **agent_role_name**: A short name for the AI agent role that would write in this style (e.g., "Creative Poet", "Academic Scholar", "Casual Storyteller")
4. **agent_role_instruction**: Instructions defining the AI agent's persona, expertise, and approach when writing in this style
5. **language_code**: The language code of the text (e.g., 'en', 'zh-hans', 'zh-hant', 'ja', 'ko', 'fr', 'de', 'es', etc.)

**IMPORTANT INSTRUCTION:**
- Generate ALL text values (`style_name`, `style_instruction`, `agent_role_name`, `agent_role_instruction`) in the SAME LANGUAGE as the text sample above.
- For example: if the sample is in Chinese, write everything in Chinese; if in Japanese, write in Japanese; if in English, write in English.
- The JSON keys must remain in English.
- Only the `language_code` value should be the language code (e.g., 'zh-hans'), not translated.

Return a JSON object with this exact structure:
{{
    "style_name": "name in sample's language",
    "style_instruction": "instructions in sample's language",
    "agent_role_name": "role name in sample's language",
    "agent_role_instruction": "role instructions in sample's language",
    "language_code": "language_code_here"
}}

Return ONLY the JSON object, no additional text."""

            messages = [
                {"role": "system", "content": "You are an expert literary analyst who creates precise writing style definitions and agent role definitions."},
                {"role": "user", "content": prompt}
            ]

        try:
            data, token_usage = self.chat_completion_with_json(
                messages=messages,
                temperature=0.3,  # Lower temperature for consistent analysis
                max_tokens=max_tokens
            )

            # Add the first_100_words to the response
            data['first_100_words'] = first_100_words

            logger.info(f"Simple style analysis complete: {data.get('style_name', 'Unknown')}")
            return data, token_usage

        except Exception as e:
            logger.error(f"Failed to analyze simple style: {str(e)}")
            raise


def generate_theme_from_idea(idea_data, language='English'):
    """
    Generate a one-sentence theme based on the plot idea.

    Args:
        idea_data: Dictionary containing idea information (premise, title, etc.)
        language: Target language for the theme (default: English)

    Returns:
        tuple: (theme, token_usage) where token_usage is a dict with prompt_tokens, completion_tokens, total_tokens
    """
    logger.info(f"Generating one-sentence theme from idea - Language: {language}")

    premise = idea_data.get('premise', idea_data.get('description', ''))
    title = idea_data.get('title', 'Untitled')

    if not premise:
        logger.warning("No premise found in idea_data, returning default theme")
        return "A story of personal growth and discovery.", {}

    # Construct the prompt
    prompt = f"""Based on the following plot idea, generate ONE SENTENCE that captures the core theme of the story.
The theme should be universal, profound, and capture the deeper meaning of the narrative.

Title: {title}
Plot Idea: {premise}

Generate the theme in {language}.

You MUST return a JSON object with the following structure:
{{
    "theme": "One sentence that captures the core theme"
}}

Return ONLY the JSON object, no additional text or explanation."""

    messages = [
        {"role": "system", "content": "You are a literary expert who identifies core themes in stories."},
        {"role": "user", "content": prompt}
    ]

    try:
        client = LoggingOpenAIClient()
        data, token_usage = client.chat_completion_with_json(
            messages=messages,
            temperature=0.7,
            max_tokens=150
        )

        theme = data.get('theme', "A story of personal growth and discovery.")
        logger.info(f"Generated theme: {theme}, tokens: {token_usage}")
        return theme, token_usage

    except Exception as e:
        logger.error(f"Failed to generate theme: {str(e)}")
        # Return a default theme if generation fails
        return "A story of personal growth and discovery.", {}
