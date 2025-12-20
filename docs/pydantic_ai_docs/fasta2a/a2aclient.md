### A2AClient

A client for the A2A protocol.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/client.py`

```python
class A2AClient:
    """A client for the A2A protocol."""

    def __init__(self, base_url: str = 'http://localhost:8000', http_client: httpx.AsyncClient | None = None) -> None:
        if http_client is None:
            self.http_client = httpx.AsyncClient(base_url=base_url)
        else:
            self.http_client = http_client
            self.http_client.base_url = base_url

    async def send_message(
        self,
        message: Message,
        *,
        metadata: dict[str, Any] | None = None,
        configuration: MessageSendConfiguration | None = None,
    ) -> SendMessageResponse:
        """Send a message using the A2A protocol.

        Returns a JSON-RPC response containing either a result (Task) or an error.
        """
        params = MessageSendParams(message=message)
        if metadata is not None:
            params['metadata'] = metadata
        if configuration is not None:
            params['configuration'] = configuration

        request_id = str(uuid.uuid4())
        payload = SendMessageRequest(jsonrpc='2.0', id=request_id, method='message/send', params=params)
        content = send_message_request_ta.dump_json(payload, by_alias=True)
        response = await self.http_client.post('/', content=content, headers={'Content-Type': 'application/json'})
        self._raise_for_status(response)

        return send_message_response_ta.validate_json(response.content)

    async def get_task(self, task_id: str) -> GetTaskResponse:
        payload = GetTaskRequest(jsonrpc='2.0', id=None, method='tasks/get', params={'id': task_id})
        content = a2a_request_ta.dump_json(payload, by_alias=True)
        response = await self.http_client.post('/', content=content, headers={'Content-Type': 'application/json'})
        self._raise_for_status(response)
        return get_task_response_ta.validate_json(response.content)

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.status_code >= 400:
            raise UnexpectedResponseError(response.status_code, response.text)

```

#### send_message

```python
send_message(
    message: Message,
    *,
    metadata: dict[str, Any] | None = None,
    configuration: MessageSendConfiguration | None = None
) -> SendMessageResponse

```

Send a message using the A2A protocol.

Returns a JSON-RPC response containing either a result (Task) or an error.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/client.py`

```python
async def send_message(
    self,
    message: Message,
    *,
    metadata: dict[str, Any] | None = None,
    configuration: MessageSendConfiguration | None = None,
) -> SendMessageResponse:
    """Send a message using the A2A protocol.

    Returns a JSON-RPC response containing either a result (Task) or an error.
    """
    params = MessageSendParams(message=message)
    if metadata is not None:
        params['metadata'] = metadata
    if configuration is not None:
        params['configuration'] = configuration

    request_id = str(uuid.uuid4())
    payload = SendMessageRequest(jsonrpc='2.0', id=request_id, method='message/send', params=params)
    content = send_message_request_ta.dump_json(payload, by_alias=True)
    response = await self.http_client.post('/', content=content, headers={'Content-Type': 'application/json'})
    self._raise_for_status(response)

    return send_message_response_ta.validate_json(response.content)

```
