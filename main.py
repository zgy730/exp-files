import sys
import os
import asyncio
import click

from exp_files.settings import settings
from exp_files.processor import AsyncProcessor, ProcessFilesRequest

class FileProcessorRunner:
    """文件处理器运行类"""
    
    def __init__(self):
        """初始化运行器"""
        self.processor = AsyncProcessor(concurrent_limit=settings.concurrent_limit)
    
    async def run(self, dir_path: str = "", file_paths: list[str] = []):
        """运行文件处理器
        
        Args:
            dir_path: 要处理的目录路径
            file_paths: 要处理的文件路径列表
        """
        # 创建请求对象
        request = ProcessFilesRequest(
            dir_path=dir_path,
            file_paths=file_paths
        )
        
        try:
            print("开始处理文件...")
            print(f"并发限制: {settings.concurrent_limit}")
            
            # 处理文件
            result = await self.processor.process_files(request)
            
            print("处理完成！")
            print(f"总文件数: {self.processor.total_files}")
            print(f"处理文件数: {self.processor.processed_files}")
            print(f"结果包含 {len(result)} 个不同的词")
            
            # 打印前10个最常见的词
            print("\n前10个最常见的词:")
            for word, count in result.most_common(10):
                print(f"{word}: {count}")
                
            return result
            
        except Exception as e:
            print(f"处理过程中发生错误: {e}")
            raise

@click.command()
@click.option('--dir', '-d', help='要处理的目录路径')
@click.option('--file', '-f', multiple=True, help='要处理的文件路径，可以多次使用')
def main(dir, file):
    """文件处理器命令行工具

    示例用法：
        python main.py --dir /path/to/directory
        python main.py --file file1.txt --file file2.txt
        python main.py -d /path/to/directory -f file1.txt -f file2.txt
    """
    runner = FileProcessorRunner()
    
    # 确保dir_path是字符串类型，click未提供时返回None
    dir_path = dir if dir is not None else ""
    
    # 确保file_paths是列表类型，click的multiple=True返回元组
    file_paths = list(file) if file else []
    
    asyncio.run(runner.run(dir_path, file_paths))

if __name__ == "__main__":
    main()

