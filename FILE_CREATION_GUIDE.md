# File Auto-Generation Guide

## Overview

The ProjectWorkspace now supports automatic file generation. When you use a skill that outputs file creation directives, files are created automatically in your project folder, and only the creation status is shown in the chat (not the file contents).

## How It Works

### 1. Create a File Generation Skill

In the Workspace left panel, click the Skill Manager button:

1. Click the **Skill Manager** button (📚 icon)
2. Click the **📝 Template** button to load the file generation template
3. Customize the skill prompt if needed (optional)
4. Click **Add Skill** to save

### 2. Use the Skill in Chat

1. Select the skill by checking the checkbox next to it
2. Write your instruction in the chat (e.g., "Create a documentation file for my XMF parser")
3. The skill prompt + context files + your message will be sent to Claude
4. Claude will generate file creation directives

### 3. Files Are Created Automatically

When Claude returns a response with file creation directives:
- Files are created server-side in your project folder
- File tree automatically updates
- Chat shows only creation status messages like:
  ```
  ✅ output/README.md 생성 완료 (1,234 characters)
  ✅ output/TEST.md 생성 완료 (2,456 characters)
  ```
- No file contents appear in the chat

## File Creation Directive Format

Claude must output directives in this exact format:

```
[FILE_CREATE:{"path":"relative/path/to/file.ext","content":"file content here"}]
[FILE_CREATE:{"path":"another/file.ext","content":"more content"}]
```

### Key Rules:

1. **Each file wrapped in `[FILE_CREATE:{...}]`** — This is required
2. **Valid JSON object** with:
   - `path` (string): relative path from project root
   - `content` (string): the complete file content
3. **Newlines in content**: use `\n` (backslash-n, not actual newlines in JSON)
4. **No markdown code blocks** — output directives directly
5. **Multiple directives** — one per file to create

### Example Skill Prompt:

```
You are a technical documentation expert. 

When asked to create documentation files, output ONLY file creation directives.
Use this format:

[FILE_CREATE:{"path":"docs/PLAN.md","content":"# Project Plan\n\nKey objectives:\n- item 1\n- item 2"}]
[FILE_CREATE:{"path":"docs/TEST.md","content":"# Test Strategy\n\nTest cases:\n1. test one\n2. test two"}]

Rules:
- Output ONLY FILE_CREATE directives
- Do not use markdown code blocks
- Each file must be a separate directive
- Use \n for newlines in content
```

## Example Workflow

### Step 1: Load Template
Click the **Template** button in Skill Manager

### Step 2: Customize (Optional)
Edit the skill to specify your requirements:
```
You are an XMF documentation generator.

For XMF files, create:
1. PLAN.md - High-level design document
2. TEST.md - Test strategy
3. simulator.html - Interactive simulator

Format:
[FILE_CREATE:{"path":"output/FILENAME","content":"content"}]
```

### Step 3: Use in Chat
```
User: Create documentation for this XMF file
(with XMF file selected in context)

Claude: 
[FILE_CREATE:{"path":"output/sfc1001m00-PLAN.md","content":"# SFC1001M00 Design..."}]
[FILE_CREATE:{"path":"output/sfc1001m00-TEST.md","content":"# Test Strategy..."}]
[FILE_CREATE:{"path":"output/sfc1001m00-simulator.html","content":"<html>...</html>"}]

Chat Shows:
✅ output/sfc1001m00-PLAN.md 생성 완료 (2,345 characters)
✅ output/sfc1001m00-TEST.md 생성 완료 (1,234 characters)
✅ output/sfc1001m00-simulator.html 생성 완료 (5,678 characters)
```

## Token Optimization

Using the file auto-generation system with persistent conversation IDs provides token savings:

- **Conversation persistence** (~40-50% savings): backend maintains history via `conversation_id`
- **No content bloat**: file contents don't appear in chat messages
- **Sliding window**: only last 20 messages kept (prevents unbounded growth)
- **File budgeting**: context files limited to 10,000 tokens total

## Troubleshooting

### "❌ 파일 생성 실패" (File creation failed)

**Causes:**
1. Path is outside project folder (use relative paths)
2. Directory doesn't exist (use `create_dirs: true` in API)
3. Permission issue

**Solution:** Check file path is relative to project root, e.g., `output/file.md` not `/absolute/path/file.md`

### Files not appearing in file tree

**Cause:** File tree needs refresh

**Solution:** Click the refresh button in the left panel (circular arrow icon)

### Claude not outputting directives correctly

**Cause:** Skill prompt not clear enough or Claude not following format

**Solution:** 
1. Simplify the skill prompt
2. Add explicit examples in the skill
3. Use the template as base
4. Test with a simple single-file request first

## Advanced Tips

### 1. Multi-File Generation
Create complex document sets in one request:
```
Create both a README.md and CONTRIBUTING.md for this project
```

### 2. Template Files
Create reusable file templates in your skill:
```
[FILE_CREATE:{"path":"templates/test_template.py","content":"import pytest\n\ndef test_example():\n    assert True"}]
```

### 3. Format-Specific Content
The system supports any file type:
- `.md` — Markdown documentation
- `.py` — Python code
- `.ts` — TypeScript
- `.html` — Web pages
- `.json` — Configuration
- `.yaml` — Config files
- etc.

## Integration with Other Features

### With Context Files
Files added to context are available in your skill's message:
```
Skill gets: [skill instructions] + [context file content] + [user message]
```

### With Agent.md
Your project's `agent.md` provides additional context for code generation

### With Conversation History
Messages are maintained per conversation ID, preventing token waste on repeated introductions

## Limitations

- Max file size: limited by token budget (typically ~3,000 tokens per file)
- JSON must be valid (test with online JSON validators)
- Path must be relative to project root
- Newlines must use `\n` not actual newline characters in JSON

## Future Enhancements

Planned improvements:
- Bulk file operations (zip creation)
- File preview before saving
- Batch file editing
- Version history for created files
