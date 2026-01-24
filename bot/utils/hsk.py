"""HSK dictionary utilities."""

import json
import os
from pathlib import Path
from typing import Optional

# Path to data directory
DATA_DIR = Path(__file__).parent.parent.parent / "data"


def load_hsk_dictionary(level: int) -> list[dict]:
    """
    Load HSK vocabulary for a given level.
    
    Args:
        level: HSK level (1, 2, or 3)
    
    Returns:
        List of word dictionaries with keys: hanzi, pinyin, translation
    """
    if level not in [1, 2, 3]:
        raise ValueError(f"Invalid HSK level: {level}. Must be 1, 2, or 3.")
    
    filepath = DATA_DIR / f"hsk{level}.json"
    
    if not filepath.exists():
        return []
    
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return data.get("words", [])


def get_vocabulary_for_level(level: int) -> list[dict]:
    """
    Get cumulative vocabulary up to and including the given HSK level.
    
    Args:
        level: HSK level (1, 2, or 3)
    
    Returns:
        Combined list of words from HSK 1 up to the given level
    """
    words = []
    for l in range(1, level + 1):
        words.extend(load_hsk_dictionary(l))
    return words


def search_word(query: str, level: int = 3) -> Optional[dict]:
    """
    Search for a word in HSK dictionaries.
    
    Args:
        query: Search query (hanzi, pinyin, or translation)
        level: Maximum HSK level to search (default: 3)
    
    Returns:
        Word dictionary if found, None otherwise
    """
    query_lower = query.lower()
    
    for l in range(1, level + 1):
        words = load_hsk_dictionary(l)
        for word in words:
            if (word["hanzi"] == query or 
                word["pinyin"].lower() == query_lower or
                query_lower in word["translation"].lower()):
                return {**word, "hsk_level": l}
    
    return None


def get_random_words(count: int = 5, level: int = 1) -> list[dict]:
    """
    Get random words for practice.
    
    Args:
        count: Number of words to return
        level: HSK level to pick from
    
    Returns:
        List of random words
    """
    import random
    
    words = load_hsk_dictionary(level)
    if not words:
        return []
    
    return random.sample(words, min(count, len(words)))
