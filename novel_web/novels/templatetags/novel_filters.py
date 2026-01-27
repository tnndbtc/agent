"""Custom template filters for the novels app."""
from django import template
import re

register = template.Library()


@register.filter
def uuid_equals(uuid1, uuid2):
    """Compare two UUIDs for equality, handling both UUID objects and strings."""
    if uuid1 is None or uuid2 is None:
        return False
    # Convert both to strings for comparison
    return str(uuid1) == str(uuid2)


@register.filter
def first_sentences(text, count=2):
    """Extract the first N sentences from text.

    Args:
        text: The text to extract sentences from
        count: Number of sentences to extract (default 2)

    Returns:
        String containing the first N sentences, or empty string if no text
    """
    if not text:
        return ""

    # Clean up the text - remove extra whitespace
    text = text.strip()

    # Match sentences ending with . ! ? followed by space or end of string
    # This regex handles most common sentence endings
    sentences = re.split(r'(?<=[.!?])\s+', text)

    # Filter out empty strings
    sentences = [s for s in sentences if s.strip()]

    # Take first N sentences
    if not sentences:
        return ""

    preview_sentences = sentences[:count]
    result = ' '.join(preview_sentences)

    # Ensure sentences end with punctuation
    if result and result[-1] not in '.!?':
        # If the last character isn't punctuation, it might be incomplete
        # Add ellipsis to indicate continuation
        result += '...'

    # Limit length as safety measure (max ~200 chars)
    if len(result) > 200:
        # Find the last space before 197 chars to avoid breaking words
        truncate_point = result[:197].rfind(' ')
        if truncate_point > 0:
            result = result[:truncate_point] + '...'
        else:
            result = result[:197] + '...'

    return result