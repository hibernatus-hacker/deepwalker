# deepwalker

Automate analysis of javascript files for quicker bug bounty hunting. Requires a [replicate.com](https://replicate.com) account.

Tweak the "system_prompt.txt" as needed to improve or change the result of the LLM analysis.

Configured to use: "anthropic/claude-3.5-sonnet" as the default LLM.

```sh
export REPLICATE_API_TOKEN=r8_xxx
python3 ./deepwalker.py ./folder_with_js_files
```
