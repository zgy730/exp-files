import asyncio
from collections import Counter

import click

from exp_files.processor import (
    AsyncProcessor,
    ProcessFilesRequest,
    SentenceSearchStrategy,
    WordFrequencyStrategy,
)
from exp_files.settings import settings


class FileProcessorRunner:
    """File processor runner class"""

    def __init__(self, strategy=None, concurrent_limit=None):
        """Initialize the runner

        Args:
            strategy: Text processing strategy to use (default: WordFrequencyStrategy)
            concurrent_limit: Maximum number of concurrent tasks (default: settings.concurrent_limit)
        """
        # Use WordFrequencyStrategy as default if no strategy provided
        self.strategy = strategy or WordFrequencyStrategy()
        self.concurrent_limit = concurrent_limit or settings.concurrent_limit
        self.processor = AsyncProcessor(
            strategy=self.strategy, concurrent_limit=self.concurrent_limit
        )

    def set_strategy(self, strategy):
        """Set a new processing strategy at runtime

        Args:
            strategy: New text processing strategy to use
        """
        self.strategy = strategy
        # Create a new processor with the new strategy
        self.processor = AsyncProcessor(
            strategy=self.strategy, concurrent_limit=self.concurrent_limit
        )

    async def run(self, dir_path: str = "", file_paths: list[str] = []):
        """Run the file processor

        Args:
            dir_path: Directory path to process
            file_paths: List of file paths to process
        """
        # Create request object
        request = ProcessFilesRequest(dir_path=dir_path, file_paths=file_paths)

        try:
            print("Starting file processing...")
            print(f"Concurrent limit: {self.concurrent_limit}")
            print(f"Strategy: {self.strategy.__class__.__name__}")

            # Process files
            result = await self.processor.process_files(request)

            print("Processing completed!")
            print(f"Total files: {self.processor.total_files}")
            print(f"Processed files: {self.processor.processed_files}")

            # Print results based on strategy type
            if isinstance(self.strategy, WordFrequencyStrategy):
                counter_result = result if isinstance(result, Counter) else Counter()
                print(f"Result contains {len(counter_result)} different words")
                print("\nTop 10 most common words:")
                for word, count in counter_result.most_common(10):
                    print(f"{word}: {count}")
            elif isinstance(self.strategy, SentenceSearchStrategy):
                print(f"Found {len(result)} matching sentences")
                print("\nMatching sentences:")
                sentence_result = result if isinstance(result, list) else []
                for i, match in enumerate(
                    sentence_result[:10], 1
                ):  # Show first 10 matches
                    print(f"\n{i}. File: {match['file']}")
                    print(f"   Sentence: {match['sentence']}")
                if len(result) > 10:
                    print(f"\n... and {len(result) - 10} more matches")
            else:
                print(f"Result: {result}")

            return result

        except Exception as e:
            print(f"Error occurred during processing: {e}")
            raise


@click.command()
@click.option("--dir", "-d", help="Directory path to process")
@click.option(
    "--file",
    "-f",
    multiple=True,
    help="File paths to process, can be used multiple times",
)
@click.option(
    "--strategy",
    "-s",
    type=click.Choice(["word_freq", "sentence_search"], case_sensitive=False),
    default="word_freq",
    help="Processing strategy to use (default: word_freq)",
)
@click.option(
    "--search-query",
    "-q",
    help="Search query for sentence_search strategy",
)
@click.option(
    "--case-sensitive",
    "-c",
    is_flag=True,
    default=False,
    help="Case sensitive search for sentence_search strategy",
)
def main(dir, file, strategy, search_query, case_sensitive):
    """File processor command line tool

    Example usage:
        # Word frequency analysis
        python main.py --dir /path/to/directory

        # Sentence search (case insensitive)
        python main.py --dir /path/to/directory --strategy sentence_search --search-query "specific text"

        # Sentence search (case sensitive)
        python main.py --file file1.txt --file file2.txt --strategy sentence_search --search-query "Specific Text" --case-sensitive
    """
    # Create appropriate strategy based on command line option
    if strategy == "sentence_search":
        if not search_query:
            click.echo(
                "Error: --search-query is required for sentence_search strategy",
                err=True,
            )
            click.echo("Use --help for more information", err=True)
            return
        processor_strategy = SentenceSearchStrategy(
            search_query=search_query, case_sensitive=case_sensitive
        )
    else:
        # Default strategy: word frequency
        processor_strategy = WordFrequencyStrategy()

    # Create runner with selected strategy
    runner = FileProcessorRunner(strategy=processor_strategy)

    # Ensure dir_path is string type, click returns None when not provided
    dir_path = dir if dir is not None else ""

    # Ensure file_paths is list type, click's multiple=True returns tuple
    file_paths = list(file) if file else []

    asyncio.run(runner.run(dir_path, file_paths))


if __name__ == "__main__":
    main()
