"""HTTP agent identity: URL slugs and mapping to pipeline ``AgentName``."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from backend.contracts.enums import AgentNameSlug
from discount_analyst.agents.common.agent_names import AgentName


@dataclass
class AgentConfig:
    name: AgentName
    agent_name_slug: AgentNameSlug


agent_configs: Final[list[AgentConfig]] = [
    AgentConfig(name=AgentName.SURVEYOR, agent_name_slug=AgentNameSlug.SURVEYOR),
    AgentConfig(name=AgentName.PROFILER, agent_name_slug=AgentNameSlug.PROFILER),
    AgentConfig(name=AgentName.RESEARCHER, agent_name_slug=AgentNameSlug.RESEARCHER),
    AgentConfig(name=AgentName.STRATEGIST, agent_name_slug=AgentNameSlug.STRATEGIST),
    AgentConfig(name=AgentName.SENTINEL, agent_name_slug=AgentNameSlug.SENTINEL),
    AgentConfig(name=AgentName.APPRAISER, agent_name_slug=AgentNameSlug.APPRAISER),
    AgentConfig(name=AgentName.ARBITER, agent_name_slug=AgentNameSlug.ARBITER),
]
