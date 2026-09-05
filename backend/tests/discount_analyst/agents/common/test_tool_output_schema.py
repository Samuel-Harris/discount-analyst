from typing import Literal

import pytest
from pydantic import BaseModel, RootModel
from pydantic_ai import Agent, ToolOutput
from pydantic_ai.exceptions import UserError
from pydantic_ai.models.test import TestModel
from pydantic_ai._utils import check_object_json_schema

from discount_analyst.agents.appraiser.appraiser import APPRAISER_AGENT_SPEC
from discount_analyst.agents.curator.curator import CURATOR_AGENT_SPEC
from discount_analyst.agents.profiler.profiler import PROFILER_AGENT_SPEC
from discount_analyst.agents.researcher.researcher import RESEARCHER_AGENT_SPEC
from discount_analyst.agents.runtime.agent_factory import AgentSpec
from discount_analyst.agents.runtime.agent_names import AgentName
from discount_analyst.agents.runtime.structured_output_unwrap import (
    unwrapping_output_type,
)
from discount_analyst.agents.sentinel.sentinel import SENTINEL_AGENT_SPEC
from discount_analyst.agents.strategist.strategist import STRATEGIST_AGENT_SPEC
from discount_analyst.agents.surveyor.surveyor import SURVEYOR_AGENT_SPEC

PIPELINE_SPECS = (
    SURVEYOR_AGENT_SPEC,
    PROFILER_AGENT_SPEC,
    RESEARCHER_AGENT_SPEC,
    STRATEGIST_AGENT_SPEC,
    SENTINEL_AGENT_SPEC,
    APPRAISER_AGENT_SPEC,
    CURATOR_AGENT_SPEC,
)


@pytest.mark.parametrize("spec", PIPELINE_SPECS, ids=lambda spec: spec.name.value)
def test_tool_output_schema_is_a_json_object(spec: AgentSpec[object]) -> None:
    Agent(
        name=spec.name,
        output_type=ToolOutput(unwrapping_output_type(spec.output_type)),
        model=TestModel(),
    )


def test_pipeline_specs_cover_every_agent_name() -> None:
    assert {spec.name for spec in PIPELINE_SPECS} == set(AgentName)


class _CanaryKeep(BaseModel):
    decision: Literal["keep_prior"] = "keep_prior"


class _CanaryReplace(BaseModel):
    decision: Literal["replace"] = "replace"
    value: str


class _CanaryUnionRoot(RootModel[_CanaryKeep | _CanaryReplace]):
    root: _CanaryKeep | _CanaryReplace


def test_root_model_union_still_fails_object_schema_check() -> None:
    with pytest.raises(UserError, match="Schema must be an object"):
        check_object_json_schema(_CanaryUnionRoot.model_json_schema())
