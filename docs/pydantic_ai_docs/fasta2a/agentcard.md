### AgentCard

Bases: `TypedDict`

The card that describes an agent.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/schema.py`

```python
@pydantic.with_config({'alias_generator': to_camel})
class AgentCard(TypedDict):
    """The card that describes an agent."""

    name: str
    """Human readable name of the agent e.g. "Recipe Agent"."""

    description: str
    """A human-readable description of the agent.

    Used to assist users and other agents in understanding what the agent can do.
    (e.g. "Agent that helps users with recipes and cooking.")
    """

    url: str
    """A URL to the address the agent is hosted at."""

    version: str
    """The version of the agent - format is up to the provider. (e.g. "1.0.0")"""

    protocol_version: str
    """The version of the A2A protocol this agent supports."""

    provider: NotRequired[AgentProvider]
    """The service provider of the agent."""

    documentation_url: NotRequired[str]
    """A URL to documentation for the agent."""

    icon_url: NotRequired[str]
    """A URL to an icon for the agent."""

    preferred_transport: NotRequired[str]
    """The transport of the preferred endpoint. If empty, defaults to JSONRPC."""

    additional_interfaces: NotRequired[list[AgentInterface]]
    """Announcement of additional supported transports."""

    capabilities: AgentCapabilities
    """The capabilities of the agent."""

    security: NotRequired[list[dict[str, list[str]]]]
    """Security requirements for contacting the agent."""

    security_schemes: NotRequired[dict[str, SecurityScheme]]
    """Security scheme definitions."""

    default_input_modes: list[str]
    """Supported mime types for input data."""

    default_output_modes: list[str]
    """Supported mime types for output data."""

    skills: list[Skill]

```

#### name

```python
name: str

```

Human readable name of the agent e.g. "Recipe Agent".

#### description

```python
description: str

```

A human-readable description of the agent.

Used to assist users and other agents in understanding what the agent can do. (e.g. "Agent that helps users with recipes and cooking.")

#### url

```python
url: str

```

A URL to the address the agent is hosted at.

#### version

```python
version: str

```

The version of the agent - format is up to the provider. (e.g. "1.0.0")

#### protocol_version

```python
protocol_version: str

```

The version of the A2A protocol this agent supports.

#### provider

```python
provider: NotRequired[AgentProvider]

```

The service provider of the agent.

#### documentation_url

```python
documentation_url: NotRequired[str]

```

A URL to documentation for the agent.

#### icon_url

```python
icon_url: NotRequired[str]

```

A URL to an icon for the agent.

#### preferred_transport

```python
preferred_transport: NotRequired[str]

```

The transport of the preferred endpoint. If empty, defaults to JSONRPC.

#### additional_interfaces

```python
additional_interfaces: NotRequired[list[AgentInterface]]

```

Announcement of additional supported transports.

#### capabilities

```python
capabilities: AgentCapabilities

```

The capabilities of the agent.

#### security

```python
security: NotRequired[list[dict[str, list[str]]]]

```

Security requirements for contacting the agent.

#### security_schemes

```python
security_schemes: NotRequired[dict[str, SecurityScheme]]

```

Security scheme definitions.

#### default_input_modes

```python
default_input_modes: list[str]

```

Supported mime types for input data.

#### default_output_modes

```python
default_output_modes: list[str]

```

Supported mime types for output data.
