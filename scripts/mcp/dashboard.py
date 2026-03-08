#!/usr/bin/env -S uv run marimo run
"""MCP Tool Dashboard — browse, search, and curate tools from tool_list.json.

Run: uv run marimo run scripts/mcp/dashboard.py
"""

from __future__ import annotations

import marimo as mo

app = mo.App()


@app.cell
def _():
    import html
    import json
    from pathlib import Path

    import marimo as mo

    _script_dir = mo.notebook_dir() or (Path.cwd() / "scripts" / "mcp")
    _tool_path = _script_dir / "tool_list.json"
    _curated_path = _script_dir / "curated_tool_list.json"

    def _load_tool_list():
        if not _tool_path.exists():
            return f"Error: {_tool_path} not found. Run: uv run python scripts/mcp/fetch_mcp_tool_list.py -o {_tool_path}"
        try:
            data = json.loads(_tool_path.read_text())
            if not isinstance(data, dict):
                return "Error: tool_list.json must be a dict with server keys (eodhd, fmp)."
            return data
        except json.JSONDecodeError as e:
            return f"Error: Invalid JSON in tool_list.json: {e}"

    def _load_curated():
        if not _curated_path.exists():
            return {}
        try:
            data = json.loads(_curated_path.read_text())
            if not isinstance(data, dict):
                return {}
            return {k: v if isinstance(v, list) else [] for k, v in data.items()}
        except json.JSONDecodeError:
            return {}

    tools_data = _load_tool_list()
    curated = _load_curated()

    mo.output.clear()
    return (
        _curated_path,
        html,
        json,
        mo,
        curated,
        tools_data,
    )


@app.cell
def _(curated, html, mo, tools_data):
    if isinstance(tools_data, str):
        mo.stop(True)
        error_msg = tools_data
        total = 0
    else:
        error_msg = None
        total = sum(len(v) for v in tools_data.values())

    mo.output.clear()
    return (curated, error_msg, tools_data, total, html)


@app.cell
def _(error_msg, mo, tools_data):
    if error_msg is not None:
        mo.md(f"## MCP Tool Dashboard\n\n{error_msg}").callout(kind="danger")
        mo.stop(True)

    mo.output.replace(
        mo.md(
            f"## MCP Tool Dashboard\n\nLoaded **{sum(len(v) for v in tools_data.values())}** tools from `tool_list.json`."
        )
    )
    return


@app.cell
def _(mo):
    search_box = mo.ui.text(
        placeholder="Search by name or description…",
        label="Search",
        full_width=True,
    )
    mo.output.replace(search_box)
    return (search_box, mo)


@app.cell
def _(curated, error_msg, html, mo, search_box, tools_data):
    if error_msg is not None:
        mo.stop(True)

    all_checkboxes: dict[str, dict[str, mo.ui.checkbox]] = {}

    for _srv, _tl in tools_data.items():
        all_checkboxes[_srv] = {}
        curated_names = set(curated.get(_srv, []))
        for tool in _tl:
            name = tool.get("name", "")
            cb = mo.ui.checkbox(
                value=name in curated_names,
                label="",
            )
            all_checkboxes[_srv][name] = cb

    def _matches(tool: dict, q: str) -> bool:
        if not q:
            return True
        ql = q.lower()
        name = (tool.get("name") or "").lower()
        desc = (tool.get("description") or "").lower()
        return ql in name or ql in desc

    query = (search_box.value or "").strip()
    filtered: dict[str, list[dict]] = {}
    for _srv, _tl in tools_data.items():
        filtered[_srv] = [t for t in _tl if _matches(t, query)]

    # Don't display the huge all_checkboxes dict — it breaks rendering
    mo.output.clear()
    return (all_checkboxes, filtered, query, html, mo)


@app.cell
def _(all_checkboxes, filtered, html, mo):
    def _tool_row(server: str, tool: dict) -> mo.Html:
        name = tool.get("name", "")
        desc = tool.get("description") or ""
        # Use plain HTML with <br> for newlines; inline-block + column-width prevents column flow
        desc_html = html.escape(desc).replace("\n", "<br>")
        cb = all_checkboxes[server][name]
        return mo.hstack(
            [
                cb,
                mo.Html(
                    f'<span style="display:inline-block;column-width:9999px"><strong>{name}</strong> — {desc_html}</span>'
                ),
            ],
            justify="start",
            gap=1,
            wrap=False,
        )

    tab_contents = {}
    for _srv, _tl in filtered.items():
        if not _tl:
            tab_contents[_srv] = mo.md("_No tools match the search._")
        else:
            rows = [_tool_row(_srv, t) for t in _tl]
            tab_contents[_srv] = mo.vstack(rows, gap=1).style(
                {"maxHeight": "70vh", "overflowY": "auto"}
            )

    tabs = mo.ui.tabs(tab_contents)
    mo.output.replace(tabs)
    return (tab_contents, tabs, _tool_row)


@app.cell
def _(all_checkboxes, json, mo, tools_data):
    import pathlib
    from functools import partial

    def _do_save(curated_path, checkboxes, data, _: object = None) -> str:
        result: dict[str, list[str]] = {}
        for server in data:
            result[server] = [
                name for name, cb in checkboxes[server].items() if cb.value
            ]
        try:
            curated_path.write_text(json.dumps(result, indent=2))
            return f"Saved to {curated_path}"
        except OSError as e:
            return f"Error saving: {e}"

    _curated_path = (
        mo.notebook_dir() or (pathlib.Path.cwd() / "scripts" / "mcp")
    ) / "curated_tool_list.json"
    save_btn = mo.ui.button(
        label="Save",
        kind="success",
        on_click=partial(_do_save, _curated_path, all_checkboxes, tools_data),
    )
    mo.output.replace(save_btn)
    return (_do_save, save_btn)


@app.cell
def _(mo, save_btn):
    if save_btn.value is not None:
        msg = str(save_btn.value)
        kind = "success" if msg.startswith("Saved") else "danger"
        mo.output.replace(mo.md(msg).callout(kind=kind))
    else:
        mo.output.clear()
    return


if __name__ == "__main__":
    app.run()
