import asyncio
import os
import time
from abc import ABC, abstractmethod
from collections import Counter
from typing import Any, List, Optional

import aiofiles
from pydantic import BaseModel

from exp_files.settings import settings
from exp_files.utils import clean_text


class ProcessFilesRequest(BaseModel):
    dir_path: str = ""
    file_paths: list[str] = []


# Strategy interface for text processing
class TextProcessingStrategy(ABC):
    @abstractmethod
    def process_chunk(self, chunk: str) -> Any:
        """Process a chunk of text"""
        pass

    @abstractmethod
    def merge_results(self, results: List[Any]) -> Any:
        """Merge results from multiple chunks"""
        pass

    @abstractmethod
    def get_final_result(self) -> Any:
        """Get the final result after processing all chunks"""
        pass


# Concrete strategy: Word frequency counting (original functionality)
class WordFrequencyStrategy(TextProcessingStrategy):
    def __init__(self):
        self.counter = Counter()

    def process_chunk(self, chunk: str) -> Counter:
        words = clean_text(chunk)
        return Counter(words)

    def merge_results(self, results: List[Counter]) -> None:
        for result in results:
            self.counter.update(result)

    def get_final_result(self) -> Counter:
        return self.counter


# Concrete strategy: Sentence search
class SentenceSearchStrategy(TextProcessingStrategy):
    def __init__(self, search_query: str, case_sensitive: bool = False):
        self.search_query = search_query if case_sensitive else search_query.lower()
        self.case_sensitive = case_sensitive
        self.matched_sentences: List[dict] = []
        self.current_file: Optional[str] = None
        self.buffer = ""  # Buffer to handle sentences that span chunks

    def set_current_file(self, file_path: str) -> None:
        self.current_file = file_path

    def process_chunk(self, chunk: str) -> List[dict]:
        # Combine with buffer to handle sentences spanning chunks
        combined_text = self.buffer + chunk
        self.buffer = ""

        # Split into sentences (simple implementation, can be improved)
        sentences = []
        current_sentence = ""
        for char in combined_text:
            current_sentence += char
            if char in [".", "!", "?"]:
                sentences.append(current_sentence.strip())
                current_sentence = ""

        # Keep the last incomplete sentence in buffer
        if current_sentence.strip():
            self.buffer = current_sentence

        # Search for matching sentences
        matched = []
        for sentence in sentences:
            text_to_search = sentence if self.case_sensitive else sentence.lower()
            if self.search_query in text_to_search:
                matched.append({"file": self.current_file, "sentence": sentence})

        return matched

    def merge_results(self, results: List[List[dict]]) -> None:
        for result in results:
            self.matched_sentences.extend(result)

    def get_final_result(self) -> List[dict]:
        # Check if there's a remaining sentence in buffer that matches
        if self.buffer.strip():
            text_to_search = self.buffer if self.case_sensitive else self.buffer.lower()
            if self.search_query in text_to_search:
                self.matched_sentences.append(
                    {"file": self.current_file, "sentence": self.buffer.strip()}
                )
        return self.matched_sentences


class AsyncProcessor:
    def __init__(
        self,
        strategy: TextProcessingStrategy,
        concurrent_limit: int = settings.concurrent_limit,
    ):
        self.concurrent_limit = concurrent_limit
        self.semaphore = asyncio.Semaphore(concurrent_limit)
        self.total_files = 0
        self.processed_files = 0
        self.strategy = strategy

    async def _process_file(self, file_path: str):
        async with self.semaphore:
            # Create a new strategy instance for each file to avoid state sharing
            file_strategy = self._create_strategy_instance()

            # Set current file if strategy supports it
            if func := getattr(file_strategy, "set_current_file", None):
                func(file_path)

            try:
                # Try to open file with UTF-8 encoding, skip if failed
                async with aiofiles.open(
                    file_path, "r", encoding=settings.encoding, errors="ignore"
                ) as f:
                    while True:
                        chunk = await f.read(settings.chunk_size)
                        if not chunk:
                            break
                        result = file_strategy.process_chunk(chunk)
                        file_strategy.merge_results([result])

                        await asyncio.sleep(0)

                self.processed_files += 1
                print(f"Processing {file_path} finished.")
                return file_strategy.get_final_result()
            except Exception as e:
                print(f"Failed to process {file_path}: {e}")
                self.processed_files += 1
                return file_strategy.get_final_result()

    def _create_strategy_instance(self) -> TextProcessingStrategy:
        """Create a new instance of the strategy"""
        if isinstance(self.strategy, WordFrequencyStrategy):
            return WordFrequencyStrategy()
        elif isinstance(self.strategy, SentenceSearchStrategy):
            return SentenceSearchStrategy(
                self.strategy.search_query, self.strategy.case_sensitive
            )
        else:
            raise ValueError(
                f"Unsupported strategy type: {type(self.strategy).__name__}"
            )

    async def process_files(self, request: ProcessFilesRequest):
        if not request.dir_path and not request.file_paths:
            raise ValueError("Either dir_path or file_paths must be provided.")

        # Collect all file paths
        all_files = set(request.file_paths)

        # If directory path is provided, traverse all files in the directory
        if request.dir_path:
            if not os.path.exists(request.dir_path):
                raise ValueError(f"Directory {request.dir_path} does not exist.")

            for root, dirs, files in os.walk(request.dir_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    all_files.add(file_path)

        # Convert to list and update total files count
        all_files_list = list(all_files)
        self.total_files = len(all_files_list)

        # Process all files
        tasks = [self._process_file(file_path) for file_path in all_files_list]
        results = await asyncio.gather(*tasks)

        # Merge results according to strategy type
        if isinstance(self.strategy, WordFrequencyStrategy):
            total_counter = Counter()
            for result in results:
                total_counter.update(result)
            return total_counter
        elif isinstance(self.strategy, SentenceSearchStrategy):
            all_matched_sentences = []
            for result in results:
                all_matched_sentences.extend(result)
            return all_matched_sentences
        else:
            # For other strategies, just return the merged results
            return results

    async def process_status(self, request: ProcessFilesRequest):
        start_time = time.time()
        result = await self.process_files(request)
        return {
            "total_files": self.total_files,
            "processed_files": self.processed_files,
            "elapsed_time": time.time() - start_time,
            "result": result,
        }
