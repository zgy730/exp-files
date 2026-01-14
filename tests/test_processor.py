#!/usr/bin/env python3
"""
Test script for the new AsyncProcessor architecture with strategy pattern
"""

import asyncio
from collections import Counter

from exp_files.processor import (
    AsyncProcessor,
    ProcessFilesRequest,
    SentenceSearchStrategy,
    WordFrequencyStrategy,
)


async def test_word_frequency():
    """Test the original word frequency counting functionality"""
    print("=== Testing Word Frequency Strategy ===")

    # Create the strategy
    strategy = WordFrequencyStrategy()

    # Create processor with the strategy
    processor = AsyncProcessor(strategy)

    # Create request for current directory
    request = ProcessFilesRequest(dir_path=".")

    # Process files
    result = await processor.process_files(request)

    # Print top 10 words
    print("Top 10 words:")
    word_result = result if isinstance(result, Counter) else Counter()
    for word, count in word_result.most_common(10):
        print(f"  {word}: {count}")

    print(f"Total unique words: {len(word_result)}")
    print()


async def test_sentence_search():
    """Test the new sentence search functionality"""
    print("=== Testing Sentence Search Strategy ===")

    # Search for sentences containing "strategy" (case insensitive)
    search_query = "strategy"
    strategy = SentenceSearchStrategy(search_query)

    # Create processor with the strategy
    processor = AsyncProcessor(strategy)

    # Create request for current directory
    request = ProcessFilesRequest(dir_path=".")

    # Process files
    result = await processor.process_files(request)

    # Print matching sentences
    print(f"Found {len(result)} sentences containing '{search_query}':")
    sentence_result = result if isinstance(result, list) else []
    for match in sentence_result[:5]:  # Show first 5 matches
        print(f"  File: {match['file']}")
        print(f"  Sentence: {match['sentence']}")
        print()

    if len(result) > 5:
        print(f"  ... and {len(result) - 5} more matches")
    print()


async def test_sentence_search_case_sensitive():
    """Test sentence search with case sensitivity"""
    print("=== Testing Sentence Search Strategy (Case Sensitive) ===")

    # Search for sentences containing "Strategy" (case sensitive)
    search_query = "Strategy"
    strategy = SentenceSearchStrategy(search_query, case_sensitive=True)

    # Create processor with the strategy
    processor = AsyncProcessor(strategy)

    # Create request for current directory
    request = ProcessFilesRequest(dir_path=".")

    # Process files
    result = await processor.process_files(request)

    # Print matching sentences
    print(
        f"Found {len(result)} sentences containing '{search_query}' (case sensitive):"
    )
    for match in result:
        print(f"  File: {match['file']}")
        print(f"  Sentence: {match['sentence']}")
        print()
    print()


async def main():
    """Run all tests"""
    await test_word_frequency()
    await test_sentence_search()
    await test_sentence_search_case_sensitive()
    print("All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
