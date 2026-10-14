# Qualitative review

The parent runs three steps for every pipeline agent that has a merged digest. Reviewers do not write the HTML report.

## Reviewers

Read `~/.cursor/rules/pstack-models.mdc`. Spawn one readonly `generalPurpose` reviewer per entry on the `interrogate reviewers` line. Entries are comma-separated. Label them Reviewer A, Reviewer B, and so on, in that order.

If that file or that line is missing, spawn two reviewers. Use `grok-4.7-high` and `claude-sonnet-5-5-high`.

Set Task `model` to the entry. Omit `model` when the entry is `inherit-parent` or `auto`.

If Task rejects a slug, rerun that reviewer on the family fallback. A `grok-*` entry falls back to `grok-4.7-high`. A `claude-*` entry falls back to `claude-sonnet-5-5-high`. Any other family falls back to `claude-sonnet-5-5-high`. If the fallback is also rejected, use the closest slug named in the error. Record which slug ran.

Launch every reviewer, for every agent, in one message. Give each reviewer only its own digest and the matching section of [agent-review-briefs.md](agent-review-briefs.md). Reviewers do not see each other.

Digest path:

`.cursor/artefacts/analyse-workflow-run/<uuid>/conversation_digests/_MERGED_<AGENT>.md`

Skip an agent with no merged file.

## Synthesise

When an agent's reviewers have all returned, merge their findings before lead judgement.

- Treat two write-ups as one finding when they describe the same claim.
- Record which reviewers raised it.
- A claim raised independently by two or more reviewers is the strongest signal.
- A claim from a single reviewer stays in the merge.
- If one reviewer asserts a claim and another denies it, keep both sides for lead judgement.
- Leave severity and confidence as each reviewer wrote them.

## Lead judgement

The parent is the lead. Write the agent's HTML section from the buckets below.

Put every merged finding in one bucket.

- **Act on.** The digest or SQLite supports the claim, and the claim changes this agent's section or the book-level reading.
- **Consider.** The claim may be right, and you are not sure it changes the book-level reading.
- **Noted.** The claim is true and does not change the conclusion.
- **Dismissed.** SQLite or live pipeline code contradicts the claim, or the claim is a preference with no concrete problem. State the reason.

If Act on has more than five findings for one agent, filter again. A useful verdict is short.

Name the reviewers on each finding. Pipeline synthesis reads Act on and Consider.
