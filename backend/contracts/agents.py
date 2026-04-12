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

_KNOWN_AGENT_SLUGS: Final[frozenset[AgentNameSlug]] = frozenset(
    agent_config.agent_name_slug for agent_config in agent_configs
)


def is_known_agent_slug(slug: AgentNameSlug) -> bool:
    return slug in _KNOWN_AGENT_SLUGS
