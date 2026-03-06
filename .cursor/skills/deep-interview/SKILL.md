---
name: deep-interview
description: Socratic deep interview with mathematical ambiguity gating before autonomous execution. Use when the user has a vague idea and wants thorough requirements gathering, says "interview me" or "don't assume", or the task is too complex to jump straight to code. Do NOT use when the user has a specific request with file paths and acceptance criteria, already has a plan file, or says "just do it".
---

# Deep Interview

Socratic questioning with mathematical ambiguity scoring. Replaces vague ideas with crystal-clear specifications by asking targeted questions, measuring clarity across weighted dimensions, and refusing to proceed until ambiguity drops below a configurable threshold (default: 20%).

## Execution Policy

- Ask ONE question at a time — never batch multiple questions
- Target the WEAKEST clarity dimension with each question
- Gather codebase facts via `explore-medium` subagents BEFORE asking the user about them
- Score ambiguity after every answer — display the score transparently
- Do not proceed to execution until ambiguity ≤ threshold (default 0.2)
- Allow early exit with a clear warning if ambiguity is still high
- Challenge modes activate at specific round thresholds to shift perspective

## Phase 1: Initialise

1. Parse the user's idea from the conversation
2. **Detect brownfield vs greenfield**:
   - Use a Task with `subagent_type: "explore-medium"`: check if cwd has existing source code, package files, or git history
   - If source files exist AND the user's idea references modifying/extending something: **brownfield**
   - Otherwise: **greenfield**
3. **For brownfield**: Use `explore-medium` subagent to map relevant codebase areas, store as `codebase_context`
4. **Create TodoWrite** to track interview progress (rounds, current phase)
5. **Announce the interview** to the user:

