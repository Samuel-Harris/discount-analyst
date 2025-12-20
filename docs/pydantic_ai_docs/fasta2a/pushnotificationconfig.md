### PushNotificationConfig

Bases: `TypedDict`

Configuration for push notifications.

A2A supports a secure notification mechanism whereby an agent can notify a client of an update outside of a connected session via a PushNotificationService. Within and across enterprises, it is critical that the agent verifies the identity of the notification service, authenticates itself with the service, and presents an identifier that ties the notification to the executing Task.

The target server of the PushNotificationService should be considered a separate service, and is not guaranteed (or even expected) to be the client directly. This PushNotificationService is responsible for authenticating and authorizing the agent and for proxying the verified notification to the appropriate endpoint (which could be anything from a pub/sub queue, to an email inbox or other service, etc).

For contrived scenarios with isolated client-agent pairs (e.g. local service mesh in a contained VPC, etc.) or isolated environments without enterprise security concerns, the client may choose to simply open a port and act as its own PushNotificationService. Any enterprise implementation will likely have a centralized service that authenticates the remote agents with trusted notification credentials and can handle online/offline scenarios. (This should be thought of similarly to a mobile Push Notification Service).

Source code in `.venv/lib/python3.12/site-packages/fasta2a/schema.py`

```python
@pydantic.with_config({'alias_generator': to_camel})
class PushNotificationConfig(TypedDict):
    """Configuration for push notifications.

    A2A supports a secure notification mechanism whereby an agent can notify a client of an update
    outside of a connected session via a PushNotificationService. Within and across enterprises,
    it is critical that the agent verifies the identity of the notification service, authenticates
    itself with the service, and presents an identifier that ties the notification to the executing
    Task.

    The target server of the PushNotificationService should be considered a separate service, and
    is not guaranteed (or even expected) to be the client directly. This PushNotificationService is
    responsible for authenticating and authorizing the agent and for proxying the verified notification
    to the appropriate endpoint (which could be anything from a pub/sub queue, to an email inbox or
    other service, etc).

    For contrived scenarios with isolated client-agent pairs (e.g. local service mesh in a contained
    VPC, etc.) or isolated environments without enterprise security concerns, the client may choose to
    simply open a port and act as its own PushNotificationService. Any enterprise implementation will
    likely have a centralized service that authenticates the remote agents with trusted notification
    credentials and can handle online/offline scenarios. (This should be thought of similarly to a
    mobile Push Notification Service).
    """

    id: NotRequired[str]
    """Server-assigned identifier."""

    url: str
    """The URL to send push notifications to."""

    token: NotRequired[str]
    """Token unique to this task/session."""

    authentication: NotRequired[SecurityScheme]
    """Authentication details for push notifications."""

```

#### id

```python
id: NotRequired[str]

```

Server-assigned identifier.

#### url

```python
url: str

```

The URL to send push notifications to.

#### token

```python
token: NotRequired[str]

```

Token unique to this task/session.

#### authentication

```python
authentication: NotRequired[SecurityScheme]

```

Authentication details for push notifications.
