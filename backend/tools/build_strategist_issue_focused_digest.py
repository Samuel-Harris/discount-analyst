"""One-off builder: curated Strategist conversation excerpt file."""

from pathlib import Path


def main() -> None:
    repo = Path(__file__).resolve().parents[1]
    src = repo / "strategist_conversation_deb32c2f-369b-436b-8b91-ed1f99b73dc2.md"
    dest = (
        repo
        / "strategist_conversation_deb32c2f-369b-436b-8b91-ed1f99b73dc2_issue_focused.md"
    )

    lines = src.read_text(encoding="utf-8").splitlines(keepends=True)

    def sl(a: int, b: int) -> str:
        return "".join(lines[a - 1 : b])

    preamble = """# STRATEGIST conversations (curated, issue-focused)

- **workflow_run_id:** `deb32c2f-369b-436b-8b91-ed1f99b73dc2`
- **source:** `strategist_conversation_deb32c2f-369b-436b-8b91-ed1f99b73dc2.md` (full export: 25 tickers, ~20.8k lines)
- **this file:** representative excerpts only (duplicate per-ticker investing creed removed). Illustrates Strategist issues from `deb32c2f-369b-436b-8b91-ed1f99b73dc2_agent_review.md`: **empty assistant prose** with JSON only (BOWL.L), **orchestration / tool-channel leakage** (LBG.L, MRBK, GAMA.L), **serialisation-step blur** (GTLB), **implicit upstream linkage** in long reasoning (PRDO), and **Output Format without inline JSON schema** (system prompt tail).

---

## Canonical Strategist system prompt tail (role + output contract)

*The full export repeats the investing creed for every ticker (~230 lines each). Below is the Strategist-specific tail from the first ticker (`AVNW`), repeated verbatim across names. It references `MispricingThesis` and conviction rubric but does **not** list field-level JSON schema — relevant to the “add output schema to system prompt” improvement.*

"""

    system_tail = sl(251, 311)

    bowl = (
        """
---

## Ticker: `BOWL.L` — **empty `text` part; thesis only in `final_result`**

*Screening JSON + deep research JSON omitted (~800 lines in full export). The assistant `text` part is blank.*

```markdown
"""
        + sl(1622, 1663)
        + "\n```\n"
    )

    # LBG: line 9114 is ```json, 9115 is the JSON body (1-based from ripgrep)
    raw_json = lines[9114]  # 0-indexed
    if raw_json.strip() == "```json":
        raw_json = lines[9115]
    trunc = raw_json[:2800]
    if len(raw_json) > 2800:
        trunc += "\n… [truncated: remainder of `final_result` JSON in source file] …\n"

    lbg = (
        """
---

## Ticker: `LBG.L` — **orchestration / “orchestrator” leakage**

*Inputs omitted (long deep research JSON). First assistant message:*

"""
        + sl(9067, 9114)
        + "```json\n"
        + trunc
        + "\n```\n"
    )

    mrbk = """
---

## Ticker: `MRBK` — **“Planning tool call” / pipeline mechanics**

*Inputs omitted.*

""" + sl(12435, 12474)

    gama = """
---

## Ticker: `GAMA.L` — **tool-selection meta (`final_result` vs `multi_tool_use.parallel`)**

*Inputs omitted.*

""" + sl(5744, 5782)

    gtlb = """
---

## Ticker: `GTLB` — **reasoning blended with “prepare the JSON for the final result”**

*Inputs omitted.*

""" + sl(7417, 7443)

    prdo = """
---

## Ticker: `PRDO` — **long diary-style reasoning; no explicit “thesis hangs on field X” line**

*Inputs omitted.*

""" + sl(16614, 16632)

    out = (
        preamble
        + "```text\n"
        + system_tail.rstrip("\n")
        + "\n```\n"
        + bowl
        + lbg
        + mrbk
        + gama
        + gtlb
        + prdo
    )

    dest.write_text(out, encoding="utf-8")
    n = len(out.splitlines())
    print(f"Wrote {dest} ({n} lines)")
    if n > 6000:
        raise SystemExit(f"Exceeded 6000 lines: {n}")


if __name__ == "__main__":
    main()
