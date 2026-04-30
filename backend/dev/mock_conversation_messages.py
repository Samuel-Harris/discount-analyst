"""Example `messages_json` payloads for dashboard mock mode (pydantic-ai–style message rows)."""

from __future__ import annotations

import json
from typing import Any


def _msg(kind: str, parts: list[dict[str, Any]]) -> dict[str, Any]:
    return {"kind": kind, "parts": parts}


def _user_prompt(content: str) -> dict[str, Any]:
    return {"part_kind": "user-prompt", "content": content}


def _text(content: str) -> dict[str, Any]:
    return {"part_kind": "text", "content": content}


def _tool_call(
    tool_name: str, tool_call_id: str, args: dict[str, Any]
) -> dict[str, Any]:
    return {
        "part_kind": "tool-call",
        "tool_name": tool_name,
        "tool_call_id": tool_call_id,
        "args": json.dumps(args, ensure_ascii=False),
    }


def _tool_return(
    tool_name: str, tool_call_id: str, content: dict[str, Any]
) -> dict[str, Any]:
    return {
        "part_kind": "tool-return",
        "tool_name": tool_name,
        "tool_call_id": tool_call_id,
        "content": json.dumps(content, ensure_ascii=False),
    }


def _dumps(payload: list[dict[str, Any]]) -> str:
    return json.dumps(payload, ensure_ascii=False)


def surveyor_messages_json() -> str:
    return _dumps(
        [
            _msg(
                "request",
                [
                    _user_prompt(
                        "Discover UK and US small-cap ideas. Prefer liquid names with "
                        "identifiable catalysts and avoid obvious fraud flags."
                    ),
                ],
            ),
            _msg(
                "response",
                [
                    _text(
                        "(mock) Surveyor: screening the universe and attaching illustrative "
                        "evidence so the dashboard can exercise the full pipeline."
                    ),
                    _tool_call(
                        "search_universe",
                        "mock_surveyor_1",
                        {"regions": ["UK", "US"], "cap_band": "small"},
                    ),
                    _tool_return(
                        "search_universe",
                        "mock_surveyor_1",
                        {
                            "candidates_preview": 15,
                            "note": "Synthetic tool payload for mock mode.",
                        },
                    ),
                    _text(
                        "Structured `SurveyorOutput` will be persisted on the workflow "
                        "execution row."
                    ),
                ],
            ),
        ]
    )


def profiler_messages_json(*, ticker: str) -> str:
    return _dumps(
        [
            _msg(
                "request",
                [
                    _user_prompt(
                        f"Produce a tight Profiler summary for {ticker}: business model, "
                        "risks, and whether it merits deep research."
                    ),
                ],
            ),
            _msg(
                "response",
                [
                    _text(
                        f"(mock) Profiler: normalised the ticker {ticker}, pulled placeholder "
                        "fundamentals, and drafted a candidate card for downstream agents."
                    ),
                    _tool_call(
                        "fetch_market_metadata",
                        "mock_pf_1",
                        {"ticker": ticker, "fields": ["sector", "market_cap"]},
                    ),
                    _tool_return(
                        "fetch_market_metadata",
                        "mock_pf_1",
                        {
                            "sector": "Illustrative",
                            "market_cap_display": "n/a (mock)",
                        },
                    ),
                    _text("Returning `ProfilerOutput` for persistence."),
                ],
            ),
        ]
    )


def researcher_messages_json(*, ticker: str) -> str:
    return _dumps(
        [
            _msg(
                "request",
                [
                    _user_prompt(
                        f"Deep research on {ticker}: financial quality, narrative, "
                        "catalysts, and data gaps versus the Surveyor snapshot."
                    ),
                ],
            ),
            _msg(
                "response",
                [
                    _text(
                        "(mock) Researcher: synthesised a full report body with placeholder "
                        "sections so the UI can render a realistic transcript."
                    ),
                    _tool_call(
                        "summarise_filings",
                        "mock_rs_1",
                        {"ticker": ticker, "years": 3},
                    ),
                    _tool_return(
                        "summarise_filings",
                        "mock_rs_1",
                        {
                            "bullets": [
                                "Revenue mix stable (mock)",
                                "Capex elevated (mock)",
                            ]
                        },
                    ),
                    _text("Emitting `DeepResearchReport` JSON for the run."),
                ],
            ),
        ]
    )


def strategist_messages_json(*, ticker: str) -> str:
    return _dumps(
        [
            _msg(
                "request",
                [
                    _user_prompt(
                        f"From the deep research on {ticker}, articulate a falsifiable "
                        "mispricing thesis with risks and monitoring signals."
                    ),
                ],
            ),
            _msg(
                "response",
                [
                    _text(
                        "(mock) Strategist: framed a contrarian angle with explicit "
                        "invalidation triggers—content is illustrative only."
                    ),
                    _text(
                        "Structured thesis object follows in the assistant response."
                    ),
                ],
            ),
        ]
    )


def sentinel_messages_json(*, ticker: str) -> str:
    return _dumps(
        [
            _msg(
                "request",
                [
                    _user_prompt(
                        f"Evaluate thesis risk for {ticker}: red flags, evidence quality, "
                        "and proceed / halt to valuation."
                    ),
                ],
            ),
            _msg(
                "response",
                [
                    _text(
                        "(mock) Sentinel: scored headline risks and left a clear gate "
                        "recommendation for Appraiser / rejection handling."
                    ),
                    _tool_call(
                        "score_red_flags",
                        "mock_sn_1",
                        {"ticker": ticker, "strictness": "high"},
                    ),
                    _tool_return(
                        "score_red_flags",
                        "mock_sn_1",
                        {"verdict": "proceed_with_caution (mock)", "score": 0.22},
                    ),
                ],
            ),
        ]
    )


def appraiser_messages_json(*, ticker: str) -> str:
    return _dumps(
        [
            _msg(
                "request",
                [
                    _user_prompt(
                        f"Build DCF-ready assumptions for {ticker} from research, thesis, "
                        "and Sentinel evaluation."
                    ),
                ],
            ),
            _msg(
                "response",
                [
                    _text(
                        "(mock) Appraiser: populated stock data / assumptions placeholders; "
                        "DCF is computed locally from this payload."
                    ),
                    _text("`AppraiserOutput` is stored on the agent execution."),
                ],
            ),
        ]
    )


def arbiter_messages_json(*, ticker: str) -> str:
    return _dumps(
        [
            _msg(
                "request",
                [
                    _user_prompt(
                        f"Synthesize a final Arbiter decision for {ticker} using research, "
                        "thesis, Sentinel view, and valuation output."
                    ),
                ],
            ),
            _msg(
                "response",
                [
                    _text(
                        "(mock) Arbiter: weighed margin of safety vs. conviction and wrote a "
                        "verdict-shaped decision for the dashboard."
                    ),
                    _text(
                        "`ArbiterDecision` JSON is available as the assistant response."
                    ),
                ],
            ),
        ]
    )
