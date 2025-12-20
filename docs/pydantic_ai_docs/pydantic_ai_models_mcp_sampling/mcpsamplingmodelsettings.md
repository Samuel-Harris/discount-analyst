### MCPSamplingModelSettings

Bases: `ModelSettings`

Settings used for an MCP Sampling model request.

Source code in `pydantic_ai_slim/pydantic_ai/models/mcp_sampling.py`

```python
class MCPSamplingModelSettings(ModelSettings, total=False):
    """Settings used for an MCP Sampling model request."""

    # ALL FIELDS MUST BE `mcp_` PREFIXED SO YOU CAN MERGE THEM WITH OTHER MODELS.

    mcp_model_preferences: ModelPreferences
    """Model preferences to use for MCP Sampling."""

```

#### mcp_model_preferences

```python
mcp_model_preferences: ModelPreferences

```

Model preferences to use for MCP Sampling.
