# deepwalker

Automate analysis of javascript files for quicker bug bounty hunting. Requires a [replicate.com](https://replicate.com) account.

Tweak the "system_prompt.txt" as needed to improve or change the result of the LLM analysis.

Configured to use: "anthropic/claude-3.5-sonnet" as the default LLM.

```sh
pip install replicate
export REPLICATE_API_TOKEN=r8_xxx
python3 ./deepwalker.py ./test
```

## Example output:

This is the output from the test file that contains: "console.log(11)"

```sh
=== JAVASCRIPT SECURITY ANALYSIS REPORT ===
Generated: 2025-03-03 23:04:53

FILE #1: test/test.js
================================================================================
Status: COMPLETED
Analyzed: 2025-03-03T23:04:53.591240

ANALYSIS:
--------------------------------------------------------------------------------
After analyzing the provided JavaScript code, I can report:

NO FINDINGS

The provided code only contains a simple console.log statement with a numeric value (11), which does not present any security vulnerabilities, exposed secrets, or noteworthy security issues.


================================================================================

=== SUMMARY ===
Total files processed: 1
Successfully analyzed: 1
Failed analyses: 0
Skipped files: 0

```
