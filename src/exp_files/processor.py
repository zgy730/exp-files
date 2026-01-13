import time
import asyncio
import aiofiles
import os
from pydantic import BaseModel
from exp_files.settings import settings
from exp_files.utils import clean_text
from collections import Counter

class ProcessFilesRequest(BaseModel):
    dir_path: str = ""
    file_paths: list[str] = []

class AsyncProcessor:
    def __init__(self, concurrent_limit:int = settings.concurrent_limit):
        self.concurrent_limit = concurrent_limit
        self.semaphore = asyncio.Semaphore(concurrent_limit)
        self.total_files = 0
        self.processed_files = 0

    async def _process_file(self, file_path: str):
        async with self.semaphore:
            c = Counter()
            try:
                # 尝试使用UTF-8编码打开文件，如果失败则跳过
                async with aiofiles.open(file_path, "r", encoding=settings.encoding, errors="ignore") as f:
                    while True:
                        chunk = await f.read(settings.chunk_size)
                        if not chunk:
                            break
                        words = clean_text(chunk)
                        c.update(words)

                        await asyncio.sleep(0)

                self.processed_files += 1
                print(f"Processing {file_path} finished.")
                return c
            except Exception as e:
                print(f"Failed to process {file_path}: {e}")
                self.processed_files += 1
                return c
    
    async def process_files(self, request: ProcessFilesRequest):
        if not request.dir_path and not request.file_paths:
            raise ValueError("Either dir_path or file_paths must be provided.")
        
        # 收集所有文件路径
        all_files = set(request.file_paths)
        
        # 如果提供了目录路径，遍历目录下的所有文件
        if request.dir_path:
            if not os.path.exists(request.dir_path):
                raise ValueError(f"Directory {request.dir_path} does not exist.")
            
            for root, dirs, files in os.walk(request.dir_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    all_files.add(file_path)
        
        # 转换为列表并更新文件总数
        all_files_list = list(all_files)
        self.total_files = len(all_files_list)
        
        # 处理所有文件
        tasks = [self._process_file(file_path) for file_path in all_files_list]
        results = await asyncio.gather(*tasks)
        total_c = Counter()
        for c in results:
            total_c.update(c)
        return total_c

    async def process_status(self, request: ProcessFilesRequest):
        start_time = time.time()
        words_freq = await self.process_files(request)
        return {
            "total_files": self.total_files,
            "processed_files": self.processed_files,
            "elapsed_time": time.time() - start_time,
            "words_freq": words_freq,
        }
