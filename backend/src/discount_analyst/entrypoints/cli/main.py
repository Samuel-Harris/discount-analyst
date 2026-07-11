"""Discount Analyst CLI entry point."""

from __future__ import annotations

import argparse
import asyncio
import sys


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="discount-analyst",
        description="Discount Analyst agents, workflows, and admin tools.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    agent = sub.add_parser("agent", help="Run a single pipeline agent")
    agent_sub = agent.add_subparsers(dest="agent_name", required=True)
    for name in ("surveyor", "researcher", "strategist", "sentinel", "appraiser"):
        agent_sub.add_parser(name, help=f"Run the {name} agent")

    workflow = sub.add_parser("workflow", help="Multi-agent workflows")
    workflow_sub = workflow.add_subparsers(dest="workflow_name", required=True)
    workflow_sub.add_parser("run", help="Run the full Surveyor→verdicts workflow")

    admin = sub.add_parser("admin", help="Admin / maintenance commands")
    admin_sub = admin.add_subparsers(dest="admin_name", required=True)
    admin_sub.add_parser("export-openapi", help="Export dashboard OpenAPI schema")
    admin_sub.add_parser("check-alembic-schema", help="Verify Alembic vs ORM metadata")
    admin_sub.add_parser("verify-terminal", help="Verify agent-terminal service")

    return parser


def main(argv: list[str] | None = None) -> None:
    argv = list(sys.argv[1:] if argv is None else argv)
    # Allow `discount-analyst agent surveyor --model ...` by peeling known prefixes
    # then forwarding remaining args to the legacy argparse entry points.
    if not argv:
        _build_parser().print_help()
        raise SystemExit(2)

    command = argv[0]
    rest = argv[1:]

    if command == "agent":
        if not rest:
            _build_parser().parse_args(["agent"])
            return
        agent_name, *agent_args = rest
        _run_agent(agent_name, agent_args)
        return

    if command == "workflow":
        if not rest or rest[0] != "run":
            _build_parser().parse_args(["workflow", *(rest or [])])
            return
        from discount_analyst.entrypoints.cli.workflows import run_full_workflow

        sys.argv = ["run_full_workflow", *rest[1:]]
        asyncio.run(run_full_workflow.main())
        return

    if command == "admin":
        if not rest:
            _build_parser().parse_args(["admin"])
            return
        admin_name, *admin_args = rest
        _run_admin(admin_name, admin_args)
        return

    _build_parser().parse_args(argv)


def _run_agent(agent_name: str, agent_args: list[str]) -> None:
    sys.argv = [f"run_{agent_name}", *agent_args]
    if agent_name == "surveyor":
        from discount_analyst.entrypoints.cli.agents import run_surveyor

        asyncio.run(run_surveyor.main())
    elif agent_name == "researcher":
        from discount_analyst.entrypoints.cli.agents import run_researcher

        asyncio.run(run_researcher.main())
    elif agent_name == "strategist":
        from discount_analyst.entrypoints.cli.agents import run_strategist

        asyncio.run(run_strategist.main())
    elif agent_name == "sentinel":
        from discount_analyst.entrypoints.cli.agents import run_sentinel

        asyncio.run(run_sentinel.main())
    elif agent_name == "appraiser":
        from discount_analyst.entrypoints.cli.agents import run_appraiser

        asyncio.run(run_appraiser.main())
    else:
        raise SystemExit(f"Unknown agent: {agent_name}")


def _run_admin(admin_name: str, admin_args: list[str]) -> None:
    import runpy
    from pathlib import Path

    tools = Path(__file__).resolve().parents[4] / "tools"
    mapping = {
        "export-openapi": tools / "export_dashboard_openapi.py",
        "check-alembic-schema": tools / "check_alembic_schema.py",
        "verify-terminal": tools / "verify_agent_terminal.py",
    }
    script = mapping.get(admin_name)
    if script is None:
        raise SystemExit(f"Unknown admin command: {admin_name}")
    sys.argv = [str(script), *admin_args]
    runpy.run_path(str(script), run_name="__main__")


if __name__ == "__main__":
    main()
