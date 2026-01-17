"""AI Client wrapper with comprehensive logging for OpenAI API calls."""
import logging
from django.conf import settings
from openai import OpenAI
import functools

logger = logging.getLogger(__name__)

# Flag to track if patching has been applied
_patched = False


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

    def chat_completion(self, messages, model=None, temperature=None, max_tokens=None, **kwargs):
        """
        Create a chat completion with logging.

        Args:
            messages: List of message dictionaries
            model: Model name (optional, uses default if not provided)
            temperature: Temperature setting (optional, uses default if not provided)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional arguments to pass to the API

        Returns:
            OpenAI API response
        """
        model = model or self.model
        temperature = temperature if temperature is not None else self.temperature

        # Log the prompt
        logger.info("=" * 80)
        logger.info("OpenAI API Call - Chat Completion")
        logger.info(f"Model: {model}, Temperature: {temperature}, Max Tokens: {max_tokens}")
        logger.info("Messages:")
        for idx, msg in enumerate(messages):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            logger.info(f"  [{idx}] Role: {role}")
            logger.info(f"      Content: {content}")
        logger.info("-" * 80)

        try:
            # Make the API call
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

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


def generate_theme_from_idea(idea_data, language='English'):
    """
    Generate a one-sentence theme based on the plot idea.

    Args:
        idea_data: Dictionary containing idea information (premise, title, etc.)
        language: Target language for the theme (default: English)

    Returns:
        str: A one-sentence theme
    """
    logger.info(f"Generating one-sentence theme from idea - Language: {language}")

    premise = idea_data.get('premise', idea_data.get('description', ''))
    title = idea_data.get('title', 'Untitled')

    if not premise:
        logger.warning("No premise found in idea_data, returning default theme")
        return "A story of personal growth and discovery."

    # Construct the prompt
    prompt = f"""Based on the following plot idea, generate ONE SENTENCE that captures the core theme of the story.
The theme should be universal, profound, and capture the deeper meaning of the narrative.

Title: {title}
Plot Idea: {premise}

Generate the theme in {language}.

Return ONLY the one-sentence theme, nothing else."""

    messages = [
        {"role": "system", "content": "You are a literary expert who identifies core themes in stories."},
        {"role": "user", "content": prompt}
    ]

    try:
        client = LoggingOpenAIClient()
        response = client.chat_completion(
            messages=messages,
            temperature=0.7,
            max_tokens=100
        )

        theme = response.choices[0].message.content.strip()
        logger.info(f"Generated theme: {theme}")
        return theme

    except Exception as e:
        logger.error(f"Failed to generate theme: {str(e)}")
        # Return a default theme if generation fails
        return "A story of personal growth and discovery."


def patch_openai_for_logging():
    """
    Monkey-patch the OpenAI client to add logging to all chat completion calls.
    This ensures that all OpenAI API calls made by the novel_agent package are logged.
    """
    global _patched

    if _patched:
        logger.info("OpenAI logging patch already applied, skipping")
        return

    try:
        from openai.resources.chat import completions

        # Save the original create method
        original_create = completions.Completions.create

        @functools.wraps(original_create)
        def logged_create(self, *args, **kwargs):
            """Wrapper for chat.completions.create that adds logging."""
            # Extract parameters for logging
            messages = kwargs.get('messages', args[0] if args else [])
            model = kwargs.get('model', 'unknown')
            temperature = kwargs.get('temperature', 'default')
            max_tokens = kwargs.get('max_tokens', 'default')

            # Log the request
            logger.info("=" * 80)
            logger.info("OpenAI API Call - Chat Completion (via novel_agent)")
            logger.info(f"Model: {model}, Temperature: {temperature}, Max Tokens: {max_tokens}")
            logger.info("Messages:")
            for idx, msg in enumerate(messages):
                if isinstance(msg, dict):
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    logger.info(f"  [{idx}] Role: {role}")
                    logger.info(f"      Content: {content}")
            logger.info("-" * 80)

            try:
                # Call the original method
                response = original_create(self, *args, **kwargs)

                # Log the response
                if hasattr(response, 'choices') and response.choices:
                    response_text = response.choices[0].message.content if response.choices else ""
                    logger.info("OpenAI API Response:")
                    logger.info(f"  Response: {response_text}")
                    if hasattr(response, 'usage') and response.usage:
                        logger.info(f"  Usage: {response.usage.total_tokens} tokens")
                logger.info("=" * 80)

                return response

            except Exception as e:
                logger.error(f"OpenAI API Error: {str(e)}")
                logger.info("=" * 80)
                raise

        # Apply the patch
        completions.Completions.create = logged_create
        _patched = True
        logger.info("Successfully patched OpenAI client for comprehensive logging")

    except Exception as e:
        logger.error(f"Failed to patch OpenAI client: {str(e)}")
        logger.warning("OpenAI API calls may not be logged")