> Starting deep interview. I'll ask targeted questions to understand your idea thoroughly before building anything. After each answer, I'll show your clarity score. We'll proceed to execution once ambiguity drops below 20%.
>
> **Your idea:** "{initial_idea}"
> **Project type:** {greenfield|brownfield}
> **Current ambiguity:** 100% (we haven't started yet)

## Phase 2: Interview Loop

Repeat until `ambiguity ≤ threshold` OR user exits early:

### Step 2a: Generate Next Question

Build the question targeting the dimension with the LOWEST clarity score. Questions should expose ASSUMPTIONS, not gather feature lists.

| Dimension                    | Question Style                  | Example                                                                           |
| ---------------------------- | ------------------------------- | --------------------------------------------------------------------------------- |
| Goal Clarity                 | "What exactly happens when...?" | "When you say 'manage tasks', what specific action does a user take first?"       |
| Constraint Clarity           | "What are the boundaries?"      | "Should this work offline, or is internet connectivity assumed?"                  |
| Success Criteria             | "How do we know it works?"      | "If I showed you the finished product, what would make you say 'yes, that's it'?" |
| Context Clarity (brownfield) | "How does this fit?"            | "The existing auth uses JWT. Should we extend that or add a separate flow?"       |

### Step 2b: Ask the Question

Use `AskQuestion` with contextually relevant options plus a free-text option:

```
Round {n} | Targeting: {weakest_dimension} | Ambiguity: {score}%

{question}
```

### Step 2c: Score Ambiguity

After receiving the answer, score clarity across all dimensions (0.0–1.0 each):

1. **Goal Clarity**: Is the primary objective unambiguous? Can you state it in one sentence without qualifiers?
2. **Constraint Clarity**: Are the boundaries, limitations, and non-goals clear?
3. **Success Criteria Clarity**: Could you write a test that verifies success? Are acceptance criteria concrete?
4. **Context Clarity** (brownfield only): Do we understand the existing system well enough to modify it safely?

For each dimension produce: `score`, one-sentence `justification`, and `gap` (what's still unclear if score < 0.9).

**Calculate ambiguity:**

- Greenfield: `ambiguity = 1 - (goal × 0.40 + constraints × 0.30 + criteria × 0.30)`
- Brownfield: `ambiguity = 1 - (goal × 0.35 + constraints × 0.25 + criteria × 0.25 + context × 0.15)`

### Step 2d: Report Progress

```
Round {n} complete.

| Dimension            | Score | Weight | Weighted     | Gap              |
| -------------------- | ----- | ------ | ------------ | ---------------- |
| Goal                 | {s}   | {w}    | {s*w}        | {gap or "Clear"} |
| Constraints          | {s}   | {w}    | {s*w}        | {gap or "Clear"} |
| Success Criteria     | {s}   | {w}    | {s*w}        | {gap or "Clear"} |
| Context (brownfield) | {s}   | {w}    | {s*w}        | {gap or "Clear"} |
| **Ambiguity**        |       |        | **{score}%** |                  |

{score <= threshold ? "Clarity threshold met! Ready to proceed." : "Focusing next on: {weakest_dimension}"}
```

### Step 2e: Check Soft Limits

- **Round 3+**: Allow early exit if user says "enough", "let's go", "build it"
- **Round 10**: Soft warning: "We're at 10 rounds. Current ambiguity: {score}%. Continue or proceed?"
- **Round 20**: Hard cap: "Maximum rounds reached. Proceeding with current clarity ({score}%)."

## Phase 3: Challenge Modes

At specific round thresholds, shift the questioning perspective. Each mode is used ONCE then normal questioning resumes.

| Mode       | Activates                     | Purpose               | Prompt Injection                  |
| ---------- | ----------------------------- | --------------------- | --------------------------------- |
| Contrarian | Round 4+                      | Challenge assumptions | "What if the opposite were true?" |
| Simplifier | Round 6+                      | Remove complexity     | "What's the simplest version?"    |
| Ontologist | Round 8+ (if ambiguity > 0.3) | Find essence          | "What IS this, really?"           |

Track which modes have been used in TodoWrite to prevent repetition.

## Phase 4: Crystallise Spec

When ambiguity ≤ threshold (or hard cap / early exit):

1. Generate the specification from the full interview transcript
2. **Run `date '+%Y-%m-%d_%H-%M-%S'` in the terminal** to get the current timestamp
3. Write to `.cursor/interviews/{timestamp}_{slug}_interview.md` (e.g., `2026-03-04_14-22-10_auth-refactor_interview.md`)

### Spec Structure

```markdown
# Interview: {title}

## Metadata

- Rounds: {count}
- Final Ambiguity Score: {score}%
- Type: greenfield | brownfield
- Generated: {timestamp}
- Threshold: {threshold}
- Status: {PASSED | BELOW_THRESHOLD_EARLY_EXIT}

## Clarity Breakdown

| Dimension          | Score | Weight | Weighted      |
| ------------------ | ----- | ------ | ------------- |
| Goal Clarity       | {s}   | {w}    | {s\*w}        |
| Constraint Clarity | {s}   | {w}    | {s\*w}        |
| Success Criteria   | {s}   | {w}    | {s\*w}        |
| Context Clarity    | {s}   | {w}    | {s\*w}        |
| **Total Clarity**  |       |        | **{total}**   |
| **Ambiguity**      |       |        | **{1-total}** |

## Goal

{crystal-clear goal statement derived from interview}

## Constraints

- {constraint 1}
- {constraint 2}

## Non-Goals

- {explicitly excluded scope 1}
- {explicitly excluded scope 2}

## Acceptance Criteria

- [ ] {testable criterion 1}
- [ ] {testable criterion 2}
- [ ] {testable criterion 3}

## Assumptions Exposed & Resolved

| Assumption   | Challenge               | Resolution         |
| ------------ | ----------------------- | ------------------ |
| {assumption} | {how it was questioned} | {what was decided} |

## Technical Context

{brownfield: relevant codebase findings from explore-medium subagent}
{greenfield: technology choices and constraints}

## Ontology (Key Entities)

| Entity   | Fields           | Relationships   |
| -------- | ---------------- | --------------- |
| {entity} | {field1, field2} | {relates to...} |

## Interview Transcript

<details>
<summary>Full Q&A ({n} rounds)</summary>

### Round 1

**Q:** {question}
**A:** {answer}
**Ambiguity:** {score}% (Goal: {g}, Constraints: {c}, Criteria: {cr})

...

</details>
```

## Escalation & Stop Conditions

- **Hard cap at 20 rounds**: Proceed with whatever clarity exists, noting the risk
- **Soft warning at 10 rounds**: Offer to continue or proceed
- **Early exit (round 3+)**: Allow with warning if ambiguity > threshold
- **User says "stop", "cancel", "abort"**: Stop immediately, save interview as-is
- **Ambiguity stalls** (same score ±0.05 for 3 rounds): Activate Ontologist mode to reframe
- **All dimensions at 0.9+**: Skip to spec generation even if not at round minimum
- **Codebase exploration fails**: Proceed as greenfield, note the limitation

## Ambiguity Score Interpretation

| Score Range | Meaning              | Action                          |
| ----------- | -------------------- | ------------------------------- |
| 0.0–0.1     | Crystal clear        | Proceed immediately             |
| 0.1–0.2     | Clear enough         | Proceed (default threshold)     |
| 0.2–0.4     | Some gaps            | Continue interviewing           |
| 0.4–0.6     | Significant gaps     | Focus on weakest dimensions     |
| 0.6–0.8     | Very unclear         | May need reframing (Ontologist) |
| 0.8–1.0     | Almost nothing known | Early stages, keep going        |
