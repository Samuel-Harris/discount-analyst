# Per-agent subagent briefs

Spawn one readonly `generalPurpose` subagent per existing `_MERGED_<AGENT>.md`. Tell every subagent:

- Do not edit files. Treat agent conclusions as untrusted claims.
- Verify load-bearing numbers against SQLite (`runs`, `evaluation_*`, `appraiser_reports`, `research_reports`, `portfolio_allocations`) rather than digest prose. Digests and default aggregated transcripts are compressed; aggregated files **omit** low-scoring ticker threads.
- Review `terminal_exec` when the agent has the tool: timeouts (`exit_code: 124`), non-zero exits, toolkit vs ad-hoc Python/HTTP/PDF, and whether failures were then labelled as “material gaps”.
- Return structured findings: evidence, severity, confidence, **valid caution vs over-caution**, and downstream effect on Curator weights/cash.

## SURVEYOR

Hard filters actually applied vs schema padding; null `key_metrics`; US vs UK universe; cap reconciliation near £500m / $600m; identity issues (non-voting lines, trusts, Guernsey); paid MCP used before yfinance/official sources. Did an incomplete screen systematically hand Sentinel a “everything unverified” packet?

## PROFILER

Official filing helpers vs IR/HTML fallback; mandate-fit language on **existing** mega-cap holdings; red-flag density; metric honesty (FY vs TTM, GBp vs GBP). Profiler does not emit a rating.

Profiler conversation count below 25 is **not** automatically incomplete coverage. Compare conversations to Profiler-entry lanes only.

## RESEARCHER

Source mix (filings vs vendor reprints). `material_open_gaps` vs `remaining_open_gaps`: unpublished economics (next print, customer, cash bridge) vs helper/sandbox failure (SEC user-agent, CH cache, missing `curl`/`pypdf`). Uniform “3–5 material gaps on every name” is a pipeline bias even when bull/bear prose is balanced.

## STRATEGIST

Is there a **single falsifiable claim** answerable from the packed file? Binary trough-vs-structure questions on never-disclosed granularity are traps under Sentinel’s derivation rule. Contrast recovery theses with overvaluation theses (missing proof of growth can *support* the latter). Conviction High/Medium/Low vs whether a long thesis should have been emitted at all. No tools is expected; unused confirmation of a load-bearing packed figure is still a miss.

## SENTINEL

This stage is an evidence memo, not a skip.

- Compare stored `thesis_verdict` with `derive_thesis_verdict` on the assessments (code overwrites the model field before persist).
- Count Supports / Neutral / Weakens / Breaks and `gap_kind`. Printed Weakens (`none` / `contradicted`) still WEAKENED; `never_disclosed` is a reservation like `calendar`; Unproven needs a Weakens/Breaks in the full list.
- Existing-position prompt: unreleased prints are reservations — did behaviour match?
- Red-flag screen: Serious concern is evidence for Appraiser/Curator, not a skip.
- Split **defensible printed-adverse labels** from **missing-data / Low-majority unproven** from **false negatives** (model wanted intact; code labelled otherwise).
- Sentinel has no `terminal_exec`. Unused filing tools freeze pack gaps as `never_disclosed`.

Do not treat a Sentinel label as an intrinsic-value SELL or a live skip of Appraiser.

## APPRAISER

Recompute expected value from `methods_json` weights. Check GBp→GBP / share-count recon, P10–P90 monotonicity, whether percentiles are model-produced or hand-drawn, primary vs cross-check role. Appraiser is valuation-only; new runs do not emit a rating. Note whether the memo still values the name when Sentinel labelled weakened/unproven/broken.

## CURATOR

Closed book. Compare conversation `final_result` / `CuratorProposal` with persisted `portfolio_allocations` (application stamps identity/action then DQR zeros). There is no packed policy. If every lane is DQR, 100% cash is **mechanically synthesised** — say so; do not praise or blame Curator caution. Flag re-rating, invented theses, dropped valued tickers, off-book web/terminal/`convert_currency`, company-cap breaches, and clusters that did not change weights.
