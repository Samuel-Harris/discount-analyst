# Audit Process

Detailed steps for running the audit, either in parallel with subagents or sequentially.

## Parallel Audit (Preferred)

If the environment supports subagents, parallelise the audit for speed:

### Subagent 1: Configuration Audit

- Read all config files (.cursorignore, .cursorindexingignore, .gitignore, .gitattributes, .cursorrules, .cursor/hooks.json)
- List `.cursor/` directory contents (rules, commands, skills, agents, plugins)
- Identify legacy artefacts: apply-intelligently rules (consider skill migration if procedural), commands (can migrate to skills)
- Assess ignore file coverage

### Subagent 2: Index Pollution Scan

- Run `du`/`find` commands for large directories
- Check for generated code, binary files, LFS paths
- Identify non-code content in the repo

### Subagent 3: Context Weight Analysis

- Measure AGENTS.md sizes and find all AGENTS.md files
- Analyse rule scoping and activation modes
- Calculate total always-on context weight

### Subagent 4: Documentation Currency Check

- Fetch <https://cursor.com/changelog> for recent features
- Compare repo configuration against latest available features
- Identify missing configurations for new features

Synthesise all subagent findings into the final report.

---

## Sequential Audit (Fallback)

If subagents are not available, run these steps in order:

### Step 1: Read configuration files

Read all of these (skip any that do not exist):

- `.cursorignore`
- `.cursorindexingignore`
- `.gitignore`
- `.gitattributes`
- `.cursorrules`
- `.cursor/hooks.json`
- `.cursor/mcp.json` / `mcp.json`
- `sandbox.json`
- Root `AGENTS.md`

### Step 2: List Cursor configuration

```bash
ls .cursor/rules/ 2>/dev/null
ls .cursor/commands/ 2>/dev/null  # Deprecated — flag for migration to skills
ls .cursor/skills/ 2>/dev/null
ls .cursor/agents/ 2>/dev/null
ls .cursor/hooks/ 2>/dev/null
ls .cursor/plugins/ 2>/dev/null
```

### Step 3: Map AGENTS.md coverage

```bash
find . -name "AGENTS.md" -type f -not -path "*/node_modules/*" -not -path "*/.git/*" | sort
```

### Step 4: Identify index pollution candidates

```bash
# Large directories
du -sh */ 2>/dev/null | sort -rh | head -20

# LFS paths
grep "filter=lfs" .gitattributes 2>/dev/null

# Generated code
grep -r "auto-generated\|DO NOT EDIT" --include="*.ts" --include="*.py" -l . 2>/dev/null | head -20

# Non-code file counts in suspect directories
find . -type f -name "*.md" -not -path "*/node_modules/*" -not -path "*/.git/*" | wc -l
```

### Step 5: Assess context weight

```bash
wc -l AGENTS.md 2>/dev/null
wc -l .cursor/rules/* 2>/dev/null
grep -l "alwaysApply: true" .cursor/rules/* 2>/dev/null
```

### Step 6: Assess skills, commands, and subagents

```bash
# Skills: check structure and descriptions
ls -R .cursor/skills/ 2>/dev/null
for skill in .cursor/skills/*/SKILL.md; do
  echo "=== $skill ==="
  head -5 "$skill"
  wc -l "$skill"
done 2>/dev/null

# Commands (can be migrated to skills via /migrate-to-skills)
ls .cursor/commands/ 2>/dev/null

# Apply-intelligently rules (consider migrating to skills if procedural)
for f in .cursor/rules/*.mdc; do
  if grep -q "^description:" "$f" && ! grep -q "^globs:" "$f" && ! grep -q "alwaysApply: true" "$f"; then
    echo "Apply-intelligently rule: $f"
  fi
done 2>/dev/null

# Subagents: check existence and configuration
for agent in .cursor/agents/*.md; do
  echo "=== $agent ==="
  head -10 "$agent"
done 2>/dev/null
```

### Step 7: Assess MCP and plugins

```bash
cat .cursor/mcp.json 2>/dev/null
cat mcp.json 2>/dev/null
ls .cursor/plugins/ 2>/dev/null
cat sandbox.json 2>/dev/null
```

### Step 8: Check Cursor documentation

Consult <https://docs.cursor.com> and <https://cursor.com/changelog> for any new features, settings, or configuration options not covered in this skill. Include relevant new findings in your recommendations.
