import re


def clean_text(text: str) -> list[str]:
    words = re.findall(r"\b\w+\b", text.lower())
    return words
