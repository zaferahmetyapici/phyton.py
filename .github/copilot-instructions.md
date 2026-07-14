<!-- Auto-generated: guidance for AI coding agents in this workspace -->
# Copilot / AI agent instructions for this repository

Purpose
- Brief: This repo is a tiny Python workspace containing a single script used for quick demos and experimentation.
- Primary file: [hello_phyton.py](hello_phyton.py)

Big picture
- Single-file script: no packages, services, or CI observed. The project is a one-shot script that defines a variable and prints it.
- There are no modules, tests, or build steps to coordinate across files; treat changes as small, isolated edits.

How to run locally
- Run directly with the system Python interpreter:

```powershell
python hello_phyton.py
```

Repository-specific conventions and patterns
- Filename/typo note: repository and filenames use the spelling "phyton" rather than "python" (e.g., repo root folder). Preserve existing names when editing to avoid moving files unintentionally.
- Minimal style: the code uses global assignments and immediate top-level execution (no functions or classes). When expanding features, prefer adding small functions to keep behavior testable.
- Keep changes minimal: since this is a demo script, avoid introducing heavy dependencies or frameworks.

Edit and PR guidance for AI agents
- Make minimal, well-scoped edits. If adding features, create new files under the repo root and update this doc with run instructions.
- If introducing dependencies, add a `requirements.txt` and include exact versions.
- Use Windows-friendly commands in examples (PowerShell or cmd) because the user environment is Windows.

Debugging and testing notes
- No automated tests detected. Verify changes by running the script and using the Python Debug Console in the editor.

Examples from code
- Current code pattern (literal example):

```python
a= "merhaba zafer"
print (a)
```

When to ask the user
- Ask before renaming files or moving the repo root.
- Ask before adding external dependencies or scaffolding a package layout.

Where to look next
- If more files appear later, scan for README.md, test files, or a `requirements.txt` to update these instructions and add run/test steps.

Feedback
- If any sections are unclear or you want additional examples (unit-tests, packaging, or CI), tell me which area to expand.
