# Command-parser evaluation — `ollama:llama3.1`

30 spoken instructions, run 2026-09-13. Six of them contain speech-to-text corruptions the prompt is meant to tolerate.

| metric | value |
|---|---|
| valid_json | 1.00 |
| tool_acc | 0.97 |
| action_acc | 1.00 |
| handedness_acc | 1.00 |
| exact_match | 0.97 |
| command_acc | 1.00 |
| p50 latency | 4.68 s |
| p95 latency | 7.04 s |

## Failures

| instruction | expected | got |
|---|---|---|
| kiran cut here | scissors/cut/left | {"tool": "scalpel", "action": "cut", "handedness": "left"} |
