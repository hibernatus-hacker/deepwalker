# deepwalker

This is a simple tool that runs an LLM on a directory of files using a specified system prompts. 

This is a flexible tool useful for a wide range of usecases including summarization.

Requires a [replicate.com](https://replicate.com) account.

```sh
pip install replicate
export REPLICATE_API_TOKEN=r8_xxx
python3 ./deepwalker.py ./folder_with_js_files
```

# usage

```sh

python3 deepwalker ./directory_of_files --system-prompt "give me your opinion of this code as an angry pirate"
python3 deepwalker ./directory_of_files --system-prompt ./system_prompt.txt --file-extension js
python3 deepwalker ./directory_of_files --system-prompt "be unhelpful" --model "anthropic/claude-3.5-sonnet" --extensions js mjs
python3 deepwalker.py ./test --extensions js mjs --model "deepseek-ai/deepseek-r1" --system-prompt "analyse this javascript"
```

# use cases

You can use this to explain a code base like this..

```sh
python3 deepwalker.py ./code_base --system-prompt "You an expert in <language> and provide clear and detailed explanations"
```

You can use it to search for bug bounty findings like this...

```sh
python3 deepwalker.py ./code --system-prompt ./bb_system_prompt.txt
```
