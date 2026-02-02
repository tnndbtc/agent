"""Utility functions for the novels app."""
import re


def calculate_word_count(text):
    """
    Calculate word count for text in any language.

    For CJK (Chinese, Japanese, Korean) languages, counts characters.
    For other languages, counts words separated by spaces.

    Args:
        text (str): The text to count

    Returns:
        int: Word/character count
    """
    if not text:
        return 0

    # Check if text contains CJK characters
    # Unicode ranges for CJK: \u4e00-\u9fff (Chinese), \u3040-\u309f (Hiragana),
    # \u30a0-\u30ff (Katakana), \uac00-\ud7af (Hangul)
    cjk_pattern = re.compile(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]')
    cjk_chars = cjk_pattern.findall(text)

    if cjk_chars:
        # For CJK text, count CJK characters
        return len(cjk_chars)
    else:
        # For other languages, count words by splitting on whitespace
        return len(text.split())
