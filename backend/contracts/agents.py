"""HTTP agent identity: URL slugs and mapping to pipeline ``AgentName``."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from backend.common.primitive_types import AgentNameSlug
from discount_analyst.agents.common.agent_names import AgentName


@dataclass
class AgentConfig:
    name: AgentName
    agent_name_slug: AgentNameSlug


agent_configs: Final[list[AgentConfig]] = [
    AgentConfig(name=AgentName.SURVEYOR, agent_name_slug=AgentNameSlug("surveyor")),
    AgentConfig(name=AgentName.PROFILER, agent_name_slug=AgentNameSlug("profiler")),
    AgentConfig(name=AgentName.RESEARCHER, agent_name_slug=AgentNameSlug("researcher")),
    AgentConfig(name=AgentName.STRATEGIST, agent_name_slug=AgentNameSlug("strategist")),
    AgentConfig(name=AgentName.SENTINEL, agent_name_slug=AgentNameSlug("sentinel")),
    AgentConfig(name=AgentName.APPRAISER, agent_name_slug=AgentNameSlug("appraiser")),
    AgentConfig(name=AgentName.ARBITER, agent_name_slug=AgentNameSlug("arbiter")),
]

_SLUG_TO_AGENT_NAME: Final[dict[str, AgentName]] = {
    cfg.agent_name_slug.casefold(): cfg.name for cfg in agent_configs
}


def slug_to_agent_name(slug: str) -> AgentName:
    key = slug.casefold()
    if key not in _SLUG_TO_AGENT_NAME:
        msg = f"Unknown agent name: {slug!r}"
        raise ValueError(msg)
    return _SLUG_TO_AGENT_NAME[key]
