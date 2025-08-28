"""
This module contains utility functions for text manipulation.
"""

import re

def replace_placeholders(text: str, data: dict) -> str:
    """
    Replaces placeholders in a string with values from a dictionary in a single pass.

    Args:
        text: The string containing placeholders in the format {{KEY}}.
        data: A dictionary with keys matching the placeholders (without curly braces).

    Returns:
        The string with placeholders replaced.
    """
    def repl(match):
        key = match.group(1)
        return str(data.get(key, match.group(0)))

    return re.sub(r"{{(.*?)}}", repl, text)
