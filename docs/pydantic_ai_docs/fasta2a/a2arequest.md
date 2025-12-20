### A2ARequest

```python
A2ARequest = Annotated[
    Union[
        SendMessageRequest,
        StreamMessageRequest,
        GetTaskRequest,
        CancelTaskRequest,
        SetTaskPushNotificationRequest,
        GetTaskPushNotificationRequest,
        ResubscribeTaskRequest,
        ListTaskPushNotificationConfigRequest,
        DeleteTaskPushNotificationConfigRequest,
    ],
    Discriminator("method"),
]

```

A JSON RPC request to the A2A server.
