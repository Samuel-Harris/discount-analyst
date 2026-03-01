---
name: handoff
description: Create a comprehensive AI context handoff document for long-running sessions.
disable-model-invocation: true
---

# AI Context Handoff Prompt

You are approaching the context window limit for this session. Please create a comprehensive handoff document that will allow me to continue this work in a fresh session with a new AI agent. This handoff should preserve critical context while discarding irrelevant information.

## Instructions

**First, run `date '+%Y-%m-%d_%H-%M-%S'` in the terminal to get the current date and time.** Use this exact timestamp for the Date/Time field and the filename.

Create a structured handoff document in the following format:

### 1. Session Overview

- **Date/Time**: [Run `date '+%Y-%m-%d_%H-%M-%S'` command and use the output]
- **Primary Objective**: [What we were trying to accomplish]
- **Current Status**: [Overall progress - e.g., "80% complete", "blocked on X", "ready for testing"]

### 2. Context Summary

Provide a concise summary of:

- The project/feature we're working on
- Key technical decisions made and WHY they were made (not just what)
- Architecture patterns or approaches chosen
- Important constraints or requirements driving the implementation

### 3. File Locations & Changes

List all relevant files with their paths and what changed:

```text
src/components/Auth.tsx - Added OAuth flow, implemented token refresh
config/database.ts - Switched from connection pooling to single connection (performance issue)
tests/auth.test.ts - Added integration tests for login/logout
```

### 4. Completed Tasks

What we successfully finished:

- [ ] Task 1 - with specific outcomes
- [ ] Task 2 - with any important implementation notes

### 5. Current Work in Progress

What's partially done:

- **Feature X**: 80% complete - login works, logout not yet implemented, token refresh untested
- **Bug Fix Y**: Root cause identified in file Z line 45, fix drafted but needs testing

### 6. Critical Learnings & Gotchas

Document mistakes to avoid and discoveries:

- ❌ **Don't**: Use library X for date parsing - doesn't handle timezones correctly
- ✅ **Do**: Use library Y instead - see implementation in utils/date.ts
- 🔍 **Discovery**: The race condition was caused by async state updates - fixed with mutex lock (see Auth.tsx:127)
- ⚠️ **Watch out**: The test environment doesn't match production for ENV_VAR - hardcode for tests

### 7. Dependencies & Technical Context

- Language/framework versions being used
- Key libraries and why they were chosen
- Database schema changes (if any)
- API endpoints affected
- Environment variables or configuration changes

### 8. Open Questions & Blockers

- Question 1: Should we implement OAuth2 PKCE flow or stick with standard flow?
- Blocker: Waiting for API key from DevOps team for integration tests
- Decision needed: Token expiration time - currently 1h, considering 24h

### 9. Reference Materials

- Links to relevant documentation
- Related GitHub issues or tickets
- Design docs or technical specs
- Previous handoff documents (if this is a continuation)

### 10. Code Snippets for Continuity

If there are specific implementation patterns or code blocks the next agent should know about:

```python
# Pattern we're using for error handling
try:
    result = await api_call()
except APIError as e:
    log_error(e, context={"user_id": user.id})
    return {"error": "friendly_message"}
```

## Formatting Guidelines

- Use clear headers and bullet points
- Include file paths with line numbers when relevant (file.ts:123)
- Highlight decisions with rationale (not just "we did X" but "we chose X over Y because Z")
- Mark priority levels: [HIGH], [MEDIUM], [LOW]
- Use emojis sparingly for quick visual parsing (✅ ❌ ⚠️ 🔍)
- Keep it concise but complete - aim for clarity over brevity

## What to EXCLUDE

- Intermediate debugging attempts that led nowhere
- General conversation or off-topic discussion
- Superseded decisions that were later changed
- Code that was written then deleted
- Lengthy code blocks that are now in files (just reference the files)

---

**After you create this handoff document, save it as:** `.cursor/handoffs/YYYY-MM-DD_HH-MM-SS_<brief description>_handoff.md` (e.g., `2026-02-04_11-30-00_memory_leak_investigation_handoff.md`)

Then provide me with:

1. The complete handoff document
2. A one-sentence summary of where we are
3. Confirmation of the filename you saved it as

This document will be loaded at the start of my next session to restore context efficiently.
