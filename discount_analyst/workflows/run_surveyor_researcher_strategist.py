"""Compatibility wrapper for the scripts workflow entry point."""

import asyncio

from scripts.workflows.run_surveyor_researcher_strategist import main


if __name__ == "__main__":
    asyncio.run(main())
