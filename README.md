

# exp-files

File processing utility with async capabilities.

## Usage

```bash
# Word frequency analysis
exp-files --dir /path/to/directory

# Sentence search (case insensitive)
exp-files --dir /path/to/directory --strategy sentence_search --search-query "specific text"

# Sentence search (case sensitive)
exp-files --file file1.txt --file2.txt --strategy sentence_search --search-query "Specific Text" --case-sensitive
```

## Command Line Options

- `--dir` (`-d`): Directory path to process
- `--file` (`-f`): File paths to process (can be used multiple times)
- `--strategy` (`-s`): Processing strategy to use (`word_freq` or `sentence_search`, default: `word_freq`)
- `--search-query` (`-q`): Search query for `sentence_search` strategy
- `--case-sensitive` (`-c`): Case sensitive search for `sentence_search` strategy
