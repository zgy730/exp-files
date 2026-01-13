import asyncio

import click

from exp_files.processor import AsyncProcessor, ProcessFilesRequest
from exp_files.settings import settings


class FileProcessorRunner:
    """File processor runner class"""

    def __init__(self):
        """Initialize the runner"""
        self.processor = AsyncProcessor(concurrent_limit=settings.concurrent_limit)

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
            print(f"Concurrent limit: {settings.concurrent_limit}")

            # Process files
            result = await self.processor.process_files(request)

            print("Processing completed!")
            print(f"Total files: {self.processor.total_files}")
            print(f"Processed files: {self.processor.processed_files}")
            print(f"Result contains {len(result)} different words")

            # Print top 10 most common words
            print("\nTop 10 most common words:")
            for word, count in result.most_common(10):
                print(f"{word}: {count}")

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
def main(dir, file):
    """File processor command line tool

    Example usage:
        python main.py --dir /path/to/directory
        python main.py --file file1.txt --file file2.txt
        python main.py -d /path/to/directory -f file1.txt -f file2.txt
    """
    runner = FileProcessorRunner()

    # Ensure dir_path is string type, click returns None when not provided
    dir_path = dir if dir is not None else ""

    # Ensure file_paths is list type, click's multiple=True returns tuple
    file_paths = list(file) if file else []

    asyncio.run(runner.run(dir_path, file_paths))


if __name__ == "__main__":
    main()
